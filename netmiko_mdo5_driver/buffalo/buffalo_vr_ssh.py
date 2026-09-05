"""Buffalo VR series SSH support."""

import re
import time
from typing import Optional

from netmiko.base_connection import BaseConnection


class BuffaloVRSSH(BaseConnection):
    """Buffalo VR series SSH driver.

    Supports Buffalo VR-U300W and similar devices with unique CLI:
    - Reference Mode (read-only): prompt '>'
    - Immediate Mode (admin): prompt '$'
    - Edit Mode (batch config): prompt '[edit]$'
    """

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established.

        Buffalo VR prompt is just '$' or '>' without hostname.
        """
        self._test_channel_read(pattern=r"[$>]")
        self.set_base_prompt()
        # Disable paging - Buffalo VR uses '--More--' pagination
        self.disable_paging()
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def disable_paging(
        self,
        command: str = "terminal pager disable",
        delay_factor: Optional[float] = None,
        cmd_verify: bool = True,
        pattern: Optional[str] = None,
    ) -> str:
        """Disable paging on Buffalo VR device.

        Buffalo VR uses 'terminal pager disable' to disable pagination.
        """
        return super().disable_paging(
            command=command,
            delay_factor=delay_factor,
            cmd_verify=cmd_verify,
            pattern=pattern,
        )

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = r"\$",
        alt_prompt_terminator: str = r">",
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:
        """Sets self.base_prompt based on device prompt.

        Buffalo VR prompts are simple without hostname:
        - '$ ' for admin user (Immediate Mode)
        - '> ' for reference user (Reference Mode)
        - '[edit]$ ' for Edit Mode
        """
        # Buffalo VR has simple prompts: just '$' or '>'
        # Override to handle this unique prompt style
        prompt = self.find_prompt(delay_factor=delay_factor)
        prompt = prompt.strip()

        # Set base_prompt to empty string since Buffalo VR doesn't use hostname
        # The prompt is just the terminator character
        if "$" in prompt or ">" in prompt:
            self.base_prompt = ""
            return self.base_prompt
        else:
            raise ValueError(f"Buffalo VR prompt not found: {repr(prompt)}")

    def check_enable_mode(self, check_string: str = "$") -> bool:
        """Check if in admin mode (Immediate Mode).

        Buffalo VR uses '$' for admin mode, '>' for reference mode.
        """
        return super().check_enable_mode(check_string=check_string)

    def enable(
        self,
        cmd: str = "",
        pattern: str = "",
        enable_pattern: Optional[str] = None,
        check_state: bool = True,
        re_flags: int = re.IGNORECASE,
    ) -> str:
        """Buffalo VR does not have enable command.

        User mode is determined at login time (admin vs reference user).
        This method is a no-op but required for compatibility.
        """
        return ""

    def exit_enable_mode(self, exit_command: str = "") -> str:
        """Buffalo VR does not have disable command.

        This method is a no-op but required for compatibility.
        """
        return ""

    def check_config_mode(
        self,
        check_string: str = r"[edit]$",
        pattern: str = "",
        force_regex: bool = False,
    ) -> bool:
        """Checks if the device is in Edit Mode.

        Edit Mode prompt: '[edit]$ '
        """
        # Buffalo VR Edit Mode prompt is '[edit]$ '
        # Use find_prompt to check current prompt
        current_prompt = self.find_prompt()
        return "[edit]" in current_prompt

    def config_mode(
        self,
        config_command: str = "edit start",
        pattern: str = r"\[edit\]\$",
        re_flags: int = 0,
    ) -> str:
        """Enter Edit Mode (configuration mode).

        Command: 'edit start'
        Expected prompt: '[edit]$ '

        Note: Buffalo VR requires sending enter after 'edit start' to get
        prompt.
        """
        output = ""
        if not self.check_config_mode():
            self.write_channel(self.normalize_cmd(config_command))
            # Wait for echo, then send newline to get prompt
            time.sleep(0.5 * self.global_delay_factor)
            self.write_channel(self.RETURN)
            output = self.read_until_pattern(pattern=pattern, re_flags=re_flags)
            if not self.check_config_mode():
                raise ValueError("Failed to enter Edit Mode")
        return output

    def exit_config_mode(
        self, exit_config: str = "edit end", pattern: str = r"\$"
    ) -> str:
        """Exit from Edit Mode.

        Command: 'edit end' applies changes
        Alternative: 'edit cancel' discards changes
        """
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def save_config(
        self,
        cmd: str = "edit save",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        """Save configuration.

        In Edit Mode: 'edit save' saves pending changes
        In Immediate Mode: changes are auto-saved per command

        Note: This assumes we're in Edit Mode. For file backup, use:
        - 'setup save target usb file <filename>'
        - 'setup save target tftp server <server> file <filename>'
        """
        if confirm:
            raise ValueError("Buffalo VR does not support save_config confirmation.")

        # If in Edit Mode, save pending changes
        if self.check_config_mode():
            output = self._send_command_str(command_string=cmd)
            return output
        else:
            # In Immediate Mode, changes are already saved
            return ""

    def cleanup(self, command: str = "exit") -> None:
        """Gracefully exit the SSH session."""
        try:
            # Exit config mode if we're in it
            if self.check_config_mode():
                self.exit_config_mode()
        except Exception:
            pass
        # Call parent cleanup
        super().cleanup(command=command)

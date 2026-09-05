"""Sun Denshi SE220 SSH support."""

import re
import time
from typing import Optional

from netmiko.base_connection import BaseConnection


class SundenshiSE220SSH(BaseConnection):
    """Sun Denshi SE220 SSH driver.

    SE220 is a dual-SIM router with a simple CLI interface:
    - Single prompt: 'RoosterSE>'
    - No enable/privileged mode concept
    - No configure terminal mode
    - Settings modified with 'set' command
    - Settings saved with 'save config' and applied with 'apply config'
    - No paging functionality
    - Command echo is wrapped in ESC[s/ESC[u cursor save/restore sequences,
      so cmd_verify must be disabled.
    """

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established.

        SE220 has a simple prompt: 'RoosterSE>'
        SE220 wraps command echo in ESC[s/ESC[u cursor save/restore sequences,
        so ANSI stripping is enabled and cmd_verify is disabled.
        """
        # Enable ANSI escape code stripping
        self.ansi_escape_codes = True
        # SE220 wraps echo in ESC[s/ESC[u; cmd_verify cannot detect echo reliably
        self.global_cmd_verify = False
        self._test_channel_read(pattern=r"Rooster\s*SE>")
        self.set_base_prompt()
        # SE220 does not have paging functionality, so disable_paging is a no-op
        self.disable_paging()
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def disable_paging(
        self,
        command: str = "",
        delay_factor: Optional[float] = None,
        cmd_verify: bool = False,
        pattern: Optional[str] = None,
    ) -> str:
        """SE220 does not have paging functionality.

        This method is a no-op but required for compatibility.
        """
        # SE220 has no paging, so nothing to disable
        return ""

    def strip_ansi_escape_codes(self, string_buffer: str) -> str:
        """Remove ANSI escape codes from SE220 output.

        SE220 wraps each command echo character in cursor save/restore sequences:
            ESC[s + <char> + ESC[u
        For example, 'show version' echo appears as:
            ESC[s s ESC[u ESC[s h ESC[u ESC[s o ESC[u ...

        The parent class does not handle ESC[s (Save Cursor Position) and
        ESC[u (Restore Cursor Position), so we strip them here.
        """
        # Remove cursor save/restore sequences (ESC[s and ESC[u)
        output = re.sub(r"\x1b\[s", "", string_buffer)
        output = re.sub(r"\x1b\[u", "", output)

        # Call parent to handle other standard ANSI escape codes
        return super().strip_ansi_escape_codes(output)

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = r">",
        alt_prompt_terminator: str = r">",
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:
        """Sets self.base_prompt based on device prompt.

        SE220 prompt format: 'RoosterSE>' (no space between Rooster and SE)
        The base_prompt will be set to 'RoosterSE' (without the '>')
        """
        prompt = self.find_prompt(delay_factor=delay_factor)
        prompt = prompt.strip()

        # SE220 prompt is 'RoosterSE>' (may have optional space)
        # Extract the base part (everything before '>')
        match = re.search(r"(Rooster\s*SE)>", prompt)
        if match:
            self.base_prompt = match.group(1).strip()
            return self.base_prompt
        else:
            raise ValueError(f"SE220 prompt not found: {repr(prompt)}")

    def check_enable_mode(self, check_string: str = ">") -> bool:
        """SE220 does not have enable/privileged mode.

        All operations are performed in the single default mode.
        This method always returns True for compatibility.
        """
        return True

    def enable(
        self,
        cmd: str = "",
        pattern: str = "",
        enable_pattern: Optional[str] = None,
        check_state: bool = True,
        re_flags: int = re.IGNORECASE,
    ) -> str:
        """SE220 does not have enable command.

        All operations are available in the default mode.
        This method is a no-op but required for compatibility.
        """
        return ""

    def exit_enable_mode(self, exit_command: str = "") -> str:
        """SE220 does not have disable command.

        This method is a no-op but required for compatibility.
        """
        return ""

    def check_config_mode(
        self, check_string: str = "", pattern: str = "", force_regex: bool = False
    ) -> bool:
        """SE220 does not have configure terminal mode.

        Configuration is done directly with 'set' commands in the default mode.
        This method always returns False for compatibility.
        """
        return False

    def config_mode(
        self,
        config_command: str = "",
        pattern: str = "",
        re_flags: int = re.IGNORECASE,
    ) -> str:
        """SE220 does not have configure terminal mode.

        Configuration is done directly with 'set' commands.
        This method is a no-op but required for compatibility.
        """
        return ""

    def exit_config_mode(self, exit_config: str = "", pattern: str = "") -> str:
        """SE220 does not have configure terminal mode to exit.

        This method is a no-op but required for compatibility.
        """
        return ""

    def save_config(
        self,
        cmd: str = "save config",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        """Save configuration on SE220.

        SE220 requires two commands to save and apply configuration:
        1. 'save config' - saves to non-volatile memory
        2. 'apply config' - applies the saved configuration

        Args:
            cmd: Save command (default: 'save config')
            confirm: Not used for SE220
            confirm_response: Not used for SE220

        Returns:
            Combined output from both save and apply commands
        """
        output = ""

        # Execute save config
        result = self.send_command_timing(cmd)
        output += str(result) if result else ""
        output += "\n"

        # Execute apply config to make the saved configuration active
        apply_cmd = "apply config"
        result = self.send_command_timing(apply_cmd)
        output += str(result) if result else ""

        return output

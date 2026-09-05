"""ドライバクラス自体の単体テスト。"""

from netmiko.base_connection import BaseConnection
from netmiko.cisco_base_connection import CiscoBaseConnection

from netmiko_mdo5_driver import BuffaloVRSSH, SundenshiSE220SSH


def test_buffalo_vr_inheritance():
    """BuffaloVRSSH が BaseConnection を継承していること。"""
    assert issubclass(BuffaloVRSSH, BaseConnection)


def test_buffalo_vr_class_attributes():
    """BuffaloVRSSH が必要なメソッドを備えていること。"""
    for name in (
        "session_preparation",
        "set_base_prompt",
        "check_config_mode",
        "config_mode",
        "exit_config_mode",
        "save_config",
        "check_enable_mode",
        "enable",
        "exit_enable_mode",
        "cleanup",
    ):
        assert hasattr(BuffaloVRSSH, name), name


def test_sundenshi_se220_inheritance():
    """SundenshiSE220SSH が BaseConnection を継承していること。"""
    assert issubclass(SundenshiSE220SSH, BaseConnection)


def test_sundenshi_se220_not_cisco_based():
    """SundenshiSE220SSH が CiscoBaseConnection を継承していないこと。"""
    assert not issubclass(SundenshiSE220SSH, CiscoBaseConnection)


def test_sundenshi_se220_strips_cursor_save_restore():
    """SE220 のエコーに含まれる ESC[s / ESC[u が除去されること。"""
    conn = SundenshiSE220SSH(
        host="192.0.2.1",
        username="admin",
        password="admin",
        auto_connect=False,
    )
    raw = "\x1b[ss\x1b[u\x1b[sh\x1b[u\x1b[so\x1b[u\x1b[sw\x1b[u"
    assert conn.strip_ansi_escape_codes(raw) == "show"


def test_buffalo_vr_no_enable_mode():
    """BUFFALO VR の enable / exit_enable_mode が no-op であること。"""
    conn = BuffaloVRSSH(
        host="192.0.2.1",
        username="admin",
        password="admin",
        auto_connect=False,
    )
    assert conn.enable() == ""
    assert conn.exit_enable_mode() == ""


def test_sundenshi_se220_no_config_mode():
    """SE220 に config モードが無いこと。"""
    conn = SundenshiSE220SSH(
        host="192.0.2.1",
        username="admin",
        password="admin",
        auto_connect=False,
    )
    assert conn.check_config_mode() is False
    assert conn.config_mode() == ""
    assert conn.exit_config_mode() == ""
    assert conn.check_enable_mode() is True
    assert conn.disable_paging() == ""

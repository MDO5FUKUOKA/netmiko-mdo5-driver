"""netmiko への device_type 登録のテスト。"""

import netmiko
from netmiko.ssh_dispatcher import CLASS_MAPPER, platforms, ssh_dispatcher

from netmiko_mdo5_driver import BuffaloVRSSH, SundenshiSE220SSH, register

EXPECTED = {
    "buffalo_vr": BuffaloVRSSH,
    "buffalo_vr_ssh": BuffaloVRSSH,
    "sundenshi_se220": SundenshiSE220SSH,
    "sundenshi_se220_ssh": SundenshiSE220SSH,
}


def test_class_mapper_registration():
    """CLASS_MAPPER に device_type が登録されていること。"""
    for device_type, driver_class in EXPECTED.items():
        assert CLASS_MAPPER[device_type] is driver_class


def test_platforms_registration():
    """platforms に device_type が載っていること(ConnectHandler の検証対象)。"""
    for device_type in EXPECTED:
        assert device_type in netmiko.platforms


def test_platforms_list_is_shared_object():
    """netmiko.platforms と ssh_dispatcher.platforms が同一オブジェクトであること。

    ここが別オブジェクトになる(= platforms を再束縛する)実装だと
    ConnectHandler が device_type を認識できなくなる。
    """
    assert netmiko.platforms is platforms


def test_ssh_dispatcher_returns_driver_class():
    """ssh_dispatcher() がドライバクラスを返すこと。"""
    for device_type, driver_class in EXPECTED.items():
        assert ssh_dispatcher(device_type) is driver_class


def test_connect_handler_builds_driver():
    """ConnectHandler が device_type からドライバを生成すること(接続はしない)。"""
    for device_type, driver_class in EXPECTED.items():
        conn = netmiko.ConnectHandler(
            device_type=device_type,
            host="192.0.2.1",
            username="admin",
            password="admin",
            auto_connect=False,
        )
        assert isinstance(conn, driver_class)


def test_register_is_idempotent():
    """register() を再実行しても platforms が重複しないこと。"""
    before = list(netmiko.platforms)
    register()
    register()
    assert netmiko.platforms == before
    for device_type in EXPECTED:
        assert netmiko.platforms.count(device_type) == 1

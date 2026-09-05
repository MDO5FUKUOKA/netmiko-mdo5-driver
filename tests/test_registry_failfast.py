"""register() のフェイルファスト挙動のテスト。"""

import pytest

from netmiko_mdo5_driver import BuffaloVRSSH, RegistrationError, register
from netmiko_mdo5_driver._registry import _dispatcher_module


@pytest.fixture
def dispatcher():
    """ssh_dispatcher のグローバルをテスト後に復元する。"""
    module = _dispatcher_module()
    saved_mapper = dict(module.CLASS_MAPPER)
    saved_platforms = list(module.platforms)
    yield module
    module.CLASS_MAPPER = saved_mapper
    module.platforms = saved_platforms


def test_raises_when_platforms_is_not_a_list(dispatcher):
    """platforms がリストでなくなったら import 時点で落ちること。

    platforms がリストであることは netmiko の実装詳細で公開契約ではないため、
    実行時に「未対応の device_type」という分かりにくいエラーになる前に落とす。
    """
    dispatcher.platforms = tuple(dispatcher.platforms)
    with pytest.raises(RegistrationError, match="想定の型ではない"):
        register()


def test_raises_when_class_mapper_is_not_a_dict(dispatcher):
    """CLASS_MAPPER が dict でなくなったら落ちること。"""
    dispatcher.CLASS_MAPPER = list(dispatcher.CLASS_MAPPER)
    with pytest.raises(RegistrationError, match="想定の型ではない"):
        register()


def test_warns_and_skips_when_netmiko_owns_the_device_type(dispatcher):
    """netmiko 本体が同名 device_type を持っていたら上書きせず警告すること。"""

    class UpstreamDriver:
        pass

    dispatcher.CLASS_MAPPER = dict(dispatcher.CLASS_MAPPER)
    dispatcher.platforms = list(dispatcher.platforms)
    dispatcher.CLASS_MAPPER["buffalo_vr"] = UpstreamDriver

    with pytest.warns(RuntimeWarning, match="buffalo_vr"):
        register()

    assert dispatcher.CLASS_MAPPER["buffalo_vr"] is UpstreamDriver


def test_registers_into_a_fresh_dispatcher_state(dispatcher):
    """未登録状態から register() すると両方の辞書/リストが更新されること。"""
    dispatcher.CLASS_MAPPER = {
        k: v
        for k, v in dispatcher.CLASS_MAPPER.items()
        if not k.startswith(("buffalo_vr", "sundenshi_se220"))
    }
    dispatcher.platforms = [
        p
        for p in dispatcher.platforms
        if not p.startswith(("buffalo_vr", "sundenshi_se220"))
    ]

    register()

    assert dispatcher.CLASS_MAPPER["buffalo_vr"] is BuffaloVRSSH
    assert dispatcher.CLASS_MAPPER["buffalo_vr_ssh"] is BuffaloVRSSH
    assert "sundenshi_se220" in dispatcher.platforms
    assert dispatcher.platforms == sorted(dispatcher.platforms)

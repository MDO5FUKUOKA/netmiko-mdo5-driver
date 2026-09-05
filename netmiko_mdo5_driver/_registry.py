"""netmiko の ssh_dispatcher へ本パッケージのドライバを登録する。"""

import importlib
import warnings
from types import ModuleType
from typing import Dict, List, Tuple, Type

from netmiko.base_connection import BaseConnection

from netmiko_mdo5_driver.buffalo import BuffaloVRSSH
from netmiko_mdo5_driver.sundenshi import SundenshiSE220SSH

DEVICE_TYPES: Dict[str, Type[BaseConnection]] = {
    "buffalo_vr": BuffaloVRSSH,
    "sundenshi_se220": SundenshiSE220SSH,
}


class RegistrationError(RuntimeError):
    """netmiko への device_type 登録に失敗した。"""


def _dispatcher_module() -> ModuleType:
    """netmiko.ssh_dispatcher モジュールを返す。

    netmiko/__init__.py が同名の関数 ``ssh_dispatcher()`` をエクスポートしていて
    サブモジュール属性を隠すため、``netmiko.ssh_dispatcher`` の属性アクセスでは
    モジュールを取得できない。
    """
    return importlib.import_module("netmiko.ssh_dispatcher")


def register() -> None:
    """device_type を netmiko の CLASS_MAPPER / platforms へ登録する。

    netmiko 本体と同じく ``<device_type>`` と ``<device_type>_ssh`` の
    両方のキーを登録する。``ConnectHandler`` は ``CLASS_MAPPER`` を引く前に
    ``platforms`` で device_type を検証するため、両方の更新が必要。
    ``platforms`` は ``netmiko/__init__.py`` が同一オブジェクトを再エクスポート
    しているため、再束縛せず破壊的に更新する。

    何度呼び出しても安全。既に同じキーが登録されている場合(netmiko 本体が
    将来同名の device_type を持った場合を含む)は上書きせず、別クラスが
    登録済みであれば ``RuntimeWarning`` で知らせる。

    Raises:
        RegistrationError: netmiko 側の CLASS_MAPPER / platforms が想定の型で
            なかった場合、または登録後の検証に失敗した場合。
            ``platforms`` がリストであることや ``netmiko/__init__.py`` が同一
            オブジェクトを再エクスポートしていることは netmiko の実装詳細で
            公開契約ではないため、実行時に「未対応の device_type」という
            分かりにくいエラーになる前に import 時点で落とす。
    """
    dispatcher = _dispatcher_module()
    class_mapper = dispatcher.CLASS_MAPPER
    platforms = dispatcher.platforms

    if not isinstance(class_mapper, dict) or not isinstance(platforms, list):
        raise RegistrationError(
            "netmiko.ssh_dispatcher の CLASS_MAPPER / platforms が想定の型ではない "
            f"(CLASS_MAPPER={type(class_mapper).__name__}, "
            f"platforms={type(platforms).__name__})。"
            "netmiko の内部実装が変わった可能性がある。"
            "netmiko のバージョンを確認するか、ドライバクラスを直接"
            "インスタンス化して使用すること。"
        )

    registered: List[Tuple[str, Type[BaseConnection]]] = []
    conflicts: List[str] = []
    for base_key, driver_class in DEVICE_TYPES.items():
        for key in (base_key, f"{base_key}_ssh"):
            if key in class_mapper:
                if class_mapper[key] is not driver_class:
                    conflicts.append(key)
                continue
            class_mapper[key] = driver_class
            platforms.append(key)
            registered.append((key, driver_class))

    if registered:
        platforms.sort()

    if conflicts:
        warnings.warn(
            f"device_type {sorted(conflicts)} は netmiko 側に別のドライバとして"
            "登録済みのため、netmiko_mdo5_driver は登録をスキップした。"
            "本パッケージのドライバを使うにはクラスを直接インスタンス化すること。",
            RuntimeWarning,
            stacklevel=2,
        )

    _verify(dispatcher, registered)


def _verify(
    dispatcher: ModuleType, registered: List[Tuple[str, Type[BaseConnection]]]
) -> None:
    """今回登録したキーが ConnectHandler から見える状態か検証する。"""
    for key, driver_class in registered:
        if dispatcher.CLASS_MAPPER.get(key) is not driver_class:
            raise RegistrationError(
                f"device_type '{key}' を CLASS_MAPPER へ登録できなかった。"
            )
        if key not in dispatcher.platforms:
            raise RegistrationError(
                f"device_type '{key}' を platforms へ登録できなかった。"
                "ConnectHandler はこの device_type を受け付けない。"
            )

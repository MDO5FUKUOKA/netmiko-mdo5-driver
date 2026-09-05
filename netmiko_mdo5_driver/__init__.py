"""netmiko 用のサードパーティドライバ集(BUFFALO VR / サン電子 SE220)。

本パッケージを import した時点で device_type が netmiko へ登録されるため、
以降は ``netmiko.ConnectHandler(device_type="sundenshi_se220", ...)`` が使える。
ドライバクラスを直接インスタンス化しても良い。
"""

from netmiko_mdo5_driver._registry import DEVICE_TYPES, RegistrationError, register
from netmiko_mdo5_driver.buffalo import BuffaloVRSSH
from netmiko_mdo5_driver.sundenshi import SundenshiSE220SSH

__version__ = "0.1.0"

register()

__all__ = [
    "BuffaloVRSSH",
    "SundenshiSE220SSH",
    "DEVICE_TYPES",
    "RegistrationError",
    "register",
    "__version__",
]

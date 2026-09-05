# netmiko-mdo5-driver

netmiko のフォークを維持せずに、BUFFALO / サン電子の機器を netmiko から扱うための
サードパーティドライバ集。公式の `netmiko` をそのまま依存に使う。

対応 device_type:

| device_type | 機器 | ドライバクラス |
|---|---|---|
| `buffalo_vr` (`buffalo_vr_ssh`) | BUFFALO VR シリーズ (VR-U300W 等) | `BuffaloVRSSH` |
| `sundenshi_se220` (`sundenshi_se220_ssh`) | サン電子 SE220 (Rooster) | `SundenshiSE220SSH` |

## インストール

```bash
pip install netmiko-mdo5-driver
# もしくはリポジトリから
pip install git+https://github.com/MDO5FUKUOKA/netmiko-mdo5-driver.git
```

`netmiko>=4.5,<5` に依存する。フォーク版 netmiko は不要。

## 使い方

### ConnectHandler 経由

`netmiko_mdo5_driver` を import した時点で device_type が netmiko に登録される。
**`ConnectHandler` を呼ぶ前に import すること。**

```python
import netmiko_mdo5_driver  # noqa: F401  device_type の登録が目的
from netmiko import ConnectHandler

conn = ConnectHandler(
    device_type="sundenshi_se220",
    host="192.0.2.1",
    username="admin",
    password="********",
)
print(conn.send_command("show version"))
conn.disconnect()
```

### ドライバクラスを直接使う

登録に依存したくない場合はクラスを直接インスタンス化する。

```python
from netmiko_mdo5_driver import SundenshiSE220SSH

conn = SundenshiSE220SSH(
    host="192.0.2.1",
    username="admin",
    password="********",
)
```

### 明示的な登録

import 時に自動登録されるが、`register()` を明示的に呼んでもよい(冪等)。

```python
from netmiko_mdo5_driver import register

register()
```

登録は netmiko の `ssh_dispatcher.CLASS_MAPPER` と `ssh_dispatcher.platforms`
(= `netmiko.platforms` と同一オブジェクト)を破壊的に更新する。netmiko 本体が
同名の device_type を別クラスで持っていた場合は上書きせず `RuntimeWarning` を出す。

`platforms` がリストであることや `netmiko/__init__.py` が同一オブジェクトを
再エクスポートしていることは netmiko の実装詳細であり公開契約ではない。
そのため `register()` は登録後に結果を検証し、失敗したら `RegistrationError`
(= `RuntimeError`)を送出する。実行時に「未対応の device_type」という
分かりにくいエラーになるより import 時点で落ちる方が原因を追いやすいため。
その場合もドライバクラスの直接インスタンス化は影響を受けない。

## 機器ごとの注意点

### BUFFALO VR シリーズ

- プロンプトにホスト名が無い(`$` = Immediate Mode / `>` = Reference Mode)ため
  `base_prompt` は空文字になる。
- enable モードの概念が無い。管理者権限はログインユーザで決まる。
- 設定モードは `edit start` で入り `[edit]$` プロンプトになる。`edit end` で適用、
  `edit cancel` で破棄。`save_config()` は Edit Mode 中のみ `edit save` を実行する。
- ページャは `terminal pager disable` で無効化する。

### サン電子 SE220

- プロンプトは `RoosterSE>` の 1 種類のみ。enable モード・config モードは無い。
- コマンドエコーが 1 文字ごとに `ESC[s` / `ESC[u`(カーソル保存/復元)で包まれるため、
  ANSI 除去を有効化し `global_cmd_verify = False` にしている。
- ページャ機能が無いため `disable_paging()` は no-op。
- 設定反映は 2 段階。`save_config()` が `save config` と `apply config` を続けて実行する。

## 開発

```bash
uv venv
uv pip install -e ".[dev]"
.venv/bin/pytest -q tests
.venv/bin/black --check netmiko_mdo5_driver tests
.venv/bin/mypy netmiko_mdo5_driver
.venv/bin/ruff check netmiko_mdo5_driver tests
```

## 経緯

もとは `ttrip-ngs/netmiko` フォークの `custom-drivers` ブランチで開発していたが、
追加分は `BaseConnection` のサブクラス 2 本と dispatcher への登録のみで、
netmiko のプライベート API に触れていない。フォークを維持すると
paramiko / cryptography のセキュリティ更新に追従しにくく、git URL 依存で
再現性・CI・パッケージングの負担も大きいため、独立パッケージへ切り出した。

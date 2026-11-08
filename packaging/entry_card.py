"""Dota2Coach-Card.exe 的入口：只显示置顶卡片（给想“开箱即用、不要主窗口”的人）。

等价于 `python -m dota2coach --legacy`；把用户传入的参数原样带进去，
这样 --snapshot / --screenshot / --seconds / --save-overlay / --config 仍然可用。
"""

import os
import sys
import traceback


def _boot_log(message: str) -> None:
    try:
        path = os.path.join(os.path.dirname(sys.executable), "boot.log")
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(message + "\n")
    except OSError:
        pass


_boot_log("bootstrap start")
try:
    from dota2coach.__main__ import main

    _boot_log("import ok")
except BaseException:  # noqa: BLE001
    _boot_log("import failed:\n" + traceback.format_exc())
    raise

if __name__ == "__main__":
    _boot_log("argv=" + repr(sys.argv))
    raise SystemExit(main([*sys.argv[1:], "--legacy"]))

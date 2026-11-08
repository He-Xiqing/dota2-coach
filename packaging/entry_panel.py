"""Dota2Coach.exe 的入口（主窗口 + 卡片）。

PyInstaller 需要一个真实脚本做入口；这里只是把包内 __main__ 调起来。
"""

from dota2coach.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())

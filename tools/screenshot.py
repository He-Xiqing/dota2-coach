"""抓一张当前屏幕（主显示器），保存成 PNG。

用于标定/调试英雄栏识别：进到"英雄选择"界面或对局里，运行一次，
把生成的 PNG 发回来，就能按真实分辨率裁模板。

用法:
    python tools/screenshot.py
    python tools/screenshot.py --label draft --delay 5
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIR = ROOT / "logs" / "screenshots"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_DIR, help="保存目录")
    parser.add_argument("--label", default="screen", help="文件名前缀")
    parser.add_argument("--delay", type=float, default=3.0,
                        help="等待秒数，方便切回游戏窗口（默认 3 秒）")
    args = parser.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:
        pass

    try:
        import mss
        import mss.tools
    except ImportError:
        print("缺少 mss：在项目根执行  .\\.venv\\Scripts\\pip.exe install -r requirements-vision.txt")
        return 1

    if args.delay > 0:
        print(f"{args.delay:.0f} 秒后抓屏，请切回游戏……")
        import time
        time.sleep(args.delay)

    args.out.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%H%M%S")
    path = args.out / f"{args.label}-{stamp}.png"

    with mss.mss() as sct:
        monitors = sct.monitors
        monitor = monitors[1] if len(monitors) > 1 else monitors[0]
        shot = sct.grab(monitor)
        mss.tools.to_png(shot.rgb, shot.size, output=str(path))

    print(f"已保存: {path}")
    print(f"屏幕尺寸: {shot.size.width}x{shot.size.height}（物理像素）")
    print("把这个文件发给教练，或放进 logs/screenshots/ 供自动标定使用。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

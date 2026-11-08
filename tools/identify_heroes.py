"""从一张截图（或当前屏幕）里识别 10 个英雄。

用法:
    python tools/identify_heroes.py logs/screenshots/draft-121216.png
    python tools/identify_heroes.py --live --save-debug
    python tools/identify_heroes.py <png> --mode topbar
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import cv2  # noqa: E402

from dota2coach.config import load_config  # noqa: E402
from dota2coach.vision.capture import ScreenCapture  # noqa: E402
from dota2coach.vision.heroes import (  # noqa: E402
    HeroMatcher,
    identify_panel,
    identify_topbar,
    imread_path,
    imwrite_path,
    load_hero_table,
)

COLOR_OK = (80, 220, 80)
COLOR_BAD = (60, 60, 220)


def draw(image, result, title: str):
    vis = image.copy()
    for team, matches in result.items():
        for match in matches:
            x, y, w, h = match.box
            color = COLOR_OK if match.hero else COLOR_BAD
            cv2.rectangle(vis, (x, y), (x + w, y + h), color, 2)
            text = f"{match.label} {match.score:.2f}" if match.hero else f"? {match.score:.2f}"
            cv2.putText(vis, text, (x, max(12, y - 4)), cv2.FONT_HERSHEY_SIMPLEX,
                        0.45, color, 1, cv2.LINE_AA)
    return vis


def print_result(result, title: str) -> None:
    print(f"\n== {title} ==")
    for team, matches in result.items():
        label = {"ally": "我方", "enemy": "敌方"}.get(team, team)
        print(f"[{label}] {len(matches)} 个")
        for index, match in enumerate(matches):
            hero = match.hero
            name = f"{hero.name_loc} ({hero.short}, id={hero.hero_id})" if hero else "未识别"
            print(f"  {index}: {name:36s} score={match.score:.3f} second={match.second:.3f}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", nargs="?", help="截图路径；不给则配合 --live 抓当前屏幕")
    parser.add_argument("--live", action="store_true", help="抓当前屏幕而不是读文件")
    parser.add_argument("--mode", choices=["panel", "topbar", "both"], default="panel")
    parser.add_argument("--save-debug", action="store_true", help="把识别结果画在图上保存")
    args = parser.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:
        pass

    cfg = load_config()
    heroes = load_hero_table(cfg.vision.heroes_json)
    if not heroes:
        print(f"缺少英雄表: {cfg.vision.heroes_json}")
        print("先运行:  powershell -ExecutionPolicy Bypass -File scripts\\fetch_hero_icons.ps1")
        return 1

    matcher = HeroMatcher(heroes, cfg.vision.icons_dir, cfg.vision.cards_dir)
    if not matcher.ready:
        print(f"模板为空: {cfg.vision.icons_dir} / {cfg.vision.cards_dir}")
        print("先运行:  powershell -ExecutionPolicy Bypass -File scripts\\fetch_hero_icons.ps1")
        return 1

    if args.live or not args.image:
        with ScreenCapture() as capture:
            image = capture.grab()
        source = "live screen"
    else:
        image = imread_path(Path(args.image))
        source = args.image
        if image is None:
            print(f"读不到图片: {args.image}")
            return 1

    min_score = cfg.vision.match_min_score
    min_gap = cfg.vision.match_min_gap
    print(f"图片: {source}  {image.shape[1]}x{image.shape[0]}")

    results = {}
    if args.mode in ("panel", "both"):
        results["panel"] = identify_panel(image, matcher, min_score, min_gap)
    if args.mode in ("topbar", "both"):
        results["topbar"] = identify_topbar(image, matcher, min_score, min_gap)

    for key, result in results.items():
        print_result(result, {"panel": "战友与宿敌面板", "topbar": "顶部英雄栏"}[key])

    if args.save_debug and results:
        for key, result in results.items():
            output = Path(source if source != "live screen" else "live")
            output = output.with_name(output.stem + f"-{key}.png") if output.suffix else Path(f"live-{key}.png")
            if output.parent == Path(""):
                output = Path("logs") / "screenshots" / output
            output.parent.mkdir(parents=True, exist_ok=True)
            imwrite_path(output, draw(image, result, key))
            print(f"调试图: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

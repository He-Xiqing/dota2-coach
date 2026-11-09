"""诊断不同分辨率下顶部英雄栏识别数量。"""

import sys
from pathlib import Path

import cv2

sys.path.insert(0, "src")

from dota2coach.vision.heroes import (  # noqa: E402
    HeroMatcher,
    identify_topbar,
    load_hero_table,
    imread_path,
)

ROOT = Path(__file__).resolve().parents[1]
heroes = load_hero_table(ROOT / "data" / "heroes.json")
matcher = HeroMatcher(heroes, ROOT / "data" / "hero_icons", ROOT / "data" / "hero_cards")


def probe(path: Path, short: str, sizes):
    image = imread_path(path)
    print(f"== {path.name} {image.shape[1]}x{image.shape[0]} self={short}")
    for target in sizes:
        h = target[1]
        scale = h / image.shape[0]
        resized = cv2.resize(image, (int(round(image.shape[1] * scale)), h), interpolation=cv2.INTER_AREA)
        rows = []
        for score, boxes in matcher.locate_bar_candidates(resized, short, limit=4):
            matches = [matcher.identify(resized, b, "card", 0.55, 0.02) for b in boxes]
            known = sum(1 for m in matches if m.hero)
            names = [m.label for m in matches]
            rows.append((score, known, names))
        rows.sort(key=lambda r: r[1], reverse=True)
        best = rows[0] if rows else (0, 0, [])
        topbar = identify_topbar(resized, matcher, 0.55, 0.02)
        fixed = sum(1 for m in topbar["ally"] + topbar["enemy"] if m.hero)
        print(f"  {resized.shape[1]}x{resized.shape[0]}: anchor_best known={best[1]} score={best[0]:.3f} fixed={fixed}")
        print(f"    anchor names: {best[2]}")


if __name__ == "__main__":
    probe(ROOT / "logs" / "screenshots" / "draft-121216.png", "beastmaster", [(2560, 1600), (1920, 1080), (1600, 900)])
    probe(ROOT / "logs" / "screenshots" / "hud2-224655.png", "beastmaster", [(2560, 1600), (1920, 1080)])

"""原型：用顶部色条定位英雄栏。"""

import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, "src")

from dota2coach.vision.heroes import HeroMatcher, imread_path, load_hero_table  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def runs(mask):
    out = []
    start = None
    for i, v in enumerate(mask):
        if v and start is None:
            start = i
        elif not v and start is not None:
            out.append((start, i - start))
            start = None
    if start is not None:
        out.append((start, len(mask) - start))
    return out


def detect(image):
    h, w = image.shape[:2]
    band_h = max(10, int(round(h * 0.06)))
    band = image[:band_h]
    hsv = cv2.cvtColor(band, cv2.COLOR_BGR2HSV)
    sat = hsv[:, :, 1]
    val = hsv[:, :, 2]
    mask = ((sat > 80) & (val > 70)).any(axis=0)
    segs = [s for s in runs(mask) if s[1] >= max(8, w * 0.008)]
    # 合并相邻碎片
    merged = []
    for s in segs:
        if merged and s[0] - (merged[-1][0] + merged[-1][1]) <= max(3, w * 0.004):
            merged[-1] = (merged[-1][0], s[0] + s[1] - merged[-1][0])
        else:
            merged.append(s)
    merged = [s for s in merged if w * 0.015 <= s[1] <= w * 0.12]
    if len(merged) < 8:
        return [], merged
    widths = sorted(s[1] for s in merged)
    width = widths[len(widths) // 2]
    boxes = []
    for x, sw in merged:
        col = hsv[:, x:x + sw]
        strip_mask = (col[:, :, 1] > 80) & (col[:, :, 2] > 70)
        coverage = strip_mask.mean(axis=1)
        strip_bottom = 0
        for row, cov in enumerate(coverage):
            if cov >= 0.75:
                strip_bottom = row + 1
            elif row > 2 and cov < 0.4:
                break
        hh = int(round(min(sw, width) / 1.5))
        boxes.append((x, strip_bottom, min(sw, width), hh))
    return boxes, merged


def probe(path, short, sizes):
    table = load_hero_table(ROOT / "data" / "heroes.json")
    matcher = HeroMatcher(table, ROOT / "data" / "hero_icons", ROOT / "data" / "hero_cards")
    image = imread_path(path)
    for target_w, target_h in sizes:
        im = cv2.resize(image, (target_w, target_h), interpolation=cv2.INTER_AREA)
        boxes, segs = detect(im)
        labels = []
        if len(boxes) == 10:
            labels = [matcher.identify(im, b, "card", 0.5, 0.02).label for b in boxes]
        print(f"{path.name} {target_w}x{target_h}: segs={len(segs)} boxes={len(boxes)} known={sum(1 for l in labels if l != '未识别')}")
        print(f"   {labels}")


if __name__ == "__main__":
    probe(ROOT / "logs" / "screenshots" / "draft-121216.png", "beastmaster",
          [(2560, 1600), (1920, 1080), (1600, 900), (1280, 720)])

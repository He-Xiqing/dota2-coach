"""小地图识别：只做“点”的聚类，不认英雄身份。

实测结论：小地图上的英雄图标只有约 14px，模板匹配无法稳定区分是谁
（多个英雄会在同一位置得到相近分数），所以这里只统计：
- 敌方红点（英雄级大小）
- 我方绿点（英雄级大小）
- 自己的白/黄点
再配合时间做“敌方消失 / 我方聚集 / 团战爆发”这类判断。
"""

from __future__ import annotations

from dataclasses import dataclass, field

import cv2
import numpy as np

# 相对游戏窗口的比例：2560x1600 下约 (2190,1208)-(2555,1592)
MINIMAP_FRAC = (0.855, 0.755, 0.998, 0.995)

# 英雄标记的三种显示（图标 / 名字 / 头像）尺寸差别很大：
# - 图标：约 8–12px 方块
# - 名字：细长文字条（膨胀后并成一团）
# - 头像：约 16–22px 方块
HERO_MIN_AREA = 45
HERO_MAX_AREA = 1600
HERO_MAX_SIDE = 48
HERO_MAX_ASPECT = 5.0


@dataclass(frozen=True)
class Point:
    x: float  # 0..1，小地图内归一化坐标
    y: float


@dataclass(frozen=True)
class MinimapDots:
    enemies: list[Point] = field(default_factory=list)
    allies: list[Point] = field(default_factory=list)
    self_pos: Point | None = None
    creeps: int = 0


def crop_minimap(image: np.ndarray, frac: tuple[float, float, float, float] = MINIMAP_FRAC) -> np.ndarray:
    height, width = image.shape[:2]
    left, top, right, bottom = frac
    x0 = max(0, int(width * left))
    x1 = min(width, int(width * right))
    y0 = max(0, int(height * top))
    y1 = min(height, int(height * bottom))
    return image[y0:y1, x0:x1]


def _mask(hsv: np.ndarray, ranges: list[tuple[tuple[int, int, int], tuple[int, int, int]]]) -> np.ndarray:
    out = np.zeros(hsv.shape[:2], dtype=np.uint8)
    for low, high in ranges:
        out = cv2.bitwise_or(out, cv2.inRange(hsv, np.array(low, np.uint8), np.array(high, np.uint8)))
    return out


def _points(mask: np.ndarray, min_area: float, max_area: float) -> tuple[list[Point], int]:
    count, _labels, stats, centers = cv2.connectedComponentsWithStats(mask, 8)
    height, width = mask.shape[:2]
    points: list[Point] = []
    small = 0
    for index in range(1, count):
        area = int(stats[index, cv2.CC_STAT_AREA])
        if area < 4:
            continue
        if area < min_area:
            small += 1
            continue
        if area > max_area:
            continue
        w = max(1, int(stats[index, cv2.CC_STAT_WIDTH]))
        h = max(1, int(stats[index, cv2.CC_STAT_HEIGHT]))
        # 名字模式下文字条很扁、头像模式下更方：放宽长宽比，只排除极端细线
        if max(w, h) > HERO_MAX_SIDE or max(w, h) / min(w, h) > HERO_MAX_ASPECT:
            continue
        cx, cy = centers[index]
        if not (0.02 < cx / width < 0.98 and 0.02 < cy / height < 0.98):
            continue
        points.append(Point(float(cx) / width, float(cy) / height))
    return points, small


def detect_dots(minimap_bgr: np.ndarray, scale: float = 1.0) -> MinimapDots:
    """从一张小地图截图里取红/绿/自己三种点。"""
    if minimap_bgr.size == 0:
        return MinimapDots()
    hsv = cv2.cvtColor(minimap_bgr, cv2.COLOR_BGR2HSV)
    red = _mask(
        hsv,
        [
            ((0, 110, 110), (12, 255, 255)),
            ((168, 110, 110), (180, 255, 255)),
        ],
    )
    green = _mask(hsv, [((40, 100, 90), (95, 255, 255))])
    white = _mask(hsv, [((0, 0, 215), (180, 40, 255))])

    # 名字模式下英雄是一个个彩色文字，先闭运算 + 膨胀把同一名字的字并成一团；
    # 图标/头像模式下也会被合并成一个点，不影响计数。
    kernel = np.ones((3, 3), np.uint8)
    merged = lambda m: cv2.dilate(cv2.morphologyEx(m, cv2.MORPH_CLOSE, kernel), kernel, iterations=1)
    enemies, enemy_small = _points(merged(red), HERO_MIN_AREA * scale * scale, HERO_MAX_AREA * max(0.35, scale) ** 2 * 1.6)
    allies, _ = _points(merged(green), HERO_MIN_AREA * scale * scale, HERO_MAX_AREA * max(0.35, scale) ** 2 * 1.6)
    self_points, _ = _points(merged(white), HERO_MIN_AREA * scale * scale, HERO_MAX_AREA * max(0.35, scale) ** 2 * 1.6)
    # 边缘的白点多半是 UI（时钟、边框），不当成自己
    self_points = [p for p in self_points if 0.05 < p.x < 0.95 and 0.05 < p.y < 0.95]
    return MinimapDots(
        enemies=enemies,
        allies=allies,
        self_pos=self_points[0] if self_points else None,
        creeps=enemy_small,
    )


class StaticFilter:
    """过滤长期不动的点（塔、基地、UI 标记）。

    英雄会走动，塔/眼/UI 不会。按归一化网格记录每个格子的首次出现时间，
    停留超过 hold 秒的点不再当成英雄。
    """

    def __init__(self, cell: float = 0.02, hold: float = 12.0) -> None:
        self._cell = cell
        self._hold = hold
        self._first: dict[tuple[int, int], float] = {}

    def update(self, points: list[Point], now: float) -> list[Point]:
        first: dict[tuple[int, int], float] = {}
        moving: list[Point] = []
        for point in points:
            key = (int(point.x / self._cell), int(point.y / self._cell))
            seen = self._first.get(key, now)
            first[key] = seen
            if now - seen < self._hold:
                moving.append(point)
        self._first = first
        return moving


def cluster_count(points: list[Point], radius: float) -> int:
    """返回“最大的一簇”的点数（半径按归一化坐标算）。"""
    if not points:
        return 0
    best = 0
    for i, p in enumerate(points):
        near = 0
        for j, q in enumerate(points):
            if (p.x - q.x) ** 2 + (p.y - q.y) ** 2 <= radius * radius:
                near += 1
        best = max(best, near)
    return best


def nearest_distance(points: list[Point], target: Point | None) -> float:
    if target is None or not points:
        return 9.0
    return min(((p.x - target.x) ** 2 + (p.y - target.y) ** 2) ** 0.5 for p in points)


@dataclass(frozen=True)
class MinimapRect:
    """小地图在整张截图中的绝对像素位置。"""

    left: int
    top: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height


def _candidates(width: int, height: int, sides=("right", "left")):
    """穷举左右角 × 7 档尺寸的候选（小地图是正方形，贴边）。"""
    margin = max(2, int(width * 0.004))
    out = []
    for frac in [0.14 + 0.01 * i for i in range(0, 21)]:
        size = int(height * frac)
        if size < 80 or size > width * 0.45:
            continue
        top = height - margin - size
        for side in sides:
            if side == "right":
                left = width - margin - size
            else:
                left = margin
            out.append(MinimapRect(left, top, size, size))
    return out


def crop_rect(image: np.ndarray, rect: MinimapRect) -> np.ndarray:
    h, w = image.shape[:2]
    return image[max(0, rect.top):min(h, rect.bottom), max(0, rect.left):min(w, rect.right)]


def _score_crop(crop: np.ndarray) -> float:
    """小地图里应当有 0–5 个红点与 0–5 个绿点；数量离奇就扣分。"""
    if crop.size == 0:
        return 0.0
    scale = max(0.4, min(2.5, crop.shape[1] / 353.0))
    dots = detect_dots(crop, scale)
    enemies, allies = len(dots.enemies), len(dots.allies)
    if enemies > 6 or allies > 6:
        return -1.0
    return min(enemies, 5) * 2.0 + min(allies, 5) + (0.5 if enemies or allies else 0.0)


def _border_score(frame: np.ndarray, rect: MinimapRect) -> float:
    """小地图与周围 HUD 通常有亮度差；用上边与左边的跳变做先验。"""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
    h, w = gray.shape[:2]
    top_out, top_in = rect.top - 3, rect.top + 3
    left_out, left_in = rect.left - 3, rect.left + 3
    total = 0.0
    if 0 <= top_out and top_in < h:
        band = slice(max(0, rect.left), min(w, rect.right))
        total += float(np.abs(gray[top_out, band] - gray[top_in, band]).mean())
    if 0 <= left_out and left_in < w:
        band = slice(max(0, rect.top), min(h, rect.bottom))
        total += float(np.abs(gray[band, left_out] - gray[band, left_in]).mean())
    return total / 2.0


def locate_minimap(
    frames,
    sides=("right", "left"),
    min_score: float = 3.0,
):
    """在若干帧上给候选布局打分，返回最像小地图的那块；不确定时返回 None。"""
    if not frames:
        return None
    height, width = frames[0].shape[:2]
    scored = []
    for rect in _candidates(width, height, sides):
        total = 0.0
        for frame in frames:
            total += _score_crop(crop_rect(frame, rect)) + 0.02 * _border_score(frame, rect)
        scored.append((total, rect))
    if not scored:
        return None
    scored.sort(key=lambda item: item[0], reverse=True)
    best_score, best = scored[0]
    if best_score < min_score * len(frames):
        return None
    # 另一侧的最好成绩；差距不够大就认为“不可信”，交给配置回退
    second = 0.0
    for total, rect in scored[1:]:
        if (rect.left < width / 2) != (best.left < width / 2):
            second = max(second, total)
    if second > 0 and best_score < second * min_margin:
        return None
    return best

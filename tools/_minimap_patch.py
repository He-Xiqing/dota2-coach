"""一次性补丁：小地图自适应定位（候选布局 + 打分）。"""

from pathlib import Path

M = Path("src/dota2coach/vision/minimap.py")
src = M.read_text(encoding="utf-8")

# 1) 面积阈值随小地图尺寸缩放
src = src.replace(
    "def _points(mask: np.ndarray, min_area: int, max_area: int)",
    "def _points(mask: np.ndarray, min_area: float, max_area: float)",
)
src = src.replace(
    "    enemies, enemy_small = _points(merged(red), HERO_MIN_AREA, HERO_MAX_AREA)",
    "    enemies, enemy_small = _points(merged(red), HERO_MIN_AREA * scale * scale, HERO_MAX_AREA * scale * scale)",
)
src = src.replace(
    "    allies, _ = _points(merged(green), HERO_MIN_AREA, HERO_MAX_AREA)",
    "    allies, _ = _points(merged(green), HERO_MIN_AREA * scale * scale, HERO_MAX_AREA * scale * scale)",
)
src = src.replace(
    "    self_points, _ = _points(merged(white), HERO_MIN_AREA, HERO_MAX_AREA)",
    "    self_points, _ = _points(merged(white), HERO_MIN_AREA * scale * scale, HERO_MAX_AREA * scale * scale)",
)
src = src.replace(
    "def detect_dots(minimap_bgr: np.ndarray) -> MinimapDots:",
    "def detect_dots(minimap_bgr: np.ndarray, scale: float = 1.0) -> MinimapDots:",
)

if "class MinimapRect" not in src:
    src += '''

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
    for frac in (0.16, 0.18, 0.20, 0.22, 0.24, 0.26, 0.28, 0.30):
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


def locate_minimap(
    frames,
    sides=("right", "left"),
    min_score: float = 3.0,
):
    """在若干帧上给候选布局打分，返回最像小地图的那块；不确定时返回 None。"""
    if not frames:
        return None
    height, width = frames[0].shape[:2]
    best = None
    best_score = 0.0
    for rect in _candidates(width, height, sides):
        total = 0.0
        for frame in frames:
            total += _score_crop(crop_rect(frame, rect))
        if total > best_score:
            best_score = total
            best = rect
    if best is None or best_score < min_score * len(frames):
        return None
    return best
'''
M.write_text(src, encoding="utf-8")
print("minimap patched")

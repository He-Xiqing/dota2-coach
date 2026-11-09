"""英雄识别：定位 10 个英雄格子，再用本地模板做匹配。

两个来源：
- `detect_panel_cells`：决策时间右上角"战友与宿敌"面板，2 列 × 5 行，
  左列我方（第 0 行是自己）、右列敌方。图标是标准方形英雄图标，最好认。
- `detect_topbar_cells`：顶部英雄栏（对局中一直在），10 张卡面。

GSI 不会给敌方英雄，所以这里的识别结果是选人/对线建议的唯一来源。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

TEMPLATE_SIZE = 48
# 面板区域占整屏的比例 (x0, y0, x1, y1)
PANEL_REGION = (0.84, 0.14, 0.99, 0.52)
# 面板内的兜底网格（检测失败时用），实测 2560x1600 下的比例
PANEL_COL_FRAC = (0.352, 0.781)
PANEL_ROW_FRAC = (0.192, 0.328, 0.464, 0.600, 0.736)
PANEL_CELL_FRAC = 0.067  # 格子边长 / 面板高度

TOPBAR_HEIGHT_FRAC = 0.09

# 游戏内 HUD 顶部栏的几何（2560x1600 实测：卡面 92x52、相邻无缝、两组之间隔 308px）
HUD_CARD_H_FRAC = 0.0325   # 卡面高 / 画面高
HUD_CARD_ASPECT = 1.77     # 卡面宽 / 卡面高
HUD_GROUP_GAP_CARDS = 3.35  # 两组之间的空隙（按卡面宽计）


def detect_hud_cells(image: np.ndarray) -> list[tuple[int, int, int, int]]:
    """按比例推算游戏内 HUD 顶部栏的 10 个格子（对局中启动时没有选人界面可用）。

    HUD 随分辨率等比缩放，所以用比例而不是固定像素；识别后还会逐格匹配，
    分数不够高就不会采用。
    """
    if image is None or image.ndim < 2:
        return []
    height, width = image.shape[:2]
    card_h = int(round(height * HUD_CARD_H_FRAC))
    card_w = int(round(card_h * HUD_CARD_ASPECT))
    gap = int(round(card_w * HUD_GROUP_GAP_CARDS))
    total = card_w * 10 + gap
    if card_h < 12 or total >= width:
        return []
    start = (width - total) // 2
    boxes = [(start + i * card_w, 0, card_w, card_h) for i in range(5)]
    enemy_start = start + 5 * card_w + gap
    boxes += [(enemy_start + i * card_w, 0, card_w, card_h) for i in range(5)]
    return boxes


def hud_cell_variants(image: np.ndarray) -> list[list[tuple[int, int, int, int]]]:
    """不同分辨率/HUD 缩放下，顶部栏卡片高度不一定是同一比例。

    返回若干候选布局（高度比例从 0.028 到 0.040），由调用方逐组试匹配，
    取识别数最多的一组。这样 16:9 / 16:10 / 不同 HUD 缩放都能兜住。
    """
    if image is None or image.ndim < 2:
        return []
    height, width = image.shape[:2]
    out: list[list[tuple[int, int, int, int]]] = []
    for frac in (0.0325, 0.036, 0.030, 0.040, 0.028, 0.044):
        card_h = max(12, int(round(height * frac)))
        card_w = max(21, int(round(card_h * HUD_CARD_ASPECT)))
        gap = int(round(card_w * HUD_GROUP_GAP_CARDS))
        total = card_w * 10 + gap
        if total >= width:
            continue
        start = (width - total) // 2
        boxes = [(start + i * card_w, 0, card_w, card_h) for i in range(5)]
        enemy_start = start + 5 * card_w + gap
        boxes += [(enemy_start + i * card_w, 0, card_w, card_h) for i in range(5)]
        out.append(boxes)
    return out


def imread_path(path: Path | str) -> np.ndarray | None:
    """cv2.imread 在 Windows 上打不开非 ASCII 路径（项目路径里有“、”），用 fromfile 绕过。"""
    try:
        data = np.fromfile(str(path), dtype=np.uint8)
    except OSError:
        return None
    if data.size == 0:
        return None
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def imread_rgba(path: Path | str) -> np.ndarray | None:
    """同 imread_path，但保留 alpha 通道（英雄图标是透明底）。"""
    try:
        data = np.fromfile(str(path), dtype=np.uint8)
    except OSError:
        return None
    if data.size == 0:
        return None
    return cv2.imdecode(data, cv2.IMREAD_UNCHANGED)


def imwrite_path(path: Path | str, image: np.ndarray) -> bool:
    """与 imread_path 对应的写文件（cv2.imwrite 同样不认非 ASCII 路径）。"""
    target = Path(path)
    suffix = target.suffix or ".png"
    ok, buffer = cv2.imencode(suffix, image)
    if not ok:
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(buffer.tobytes())
    return True


def ensure_min_size(image: np.ndarray, min_height: int = 900) -> np.ndarray:
    """窗口很小时先放大再匹配：图标低于 ~26px 时 NCC 会失准。"""
    height, width = image.shape[:2]
    if height >= min_height:
        return image
    scale = min_height / float(height)
    size = (int(round(width * scale)), int(min_height))
    return cv2.resize(image, size, interpolation=cv2.INTER_CUBIC)


def composite_on_dark(image: np.ndarray, background: tuple[int, int, int] = (40, 40, 44)) -> np.ndarray:
    """把透明底图标铺到深色背景上——游戏里的图标就是深色底，直接丢 alpha 会变白底。"""
    if image.ndim == 3 and image.shape[2] == 4:
        alpha = image[:, :, 3:4].astype(np.float32) / 255.0
        color = image[:, :, :3].astype(np.float32)
        base = np.array(background, dtype=np.float32)
        return (color * alpha + base * (1.0 - alpha)).astype(np.uint8)
    if image.ndim == 3:
        return image[:, :, :3]
    return image


@dataclass(frozen=True)
class HeroInfo:
    hero_id: int
    short: str
    name: str
    name_loc: str


@dataclass(frozen=True)
class HeroMatch:
    box: tuple[int, int, int, int]
    hero: HeroInfo | None
    score: float
    second: float

    @property
    def margin(self) -> float:
        return self.score - self.second

    @property
    def label(self) -> str:
        return self.hero.name_loc if self.hero else "未识别"


def load_hero_table(path: Path) -> dict[int, HeroInfo]:
    """读取 data/heroes.json（scripts/fetch_hero_icons.ps1 生成，可能带 BOM）。"""
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig") as fh:
        raw = json.load(fh)
    table: dict[int, HeroInfo] = {}
    for key, value in raw.items():
        try:
            hero_id = int(key)
        except ValueError:
            continue
        table[hero_id] = HeroInfo(
            hero_id=hero_id,
            short=str(value.get("short", "")),
            name=str(value.get("name", "")),
            name_loc=str(value.get("name_loc", "")),
        )
    return table


def _center_crop_card(image: np.ndarray) -> np.ndarray:
    """卡面模板是 256x144，顶部英雄栏是 1.25 宽高比，取中间那一段。"""
    height, width = image.shape[:2]
    target_width = int(round(height * 1.25))
    if target_width >= width:
        return image
    left = (width - target_width) // 2
    return image[:, left:left + target_width]


CARD_TRIM_TOP = 0.06  # 顶部英雄栏卡片上沿有一条队伍颜色条
CARD_TRIM_BOTTOM = 0.04
CARD_ASPECT = 1.6  # 栏内格子的宽高比（比 16:9 窄，左右被裁掉）
CARD_SIZE = (160, 90)
CARD_TEMPLATE_W = 256
CARD_TEMPLATE_H = 144


def _aspect_crop(image: np.ndarray, aspect: float) -> np.ndarray:
    """按目标宽高比居中裁切（不变形）。"""
    height, width = image.shape[:2]
    target_width = int(round(height * aspect))
    if target_width <= 0 or height <= 0:
        return image
    if target_width < width:
        left = (width - target_width) // 2
        return image[:, left:left + target_width]
    target_height = int(round(width / aspect))
    if target_height < height:
        top = (height - target_height) // 2
        return image[top:top + target_height, :]
    return image


def prepare_card_cell(cell: np.ndarray) -> np.ndarray:
    """顶部英雄栏格子 → 统一尺寸：先去掉顶部色条/底部名字，再按栏内比例裁切。"""
    height = cell.shape[0]
    top = int(round(height * CARD_TRIM_TOP))
    bottom = max(top + 1, int(round(height * (1.0 - CARD_TRIM_BOTTOM))))
    trimmed = cell[top:bottom, :]
    if trimmed.size == 0:
        trimmed = cell
    return cv2.resize(_aspect_crop(trimmed, CARD_ASPECT), CARD_SIZE, interpolation=cv2.INTER_AREA)


class HeroMatcher:
    """把一块截图和本地英雄模板比对。"""

    def __init__(self, heroes: dict[int, HeroInfo], icons_dir: Path, cards_dir: Path | None = None) -> None:
        self.heroes = heroes
        self.by_short = {info.short: info for info in heroes.values() if info.short}
        self.icons = self._load_templates(icons_dir)
        self.cards = self._load_card_templates(cards_dir) if cards_dir else {}
        self._card_thumbs = {
            short: cv2.resize(template, (83, 47), interpolation=cv2.INTER_AREA)
            for short, template in self.cards.items()
        }

    @property
    def ready(self) -> bool:
        return bool(self.icons or self.cards)

    @staticmethod
    def _resize(image: np.ndarray) -> np.ndarray:
        return cv2.resize(image, (TEMPLATE_SIZE, TEMPLATE_SIZE), interpolation=cv2.INTER_AREA)

    def _load_templates(self, directory: Path) -> dict[str, np.ndarray]:
        templates: dict[str, np.ndarray] = {}
        if not directory or not directory.exists():
            return templates
        for path in sorted(directory.glob("*.png")):
            info = self.by_short.get(path.stem)
            if info is None:
                continue
            image = imread_rgba(path)
            if image is None:
                continue
            templates[path.stem] = self._resize(composite_on_dark(image))
        return templates

    def _load_card_templates(self, directory: Path) -> dict[str, np.ndarray]:
        """卡面模板保持原始比例存着，匹配时按格子比例再裁。"""
        templates: dict[str, np.ndarray] = {}
        if not directory or not directory.exists():
            return templates
        for path in sorted(directory.glob("*.png")):
            if path.stem not in self.by_short:
                continue
            image = imread_rgba(path)
            if image is None:
                continue
            rgb = composite_on_dark(image)
            # CDN 上不同英雄的卡面尺寸不统一（有的 128x72，有的 256x144），先统一再匹配
            if rgb.shape[1] != 256 or rgb.shape[0] != 144:
                interpolation = (
                    cv2.INTER_AREA if rgb.shape[1] > 256 else cv2.INTER_CUBIC
                )
                rgb = cv2.resize(rgb, (256, 144), interpolation=interpolation)
            templates[path.stem] = rgb
        return templates

    def locate_bar_by_self(self, image: np.ndarray, short: str) -> list[tuple[int, int, int, int]] | None:
        """用“自己的英雄卡面”当锚点，反推整条顶部栏的 10 个格子。

        不依赖固定比例：先在画面上方按多种卡面尺寸做模板匹配，找到最像自己英雄的
        那张卡（得到卡宽/卡高），再用实测的栏宽比例（约 13.33 张卡宽、整栏居中）
        推算出全部 10 格。这样 16:9 / 16:10 / 窗口化 / 不同 HUD 缩放都能用。
        """
        template = self.cards.get(short)
        if template is None or image is None or image.ndim < 2:
            return None
        height, width = image.shape[:2]
        band = image[: max(40, int(height * 0.16))]
        best: tuple[float, int, int, int, int] | None = None
        for aspect in (1.62, 1.77):
            low = max(16, int(width * 0.02))
            high = max(low + 8, int(width * 0.085))
            step = max(2, width // 300)
            for card_w in range(low, high, step):
                card_h = int(round(card_w / aspect))
                if card_h < 16 or card_h > band.shape[0]:
                    continue
                tmpl = cv2.resize(template, (card_w, card_h), interpolation=cv2.INTER_AREA)
                result = cv2.matchTemplate(band, tmpl, cv2.TM_CCOEFF_NORMED)
                _, score, _, loc = cv2.minMaxLoc(result)
                if best is None or score > best[0]:
                    best = (score, card_w, card_h, loc[0], loc[1])
        if best is None or best[0] < 0.45:
            return None
        _, card_w, card_h, _, card_y = best
        big = card_w / width > 0.05
        step = card_w * (1.06 if big else 1.0)
        gap = card_w * (2.79 if big else 3.3)
        total = step * 9 + gap + card_w
        start = (width - total) / 2.0
        boxes = [(int(round(start + i * step)), card_y, card_w, card_h) for i in range(5)]
        enemy_start = start + step * 5 + gap
        boxes += [(int(round(enemy_start + i * step)), card_y, card_w, card_h) for i in range(5)]
        return boxes

    def locate_bar(self, image: np.ndarray, heroes: list[HeroInfo | None], min_score: float = 0.5):
        """按已知的 10 个英雄，在画面上方定位各自头像（返回图像坐标的 (x, y, w, h)）。

        游戏内 HUD 的顶部栏和决策界面尺寸不同，靠颜色检测会被 3D 背景干扰，
        所以反过来：拿已识别出的英雄卡面去多尺度匹配，命中的位置就是头像。
        """
        if not self.cards or not heroes:
            return []
        height = image.shape[0]
        band = image[0 : min(220, max(120, int(height * 0.12))), :]
        if band.size == 0:
            return []
        results: list[tuple[float, int, int, int, int] | None] = []
        for hero in heroes:
            template = self.cards.get(hero.short) if hero is not None else None
            if template is None:
                results.append(None)
                continue
            best: tuple[float, int, int, int, int] | None = None
            for scale in np.arange(0.18, 0.62, 0.02):
                width = max(1, int(round(template.shape[1] * scale)))
                tall = max(1, int(round(template.shape[0] * scale)))
                if tall > band.shape[0] or width > band.shape[1]:
                    continue
                patch = cv2.resize(template, (width, tall), interpolation=cv2.INTER_AREA)
                response = cv2.matchTemplate(band, patch, cv2.TM_CCOEFF_NORMED)
                _, peak, _, location = cv2.minMaxLoc(response)
                if best is None or peak > best[0]:
                    best = (float(peak), location[0], location[1], width, tall)
            results.append(best)
        good = [item for item in results if item is not None and item[0] >= min_score]
        if len(good) < 8:
            return []
        # 同一排头像高度/宽度应一致，取中位消除个别错位
        widths = sorted(item[3] for item in good)
        heights = sorted(item[4] for item in good)
        mid_w = widths[len(widths) // 2]
        mid_h = heights[len(heights) // 2]
        boxes = []
        for item in results:
            if item is None or item[0] < min_score:
                boxes.append(None)
                continue
            _, x, y, _, _ = item
            boxes.append((x, y, mid_w, mid_h))
        return boxes

    def _prepare_cell(self, cell: np.ndarray) -> np.ndarray:
        """HUD 卡面（1.77）直接缩放；选人界面大卡面才裁装饰边。"""
        if cell.shape[1] >= cell.shape[0] * 1.70:
            return cv2.resize(cell, CARD_SIZE, interpolation=cv2.INTER_AREA)
        return prepare_card_cell(cell)

    def match_card_fast(self, cell: np.ndarray) -> float:
        """只做粗排（低分辨率缩略图），用于快速评估“这一格像不像某个英雄”，

        供自适应定位时筛选候选布局，避免每个候选都跑完整细验。
        """
        if not self._card_thumbs or cell is None or cell.size == 0:
            return 0.0
        prepared = self._prepare_cell(cell)
        small = cv2.resize(prepared, (80, 45), interpolation=cv2.INTER_AREA)
        pad = cv2.copyMakeBorder(small, 8, 8, 8, 8, cv2.BORDER_CONSTANT, value=(40, 40, 44))
        best = 0.0
        for thumb in self._card_thumbs.values():
            best = max(best, float(cv2.matchTemplate(pad, thumb, cv2.TM_CCOEFF_NORMED).max()))
        return best

    def locate_bar_candidates(
        self, image: np.ndarray, short: str, limit: int = 6
    ) -> list[tuple[float, list[tuple[int, int, int, int]]]]:
        """用自己英雄的卡面在不同尺寸下匹配，返回若干“整条栏布局”候选。

        卡面尺寸估错时布局会整体错位，所以返回多个候选，由调用方用
        `match_card_fast` 逐格打分，挑出最可信的一组再跑完整识别。
        """
        template = self.cards.get(short)
        if template is None or image is None or image.ndim < 2:
            return []
        height, width = image.shape[:2]
        band = image[: max(40, int(height * 0.16))]
        found: list[tuple[float, int, int, int]] = []
        for aspect in (1.62, 1.77):
            low = max(16, int(width * 0.015))
            high = max(low + 8, int(width * 0.09))
            step = max(2, width // 320)
            for card_w in range(low, high, step):
                card_h = int(round(card_w / aspect))
                if card_h < 16 or card_h > band.shape[0]:
                    continue
                tmpl = cv2.resize(template, (card_w, card_h), interpolation=cv2.INTER_AREA)
                result = cv2.matchTemplate(band, tmpl, cv2.TM_CCOEFF_NORMED)
                _, score, _, loc = cv2.minMaxLoc(result)
                found.append((float(score), card_w, card_h, loc[1]))
        found.sort(reverse=True)
        picked: list[tuple[float, list[tuple[int, int, int, int]]]] = []
        seen: set[int] = set()
        for score, card_w, card_h, card_y in found:
            if score < 0.4:
                break
            key = card_w // 4
            if key in seen:
                continue
            seen.add(key)
            picked.append((score, self._layout_from_card(width, card_w, card_h, card_y)))
            if len(picked) >= limit:
                break
        return picked

    @staticmethod
    def _layout_from_card(
        width: int, card_w: int, card_h: int, card_y: int
    ) -> list[tuple[int, int, int, int]]:
        big = card_w / max(1, width) > 0.05
        step = card_w * (1.06 if big else 1.0)
        gap = card_w * (2.79 if big else 3.3)
        total = step * 9 + gap + card_w
        start = (width - total) / 2.0
        boxes = [(int(round(start + i * step)), card_y, card_w, card_h) for i in range(5)]
        enemy_start = start + step * 5 + gap
        boxes += [(int(round(enemy_start + i * step)), card_y, card_w, card_h) for i in range(5)]
        return boxes

    def match_card(self, cell: np.ndarray) -> list[tuple[HeroInfo, float]]:
        """顶部英雄栏匹配。

        栏内卡片是卡面原图的放大裁切（每局缩放略有差异），所以先低分辨率粗排，
        再对前 3 名做“放大 + 多尺度 + 平移搜索”的细验，兼顾速度和抗缩放。
        """
        if not self.cards:
            return []
        # HUD 顶部栏的卡面本身已是 1.77 的宽高比、也没有选人界面那种装饰边，
        # 直接用原图缩放；选人界面的大卡面才走裁剪。
        if cell.shape[1] >= cell.shape[0] * 1.70:
            prepared = cv2.resize(cell, CARD_SIZE, interpolation=cv2.INTER_AREA)
        else:
            prepared = prepare_card_cell(cell)
        small = cv2.resize(prepared, (80, 45), interpolation=cv2.INTER_AREA)
        pad = cv2.copyMakeBorder(small, 8, 8, 8, 8, cv2.BORDER_CONSTANT, value=(40, 40, 44))
        coarse = sorted(
            (
                (float(cv2.matchTemplate(pad, thumb, cv2.TM_CCOEFF_NORMED).max()), short)
                for short, thumb in self._card_thumbs.items()
            ),
            reverse=True,
        )
        candidates = [short for _, short in coarse[:5]]
        # 细验放到模板原生尺寸上做：HUD 的小卡面也能看清细节，
        # 只按前 3 名做多尺度比对，成本可控。
        large = cv2.resize(prepared, (CARD_TEMPLATE_W, CARD_TEMPLATE_H), interpolation=cv2.INTER_CUBIC)
        pad = 20
        padded = cv2.copyMakeBorder(large, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=(40, 40, 44))
        fine: dict[str, float] = {}
        for short in candidates:
            template = self.cards[short]
            best = 0.0
            for factor in (0.92, 1.0, 1.08):
                resized = cv2.resize(
                    template,
                    (int(round(template.shape[1] * factor)), int(round(template.shape[0] * factor))),
                    interpolation=cv2.INTER_AREA,
                )
                if resized.shape[0] > padded.shape[0] or resized.shape[1] > padded.shape[1]:
                    continue
                best = max(best, float(cv2.matchTemplate(padded, resized, cv2.TM_CCOEFF_NORMED).max()))
            fine[short] = best
        scored = [(self.by_short[short], score) for short, score in fine.items()]
        scored.sort(key=lambda item: item[1], reverse=True)
        used = {hero.short for hero, _ in scored}
        for score, short in coarse:
            if short in used:
                continue
            scored.append((self.by_short[short], score * 0.9))
        return scored

    def rank(self, cell: np.ndarray, kind: str = "icon") -> list[tuple[HeroInfo, float]]:
        templates = self.icons if kind == "icon" else self.cards
        if not templates:
            return []
        prepared = self._resize(cell)
        return self._score_against(prepared, templates)

    def _score_against(
        self, prepared: np.ndarray, templates: dict[str, np.ndarray]
    ) -> list[tuple[HeroInfo, float]]:
        scored: list[tuple[HeroInfo, float]] = []
        for short, template in templates.items():
            result = cv2.matchTemplate(prepared, template, cv2.TM_CCOEFF_NORMED)
            scored.append((self.by_short[short], float(result.max())))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored

    def identify(
        self,
        image: np.ndarray,
        box: tuple[int, int, int, int],
        kind: str = "icon",
        min_score: float = 0.55,
        min_gap: float = 0.02,
    ) -> HeroMatch:
        x, y, w, h = box
        x = max(0, x)
        y = max(0, y)
        if kind == "icon" and w and h:
            # 面板格子的检测偶尔会偏 2–4 像素；把格子四周多裁一圈再滑动匹配，
            # 让 matchTemplate 自己找最佳对齐位置，避免因为几像素偏移分数暴跌。
            pad = max(4, int(round(min(w, h) * 0.15)))
            left = max(0, x - pad)
            top = max(0, y - pad)
            right = min(image.shape[1], x + w + pad)
            bottom = min(image.shape[0], y + h + pad)
            patch = image[top:bottom, left:right]
            if patch.size:
                scale = TEMPLATE_SIZE / max(1, w)
                size = (max(1, int(round(patch.shape[1] * scale))), max(1, int(round(patch.shape[0] * scale))))
                prepared = cv2.resize(patch, size, interpolation=cv2.INTER_AREA)
                ranked = self._score_against(prepared, self.icons)
                return self._verdict(box, ranked, min_score, min_gap)
        cell = image[y:y + h, x:x + w]
        if cell.size == 0:
            return HeroMatch(box, None, 0.0, 0.0)
        ranked = self.match_card(cell) if kind == "card" else self.rank(cell, kind)
        return self._verdict(box, ranked, min_score, min_gap)

    @staticmethod
    def _verdict(
        box: tuple[int, int, int, int],
        ranked: list[tuple[HeroInfo, float]],
        min_score: float,
        min_gap: float,
    ) -> HeroMatch:
        if not ranked:
            return HeroMatch(box, None, 0.0, 0.0)
        best_hero, best_score = ranked[0]
        second_score = ranked[1][1] if len(ranked) > 1 else 0.0
        hero = best_hero if (best_score >= min_score and best_score - second_score >= min_gap) else None
        return HeroMatch(box, hero, best_score, second_score)


# ---------------------------------------------------------------------------
# 格子定位
# ---------------------------------------------------------------------------


def _candidate_squares(region: np.ndarray, min_side: int = 20, max_side: int = 100) -> list[tuple[int, int, int, int]]:
    hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
    value = hsv[:, :, 2]
    saturation = hsv[:, :, 1]
    mask = ((value > 38) & (saturation > 20)).astype(np.uint8) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes: list[tuple[int, int, int, int]] = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if not (min_side <= w <= max_side and min_side <= h <= max_side):
            continue
        if not (0.65 <= w / h <= 1.5):
            continue
        if w * h < 400:
            continue
        boxes.append((x, y, w, h))
    return boxes


def _cluster(values: list[float], tolerance: float) -> list[float]:
    if not values:
        return []
    ordered = sorted(values)
    groups: list[list[float]] = [[ordered[0]]]
    for value in ordered[1:]:
        if value - groups[-1][-1] <= tolerance:
            groups[-1].append(value)
        else:
            groups.append([value])
    return [float(np.mean(group)) for group in groups]


def _fit_grid(rows: list[float], count: int = 5, prior_start: float | None = None) -> list[float] | None:
    """从部分检测到的行中心推 5 个等距行（容忍中间缺行）。

    只有 4 行被检出时，"从 402 开始" 和 "从 320 开始" 都能完美拟合；
    用先验（第 0 行的预期位置）在候选里挑一个，避免整体错一行。
    """
    rows = sorted(rows)
    if len(rows) >= count:
        return rows[:count]
    if len(rows) < 2:
        return None
    spacing = float(np.median(np.diff(rows)))
    if spacing <= 1:
        return None
    candidates = []
    for shift in range(count):
        start = rows[0] - shift * spacing
        grid = [start + i * spacing for i in range(count)]
        error = sum(min(abs(row - g) for g in grid) for row in rows) / len(rows)
        candidates.append((error, grid, start))
    best_error = min(item[0] for item in candidates)
    good = [item for item in candidates if item[0] <= best_error + spacing * 0.15]
    if prior_start is not None:
        return min(good, key=lambda item: abs(item[2] - prior_start))[1]
    return good[0][1]


def detect_panel_cells(image: np.ndarray) -> dict[tuple[int, int], tuple[int, int, int, int]]:
    """返回 {(col, row): 绝对坐标 box}，col 0=我方、1=敌方，row 0..4。"""
    height, width = image.shape[:2]
    x0 = int(width * PANEL_REGION[0])
    y0 = int(height * PANEL_REGION[1])
    x1 = int(width * PANEL_REGION[2])
    y1 = int(height * PANEL_REGION[3])
    region = image[y0:y1, x0:x1]
    if region.size == 0:
        return {}

    boxes = _candidate_squares(region)
    expected = int(round(region.shape[0] * PANEL_CELL_FRAC))
    side = expected
    if boxes:
        median = int(np.median([max(w, h) for (_, _, w, h) in boxes]))
        # 检测出的"方块"有时把图标边框/百分比数字并进来（52 vs 41），
        # 偏离标定值太多就回到按面板高度算出的固定边长。
        if 0.8 * expected <= median <= 1.2 * expected:
            side = median

    if len(boxes) >= 3:
        cols = _cluster([x + w / 2 for (x, _, w, _) in boxes], tolerance=side * 1.2)
        rows = _cluster([y + h / 2 for (_, y, _, h) in boxes], tolerance=side * 0.5)
        row_grid = _fit_grid(rows, 5, prior_start=region.shape[0] * PANEL_ROW_FRAC[0])
        if len(cols) != 2:
            cols = [region.shape[1] * f for f in PANEL_COL_FRAC]
        if row_grid is None:
            row_grid = [region.shape[0] * f for f in PANEL_ROW_FRAC]
    else:
        cols = [region.shape[1] * f for f in PANEL_COL_FRAC]
        row_grid = [region.shape[0] * f for f in PANEL_ROW_FRAC]

    cells: dict[tuple[int, int], tuple[int, int, int, int]] = {}
    half = side // 2
    for col, cx in enumerate(sorted(cols)):
        for row, cy in enumerate(sorted(row_grid)):
            left = int(round(x0 + cx - half))
            top = int(round(y0 + cy - half))
            cells[(col, row)] = (left, top, side, side)
    return cells


def _column_runs(mask: np.ndarray) -> list[tuple[int, int]]:
    """一维布尔数组里的连续 True 段，返回 (起点, 长度)。"""
    runs: list[tuple[int, int]] = []
    start = None
    for index, value in enumerate(mask):
        if value and start is None:
            start = index
        elif not value and start is not None:
            runs.append((start, index - start))
            start = None
    if start is not None:
        runs.append((start, len(mask) - start))
    return runs


def detect_bar_strips(image: np.ndarray) -> list[tuple[int, int, int, int]]:
    """按顶部彩色队伍条定位 10 张英雄卡（不依赖 DPI/UI 缩放）。

    每张卡上方有一条饱和色带；色带是整栏里唯一稳定的高饱和横向元素，
    因此按列找色带、再按色带高度起算卡面，比轮廓/模板更耐缩放。
    失败返回空列表（调用方退回旧的轮廓/比例方案）。
    """
    height, width = image.shape[:2]
    band_height = max(10, int(round(height * 0.06)))
    hsv = cv2.cvtColor(image[:band_height, :], cv2.COLOR_BGR2HSV)
    mask = ((hsv[:, :, 1] > 80) & (hsv[:, :, 2] > 70)).any(axis=0)

    segments = [run for run in _column_runs(mask) if run[1] >= max(8, width * 0.008)]
    if not segments:
        return []
    merged: list[tuple[int, int]] = []
    for start, length in segments:
        if merged and start - (merged[-1][0] + merged[-1][1]) <= max(3, width * 0.004):
            merged[-1] = (merged[-1][0], start + length - merged[-1][0])
        else:
            merged.append((start, length))
    merged = [run for run in merged if width * 0.015 <= run[1] <= width * 0.12]
    if len(merged) != 10:
        return []

    ordered = sorted(merged, key=lambda run: run[0])
    widths = sorted(run[1] for run in ordered)
    card_width = widths[len(widths) // 2]
    if any(abs(run[1] - card_width) > card_width * 0.35 for run in ordered):
        return []
    for group in (ordered[:5], ordered[5:]):
        steps = [group[i + 1][0] - group[i][0] for i in range(4)]
        if max(steps) - min(steps) > max(4, card_width * 0.15):
            return []

    card_height = int(round(card_width / 1.5))
    cells: list[tuple[int, int, int, int]] = []
    for start, length in ordered:
        columns = hsv[:, start:start + length]
        strip = ((columns[:, :, 1] > 80) & (columns[:, :, 2] > 70))
        coverage = strip.mean(axis=1)
        top = 0
        for row, value in enumerate(coverage):
            if value >= 0.75:
                top = row
                break
        cells.append((start, top, min(length, card_width), card_height))
    return cells


def detect_topbar_cells(image: np.ndarray) -> list[tuple[int, int, int, int]]:
    """顶部英雄栏的 10 张卡（从左到右）。失败返回空列表。"""
    height, width = image.shape[:2]
    band = image[0:int(height * TOPBAR_HEIGHT_FRAC), :]
    hsv = cv2.cvtColor(band, cv2.COLOR_BGR2HSV)
    mask = ((hsv[:, :, 2] > 45) & (hsv[:, :, 1] > 25)).astype(np.uint8) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes: list[tuple[int, int, int, int]] = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w < 60 or h < 40 or w > 400 or h > 260:
            continue
        if not (0.9 <= w / h <= 1.8):
            continue
        if w * h < 3500:
            continue
        boxes.append((x, y, w, h))

    if len(boxes) < 6:
        return []

    boxes.sort(key=lambda box: box[0])
    # 按最大间距切成左右两组
    gaps = [(boxes[i + 1][0] - (boxes[i][0] + boxes[i][2]), i) for i in range(len(boxes) - 1)]
    if not gaps:
        return []
    _, split = max(gaps)
    left, right = boxes[:split + 1], boxes[split + 1:]
    if len(left) != 5 or len(right) != 5:
        return []
    # 检测框会被卡面高光/名字带偏，10 张卡其实是等间距的：用首尾拟合网格
    widths = sorted(box[2] for box in left + right)
    heights = sorted(box[3] for box in left + right)
    width = widths[len(widths) // 2]
    height = heights[len(heights) // 2]
    cells: list[tuple[int, int, int, int]] = []
    for group in (left, right):
        start = min(box[0] for box in group)
        end = max(box[0] for box in group)
        step = (end - start) / 4.0
        for index in range(5):
            cells.append((int(round(start + index * step)), 0, min(width, int(round(step))), height))
    return cells


def identify_panel(
    image: np.ndarray,
    matcher: HeroMatcher,
    min_score: float = 0.55,
    min_gap: float = 0.02,
) -> dict[str, list[HeroMatch]]:
    """识别"战友与宿敌"面板：ally 5 个（第 0 个是自己）、enemy 5 个。"""
    cells = detect_panel_cells(image)
    ally: list[HeroMatch] = []
    enemy: list[HeroMatch] = []
    for row in range(5):
        box = cells.get((0, row))
        if box:
            ally.append(matcher.identify(image, box, "icon", min_score, min_gap))
        box = cells.get((1, row))
        if box:
            enemy.append(matcher.identify(image, box, "icon", min_score, min_gap))
    return {"ally": ally, "enemy": enemy}


def identify_topbar(
    image: np.ndarray,
    matcher: HeroMatcher,
    min_score: float = 0.55,
    min_gap: float = 0.02,
) -> dict[str, list[HeroMatch]]:
    """识别顶部英雄栏：前 5 个我方、后 5 个敌方。"""
    strips = detect_bar_strips(image)
    boxes = strips or detect_topbar_cells(image)
    if not boxes:
        return {"ally": [], "enemy": []}
    matches = [matcher.identify(image, box, "card", min_score, min_gap) for box in boxes]
    if strips:
        # 高分辨率缩到 720p 时个别卡面细节变少，分数会贴近阈值；
        # 色条定位可信，对漏识别再放宽一点重试，避免整栏只认出一半。
        relaxed = max(0.45, min_score - 0.08)
        for index, match in enumerate(matches):
            if match.label != "未识别":
                continue
            retry = matcher.identify(image, boxes[index], "card", relaxed, min_gap)
            if retry.label != "未识别":
                matches[index] = retry
    return {"ally": matches[:5], "enemy": matches[5:]}

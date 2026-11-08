"""顶部英雄栏下面的名字条：把识别出的英雄名字写在对应头像下方。

它只负责画字，不接收鼠标；位置由 app 根据截屏几何换算成逻辑坐标。
"""

from __future__ import annotations

from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import QColor, QFont, QGuiApplication, QPainter
from PyQt6.QtWidgets import QWidget

ALLY_COLOR = QColor(126, 231, 135)   # 队友：浅绿
ENEMY_COLOR = QColor(255, 123, 114)  # 对手：浅红
SHADOW_COLOR = QColor(0, 0, 0, 220)
ROW_HEIGHT = 20
# 卡面下沿再往下一点：游戏自己会画玩家名，英雄名放在玩家名下面更清楚
NAME_GAP = 28
NAME_GAP_SMALL = 26
# 6 字名字在游戏内 HUD 里放不下，用大家习惯的简称
ABBREV = {
    "半人马战行者": "半人马",
    "天穹守望者": "天穹",
    "食人魔魔法师": "食人魔",
}


class NameStrip(QWidget):
    """无边框、置顶、点击穿透的横条，只在顶部英雄栏下方显示名字。"""

    def __init__(self) -> None:
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
            | Qt.WindowType.WindowDoesNotAcceptFocus,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._labels: list[tuple[int, str, bool]] = []
        self._font_px = 15
        self._spacing = 60
        self.hide()

    # ------------------------------------------------------------------
    def show_names(
        self,
        boxes: list[tuple[int, int, int, int]],
        names: list[str],
        ally_count: int = 5,
    ) -> None:
        """boxes 是屏幕物理像素坐标，names 与 boxes 一一对应（前 5 个队友）。"""
        if not boxes or not names:
            self.clear()
            return
        ratio = QGuiApplication.primaryScreen().devicePixelRatio() or 1.0
        left = min(box[0] for box in boxes)
        right = max(box[0] + box[2] for box in boxes)
        bottom = max(box[1] + box[3] for box in boxes)
        # 决策界面卡面高（~107），游戏内 HUD 卡面矮（~55），间距分开设
        heights = sorted(box[3] for box in boxes)
        tall_enough = heights[len(heights) // 2] >= 80
        gap = NAME_GAP if tall_enough else NAME_GAP_SMALL
        centers = [(box[0] + box[2] / 2.0) / ratio for box in boxes]
        steps = [centers[i + 1] - centers[i] for i in range(len(centers) - 1) if centers[i + 1] > centers[i]]
        spacing = min(steps) if steps else max(1.0, (right - left) / ratio)
        display = [ABBREV.get(name, name) for name in names]
        longest = max(len(name) for name in display) or 1
        # 字号跟着头像间距走：不同分辨率/窗口大小下都不会互相压住
        font_px = int(spacing * 0.95 / longest)
        font_px = max(9, min(16, font_px))
        # 仍有超长名字（比如 6 字简称后也放不下）就截断加省略号
        fit = max(1, int(spacing * 0.95 / font_px))
        display = [
            name if len(name) <= fit else name[: max(1, fit - 1)] + "…"
            for name in display
        ]
        self._font_px = font_px
        self._spacing = max(24, int(round(spacing)))
        row_height = font_px + 6
        # 左右各留半个字宽，首尾名字不会被窗口边缘裁掉
        pad = int(round(spacing / 2))
        logical_left = int(round(left / ratio)) - pad
        logical_top = int(round((bottom + gap) / ratio))
        logical_width = max(1, int(round((right - left) / ratio))) + 2 * pad
        self._labels = [
            (
                int(round(center)) - logical_left,
                name,
                index < ally_count,
            )
            for index, (center, name) in enumerate(zip(centers, display))
        ]
        self.setGeometry(logical_left, logical_top, logical_width, row_height)
        self.show()
        self.raise_()
        self.update()

    def clear(self) -> None:
        self._labels.clear()
        self.hide()

    # ------------------------------------------------------------------
    def paintEvent(self, event) -> None:  # noqa: N802 - Qt 接口
        if not self._labels:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        font = QFont("Microsoft YaHei UI")
        font.setPixelSize(self._font_px)
        font.setBold(True)
        painter.setFont(font)
        width = max(24, self._spacing)
        for center_x, text, is_ally in self._labels:
            rect = QRect(center_x - width // 2, 0, width, self.height())
            painter.setPen(SHADOW_COLOR)
            for dx, dy in ((-1, 0), (1, 0), (0, 1), (0, -1)):
                painter.drawText(rect.translated(dx, dy), int(Qt.AlignmentFlag.AlignCenter), text)
            painter.setPen(ALLY_COLOR if is_ally else ENEMY_COLOR)
            painter.drawText(rect, int(Qt.AlignmentFlag.AlignCenter), text)
        painter.end()

"""置顶、无边框、半透明的教练卡片。

卡片平时半透明（约为设定值的 50%），只在语音播报后的 10 秒内恢复完整透明度，
播报结束自动变淡，尽量不挡视野。
阵容名字画在游戏顶部头像下方（ui/namestrip.py），卡片里不再重复头像。
"""

from __future__ import annotations

from PyQt6.QtCore import QPoint, QTimer, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

FONT_FAMILY = "Microsoft YaHei UI"
CARD_WIDTH = 500
DIM_FACTOR = 0.5
HIGHLIGHT_SECONDS = 10.0


class OverlayWindow(QWidget):
    def __init__(
        self,
        opacity: float = 0.9,
        click_through: bool = True,
        dim_opacity: float | None = None,
    ) -> None:
        super().__init__()
        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
            | Qt.WindowType.Tool
        )
        if click_through:
            # 点击穿透：鼠标事件直接落到游戏里，卡片不挡操作
            flags |= Qt.WindowType.WindowTransparentForInput
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self._full_opacity = max(0.35, min(1.0, opacity))
        self._dim_opacity = max(
            0.2,
            min(
                self._full_opacity,
                dim_opacity if dim_opacity is not None else self._full_opacity * DIM_FACTOR,
            ),
        )
        self.setWindowOpacity(self._dim_opacity)
        self.setFixedWidth(CARD_WIDTH)
        self._drag_from: QPoint | None = None

        self._dim_timer = QTimer(self)
        self._dim_timer.setSingleShot(True)
        self._dim_timer.timeout.connect(self._apply_dim)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 16)
        layout.setSpacing(7)

        self._title = self._make_label(20, True, QColor(245, 246, 250))
        self._info = self._make_label(15, False, QColor(214, 219, 230))
        self._build = self._make_label(16, False, QColor(196, 226, 196))
        self._hint = self._make_label(19, True, QColor(245, 214, 140))

        for widget in (self._title, self._info, self._build, self._hint):
            layout.addWidget(widget)

        self.render("DOTA2 入门教练 · 等待对局开始", "", "", "")

    @staticmethod
    def _make_label(size: int, bold: bool, color: QColor) -> QLabel:
        label = QLabel("")
        label.setWordWrap(True)
        # 固定宽度，否则 QLabel 按最小宽度算 sizeHint，换行数会算多、卡片出现大块空白
        label.setFixedWidth(CARD_WIDTH - 36)
        font = QFont(FONT_FAMILY)
        font.setPixelSize(size)
        font.setBold(bold)
        label.setFont(font)
        label.setStyleSheet(f"color: {color.name(QColor.NameFormat.HexRgb)};")
        return label

    # ------------------------------------------------------------------
    # 设置热更新（面板“设置”页保存时调用）
    # ------------------------------------------------------------------
    def set_opacity(self, opacity: float) -> None:
        """清晰状态的不透明度。"""
        self._full_opacity = max(0.35, min(1.0, float(opacity)))
        if not self._dim_timer.isActive():
            self.setWindowOpacity(self._dim_opacity)

    def set_dim_opacity(self, opacity: float) -> None:
        """模糊状态（平时）的不透明度。"""
        self._dim_opacity = max(0.2, min(self._full_opacity, float(opacity)))
        if not self._dim_timer.isActive():
            self.setWindowOpacity(self._dim_opacity)

    def set_opacities(self, clear: float, dim: float) -> None:
        self.set_opacity(clear)
        self.set_dim_opacity(dim)

    def set_click_through(self, click_through: bool) -> None:
        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
            | Qt.WindowType.Tool
        )
        if click_through:
            flags |= Qt.WindowType.WindowTransparentForInput
        was_visible = self.isVisible()
        self.setWindowFlags(flags)
        if was_visible:
            self.show()

    # ------------------------------------------------------------------
    # 透明度：播报时恢复，停 10 秒后变淡
    # ------------------------------------------------------------------
    def _apply_dim(self) -> None:
        self.setWindowOpacity(self._dim_opacity)

    def highlight(self, seconds: float = HIGHLIGHT_SECONDS) -> None:
        self.setWindowOpacity(self._full_opacity)
        self._dim_timer.start(int(seconds * 1000))

    # ------------------------------------------------------------------
    # 内容
    # ------------------------------------------------------------------
    def _resize_to_content(self) -> None:
        # 用布局的 sizeHint 算高度再 resize，而不是 adjustSize()：
        # 在 125%/150% 缩放的屏幕上，adjustSize 会拿物理像素和固定宽度打架，
        # Qt 会刷 "Unable to set geometry ..." 警告（卡片本身没问题）。
        layout = self.layout()
        if layout is not None:
            layout.activate()
            self.resize(CARD_WIDTH, layout.sizeHint().height())

    def render(self, title: str, info: str, build: str, hint: str) -> None:
        self._title.setText(title)
        self._info.setText(info)
        self._info.setVisible(bool(info))
        self._build.setText(build)
        self._build.setVisible(bool(build))
        self._hint.setText(hint)
        self._hint.setVisible(bool(hint))
        self._resize_to_content()

    def render_message(self, title: str, lines: list[str], hint: str = "") -> None:
        """纯文字卡片：主界面问候、赛后小结用。"""
        self.render(title, "\n".join(lines), "", hint)

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt 命名
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setBrush(QColor(16, 18, 24, 232))
        painter.setPen(QPen(QColor(90, 120, 190, 170), 1))
        rounded = self.rect().adjusted(1, 1, -1, -1)
        painter.drawRoundedRect(rounded, 10, 10)

    # 拖动窗口
    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_from = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._drag_from is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_from)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self._drag_from = None

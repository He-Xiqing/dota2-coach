"""界面视觉规范：颜色、字体与控件样式（主窗口与对话框共用）。"""

from __future__ import annotations

from PyQt6.QtGui import QFont

FONT_FAMILY = "Microsoft YaHei UI"


def font(px: int, bold: bool = False) -> QFont:
    """按像素取字体：不同 DPI 下视觉大小一致（point 会随 DPI 放大）。"""
    f = QFont(FONT_FAMILY)
    f.setPixelSize(px)
    f.setBold(bold)
    return f

BG = "#F6F7F9"
SURFACE = "#FFFFFF"
BORDER = "#E3E7EE"
TEXT = "#1C2430"
MUTED = "#6B7688"
PRIMARY = "#2F6FED"
PRIMARY_HOVER = "#2A63D4"
SUCCESS = "#1FA971"
WARNING = "#E4A11B"
DANGER = "#E5484D"

RADIUS = 10

STYLE = f"""
QWidget {{
    font-family: "{FONT_FAMILY}";
    font-size: 13px;
    color: {TEXT};
    background: {BG};
}}
QMainWindow, QDialog {{ background: {BG}; }}
QLabel {{ background: transparent; }}
QWidget#Backdrop {{ background: transparent; }}
QFrame#Card, QFrame#Side {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: {RADIUS}px;
}}
QLabel#H1 {{ font-size: 26px; font-weight: 700; }}
QLabel#H2 {{ font-size: 18px; font-weight: 700; }}
QLabel#H3 {{ font-size: 14px; font-weight: 600; }}
QLabel#Muted {{ color: {MUTED}; }}
QLabel#Tag {{
    color: {PRIMARY};
    background: #EAF1FF;
    border-radius: 8px;
    padding: 2px 8px;
}}
QPushButton {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 8px 16px;
}}
QPushButton:hover {{ border-color: {PRIMARY}; color: {PRIMARY}; }}
QPushButton#Primary {{
    background: {PRIMARY};
    border: none;
    color: white;
    font-weight: 600;
}}
QPushButton#Primary:hover {{ background: {PRIMARY_HOVER}; }}
QPushButton#Danger {{ color: {DANGER}; }}
QCheckBox, QRadioButton {{ spacing: 8px; }}
QSlider::groove:horizontal {{
    height: 4px; background: {BORDER}; border-radius: 2px;
}}
QSlider::handle:horizontal {{
    width: 14px; margin: -6px 0; border-radius: 7px; background: {PRIMARY};
}}
QComboBox, QSpinBox, QLineEdit {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 5px 8px;
    min-height: 22px;
}}
QTabWidget::pane {{ border: 1px solid {BORDER}; border-radius: {RADIUS}px; background: {SURFACE}; }}
QTabBar::tab {{
    padding: 8px 18px; background: {BG}; border: 1px solid {BORDER};
    border-bottom: none; border-top-left-radius: 8px; border-top-right-radius: 8px;
}}
QTabBar::tab:selected {{ background: {SURFACE}; color: {PRIMARY}; }}
"""

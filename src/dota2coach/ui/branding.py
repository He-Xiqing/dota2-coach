"""应用图标与 Windows 任务栏标识。"""

from __future__ import annotations

import ctypes
import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap

APP_NAME = "DOTA2 入门教练"
APP_NAME_EN = "DOTA2 GETTING STARTED Coach"
APP_USER_MODEL_ID = "Dota2Coach.App"


def icon_path(data_dir: Path | str) -> Path:
    """优先 .ico（多尺寸），没有时退回 .png。"""
    base = Path(data_dir)
    ico = base / "app.ico"
    if ico.exists():
        return ico
    return base / "app.png"


def app_icon(data_dir: Path | str | None) -> QIcon:
    """读取应用图标；缺失时返回空 QIcon（调用方自行回退）。"""
    if data_dir is None:
        return QIcon()
    path = icon_path(data_dir)
    if not path.exists():
        return QIcon()
    icon = QIcon(str(path))
    return icon


def fallback_icon() -> QIcon:
    """图标文件缺失时的占位图：蓝底白 D。"""
    pixmap = QPixmap(32, 32)
    pixmap.fill(QColor("#2F6FED"))
    painter = QPainter(pixmap)
    painter.setPen(QColor("white"))
    painter.drawText(pixmap.rect(), int(Qt.AlignmentFlag.AlignCenter), "D")
    painter.end()
    return QIcon(pixmap)


def set_windows_app_id() -> None:
    """让任务栏按本程序（而不是 python.exe）分组和显示图标。"""
    if not sys.platform.startswith("win"):
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except (AttributeError, OSError):
        pass

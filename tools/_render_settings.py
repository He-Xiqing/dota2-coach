"""离屏渲染设置页（辅助 tab），确认小地图一行。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from PyQt6.QtWidgets import QApplication, QTabWidget  # noqa: E402

from dota2coach.config import load_config  # noqa: E402
from dota2coach.ui.panel import SettingsDialog  # noqa: E402
from dota2coach.ui import theme  # noqa: E402


def main() -> int:
    app = QApplication.instance() or QApplication([])
    cfg = load_config()
    dlg = SettingsDialog(cfg)
    dlg.setStyleSheet(theme.STYLE)
    tabs = dlg.findChild(QTabWidget)
    if tabs is not None:
        tabs.setCurrentIndex(4)
    dlg.resize(560, 470)
    dlg.show()
    app.processEvents()
    out = Path("logs/screenshots/set-minimap.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    dlg.grab().save(str(out))
    print("saved", out, out.stat().st_size)
    dlg.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

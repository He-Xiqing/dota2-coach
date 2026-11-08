"""按语言渲染设置对话框。用法：python tools/_render_settings_lang.py en 4 out.png"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from PyQt6.QtWidgets import QApplication, QTabWidget  # noqa: E402

from dota2coach.config import load_config  # noqa: E402
from dota2coach.ui import theme  # noqa: E402
from dota2coach.ui.panel import SettingsDialog  # noqa: E402


def main() -> int:
    lang = sys.argv[1] if len(sys.argv) > 1 else "en"
    tab = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    out = Path(sys.argv[3] if len(sys.argv) > 3 else "logs/screenshots/set-lang.png")
    app = QApplication.instance() or QApplication([])
    cfg = load_config()
    cfg.app.language = lang
    dlg = SettingsDialog(cfg)
    dlg.setStyleSheet(theme.STYLE)
    tabs = dlg.findChild(QTabWidget)
    if tabs is not None:
        tabs.setCurrentIndex(tab)
    dlg.resize(560, 470)
    dlg.show()
    for _ in range(3):
        app.processEvents()
    out.parent.mkdir(parents=True, exist_ok=True)
    dlg.grab().save(str(out))
    print("saved", out, dlg.width(), dlg.height())
    dlg.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

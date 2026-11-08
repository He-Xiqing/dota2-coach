"""离屏渲染主窗口，验证语言切换即时生效。"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", r"C:\Windows\Fonts")

from PyQt6.QtWidgets import QApplication  # noqa: E402

from dota2coach.config import load_config  # noqa: E402
from dota2coach.ui.panel import CoachPanel  # noqa: E402


class StubApp:
    def __init__(self, config):
        self.config = config

    def status(self):
        return {
            "running": True,
            "in_match": False,
            "known": 10,
            "clock": 0,
            "phase": "对线期",
            "hero": "",
            "allies": [],
            "enemies": [],
            "mode": "MENU",
        }

    def start(self):
        return True

    def stop(self):
        pass

    def apply_settings(self, cfg):
        return []


def main() -> int:
    config = load_config()
    app = QApplication(sys.argv)
    panel = CoachPanel(StubApp(config), config)
    panel.timer.stop()
    panel.resize(1460, 860)
    panel.show()
    app.processEvents()
    panel.grab().save("logs/screenshots/panel-retrans-zh.png")

    config.app.language = "en"
    panel._retranslate_ui()
    app.processEvents()
    panel.grab().save("logs/screenshots/panel-retrans-en.png")
    panel.stack.setCurrentIndex(0)
    app.processEvents()
    panel.grab().save("logs/screenshots/panel-retrans-en-idle.png")
    panel.stack.setCurrentIndex(1)

    config.app.language = "ru"
    panel._retranslate_ui()
    app.processEvents()
    panel.grab().save("logs/screenshots/panel-retrans-ru.png")

    config.app.language = "zh-CN"
    panel._retranslate_ui()
    panel.stack.setCurrentIndex(0)
    app.processEvents()
    panel.grab().save("logs/screenshots/panel-retrans-zh-back.png")
    print("saved retranslate screenshots")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""离屏渲染赛后小结卡片（验证辅助英雄不再提示补刀）。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", r"C:\Windows\Fonts")

from PyQt6.QtWidgets import QApplication  # noqa: E402

from dota2coach.coach.summary import (
    MatchSummary,
    encourage,
    improvements,
    summary_lines,
)  # noqa: E402
from dota2coach.coach.texts import set_language  # noqa: E402
from dota2coach.ui.overlay import OverlayWindow  # noqa: E402


def main() -> int:
    set_language("zh-CN")
    app = QApplication(sys.argv)
    card = OverlayWindow()
    cases = {
        "summary-support": MatchSummary(
            "水晶室女", 3, 9, 15, 42, 2, 900, 310, 2280, False, True
        ),
        "summary-core": MatchSummary(
            "影魔", 4, 1, 5, 88, 6, 812, 250, 1800, False, False
        ),
    }
    out = Path("logs/screenshots")
    out.mkdir(parents=True, exist_ok=True)
    for name, summary in cases.items():
        title = f"上一局 · {summary.result}"
        hint = encourage(summary, bool(improvements(summary)))
        card.render_message(title, summary_lines(summary), hint)
        app.processEvents()
        path = out / f"{name}.png"
        card.grab().save(str(path))
        print("saved", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

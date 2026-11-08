"""英雄强势期：来自 OpenDota 的按对局时长分桶胜率。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ..coach.texts_why import note as note_text


@dataclass(frozen=True)
class HeroTiming:
    hero_id: int
    early: float
    mid: float
    late: float
    label: str
    games: int

    @property
    def note(self) -> str:
        return note_text(self.label)


def load_hero_timing(path: Path) -> dict[int, HeroTiming]:
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    timing: dict[int, HeroTiming] = {}
    for key, item in raw.items():
        try:
            timing[int(key)] = HeroTiming(
                hero_id=int(key),
                early=float(item.get("early", 0.0)),
                mid=float(item.get("mid", 0.0)),
                late=float(item.get("late", 0.0)),
                label=str(item.get("label", "")),
                games=int(item.get("games", 0)),
            )
        except (TypeError, ValueError):
            continue
    return timing

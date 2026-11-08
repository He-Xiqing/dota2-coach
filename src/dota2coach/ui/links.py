"""界面里用到的外部/本地链接。"""

from __future__ import annotations

from pathlib import Path

OFFICIAL_HEROES_URL = "https://www.dota2.com/heroes"
OFFICIAL_HERO_PATTERN = "https://www.dota2.com/hero/{short}"

INGAME_GUIDE_FILE = "ingame_guide.html"


def official_guide_url(hero_short: str | None) -> str:
    """官方攻略：有当前英雄就打开该英雄页，否则打开英雄列表。"""
    short = (hero_short or "").strip()
    if short and all(ch.isalnum() or ch == "_" for ch in short):
        return OFFICIAL_HERO_PATTERN.format(short=short)
    return OFFICIAL_HEROES_URL


def ingame_guide_path(data_dir: Path | str) -> Path:
    """游戏内“出装顺序/攻略”用法说明（随 data 目录一起分发）。"""
    return Path(data_dir) / INGAME_GUIDE_FILE

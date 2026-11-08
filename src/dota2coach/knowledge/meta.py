"""英雄元数据：角色（Carry/Nuker/Disabler/…）与各分段胜率。

数据来源是 OpenDota 的 heroStats（当前版本持续累积的公开对局），
由 `scripts/fetch_hero_stats.py` 生成为 `data/hero_meta.json`。
没有这个文件时上层会退回静态规则表，所以离线也能用。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class HeroMeta:
    hero_id: int
    name: str
    roles: tuple[str, ...]
    pub_winrate: float = 0.0
    high_winrate: float = 0.0
    pro_winrate: float = 0.0
    pro_picks: int = 0


def load_hero_meta(path: Path) -> dict[int, HeroMeta]:
    """读取 hero_meta.json；文件缺失或损坏时返回空表。"""
    try:
        if not path.exists():
            return {}
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    rows = raw.get("heroes") if isinstance(raw, dict) else None
    if not isinstance(rows, dict):
        rows = raw if isinstance(raw, dict) else {}

    meta: dict[int, HeroMeta] = {}
    for key, row in rows.items():
        if not isinstance(row, dict):
            continue
        try:
            hero_id = int(key)
        except (TypeError, ValueError):
            continue
        roles = tuple(str(role) for role in row.get("roles") or [])
        meta[hero_id] = HeroMeta(
            hero_id=hero_id,
            name=str(row.get("name") or row.get("localized_name") or ""),
            roles=roles,
            pub_winrate=float(row.get("pub_winrate") or 0.0),
            high_winrate=float(row.get("high_winrate") or 0.0),
            pro_winrate=float(row.get("pro_winrate") or 0.0),
            pro_picks=int(row.get("pro_picks") or 0),
        )
    return meta

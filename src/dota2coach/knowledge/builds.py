"""从 OpenDota 的出装热度里挑下一件装备。

data/popularity.json 由 scripts/fetch_popularity.py 生成，物品键是 **数字 id**：
    {"38": {"mid_game_items": {"22": 106, ...}, ...}}
data/items.json 由 scripts/build_item_table.py 生成，提供 id -> 物品信息。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

# 这些是消耗品/眼，不适合当作"下一件大件"推荐
CONSUMABLES = {
    "item_tango",
    "item_flask",
    "item_clarity",
    "item_enchanted_mango",
    "item_faerie_fire",
    "item_branches",
    "item_ward_observer",
    "item_ward_sentry",
    "item_smoke_of_deceit",
    "item_dust",
    "item_tpscroll",
    "item_magic_stick",
}


@dataclass(frozen=True)
class ItemInfo:
    name: str
    dname: str
    created: bool
    cost: int


def load_popularity(path: Path) -> dict[int, dict[str, dict[int, int]]]:
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    table: dict[int, dict[str, dict[int, int]]] = {}
    for key, value in raw.items():
        try:
            hero_id = int(key)
        except (TypeError, ValueError):
            continue
        if not isinstance(value, dict):
            continue
        phases: dict[str, dict[int, int]] = {}
        for phase, items in value.items():
            if not isinstance(items, dict):
                continue
            try:
                phases[phase] = {int(item_id): int(count) for item_id, count in items.items()}
            except (TypeError, ValueError):
                continue
        table[hero_id] = phases
    return table


def load_item_table(path: Path) -> tuple[dict[int, ItemInfo], dict[str, str]]:
    """返回 (id -> ItemInfo, 内部名 -> 显示名)。"""
    if not path.exists():
        return {}, {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}, {}
    by_id: dict[int, ItemInfo] = {}
    by_name: dict[str, str] = {}
    for item_id, entry in (raw.get("by_id") or {}).items():
        if not isinstance(entry, dict):
            continue
        try:
            key = int(item_id)
        except (TypeError, ValueError):
            continue
        name = str(entry.get("name", ""))
        if name and not name.startswith("item_"):
            name = f"item_{name}"  # constants/items 里是 "blink"，游戏里是 "item_blink"
        dname = str(entry.get("dname", "") or name.removeprefix("item_").replace("_", " "))
        info = ItemInfo(
            name=name,
            dname=dname,
            created=bool(entry.get("created", False)),
            cost=int(entry.get("cost") or 0),
        )
        by_id[key] = info
        if name:
            by_name[name] = dname
    return by_id, by_name


def display_name(internal: str, names: dict[str, str]) -> str:
    for key in (internal, f"item_{internal}"):
        if key in names:
            return names[key]
    return internal.removeprefix("item_").replace("_", " ")


def _ranked(hero: dict[str, dict[int, int]], phase: str) -> list[int]:
    items = hero.get(phase, {})
    return [item_id for item_id, _ in sorted(items.items(), key=lambda kv: kv[1], reverse=True)]


def _usable(
    item_id: int,
    by_id: dict[int, ItemInfo],
    owned: set[str],
    chosen: list[str],
) -> str | None:
    info = by_id.get(item_id)
    if info is None:
        return None
    # OpenDota 的 created 表示"由散件合成"；闪烁匕首这类整件购买的建议保留，
    # 便宜的散件（Blade of Alacrity 等）直接跳过。
    if not info.created and info.cost < 2000:
        return None
    if info.name in owned or info.name in CONSUMABLES or info.name in chosen:
        return None
    return info.name


def suggest_items(
    popularity: dict[int, dict[str, dict[int, int]]],
    hero_id: int,
    owned: set[str],
    by_id: dict[int, ItemInfo],
    limit: int = 3,
) -> list[str]:
    """按 mid_game 热度给"下一件/下两件"，跳过已拥有、消耗品和散件。"""
    hero = popularity.get(hero_id)
    if not hero:
        return []
    result: list[str] = []
    for item_id in _ranked(hero, "mid_game_items") + _ranked(hero, "late_game_items"):
        name = _usable(item_id, by_id, owned, result)
        if name:
            result.append(name)
            if len(result) >= limit:
                break
    return result


def core_build(
    popularity: dict[int, dict[str, dict[int, int]]],
    hero_id: int,
    by_id: dict[int, ItemInfo],
    limit: int = 6,
) -> list[str]:
    """六格目标出装（不含消耗品与散件）。"""
    return suggest_items(popularity, hero_id, set(), by_id, limit=limit)

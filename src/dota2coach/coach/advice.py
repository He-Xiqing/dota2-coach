"""阵容建议：只根据"已经识别到的敌方英雄"给保守、可执行的提示。

原则：
- 不猜敌方分路、不猜经济差，只做"阵容特征 → 出门装/第一件防具"的匹配；
- 每条提示都必须能立刻执行（带粉、先出挑战、别站桩）；
- 识别不全时不输出（宁可不说话，也不误导）。

分类来源分两层：
1. 有 `data/hero_meta.json`（OpenDota 当前版本数据 + 官方角色标签）时，用角色
   Disabler / Nuker / Pusher 判断，版本更新后重跑 `scripts/fetch_hero_stats.py` 即可；
2. 没有该文件时退回下面的静态集合（内置兜底，允许过期，仅保证离线可用）。
   隐身/回复这两类不是 OpenDota 的角色标签，仍然用静态集合（按英雄技能整理）。
"""

from __future__ import annotations

from ..knowledge.meta import HeroMeta
from ..vision.heroes import HeroInfo

# 隐身/绕后/游走类：需要粉、哨兵、真眼（按"技能自带隐身/伪装"整理）
STEALTH = {
    "bounty_hunter",
    "riki",
    "clinkz",
    "weaver",
    "slark",
    "mirana",
    "sand_king",
    "nyx_assassin",
    "treant",
    "templar_assassin",
}

# 回复/治疗：大骨灰、散失
SUSTAIN = {
    "dazzle",
    "oracle",
    "omniknight",
    "witch_doctor",
    "abaddon",
    "treant",
    "undying",
    "io",
    "chen",
    "necrolyte",
}

# 以下三个集合只在没有 hero_meta.json 时兜底使用。
FALLBACK_CC = {
    "lion",
    "shadow_shaman",
    "bane",
    "doom_bringer",
    "legion_commander",
    "axe",
    "warlock",
    "enigma",
    "magnataur",
    "tidehunter",
    "kunkka",
    "sven",
    "pudge",
    "beastmaster",
    "spirit_breaker",
    "storm_spirit",
    "batrider",
}
FALLBACK_BURST = {
    "lina",
    "leshrac",
    "zuus",
    "storm_spirit",
    "puck",
    "queenofpain",
    "tinker",
    "skywrath_mage",
    "invoker",
    "necrolyte",
    "death_prophet",
    "timbersaw",
    "outworld_devourer",
}
FALLBACK_PUSH = {
    "pugna",
    "death_prophet",
    "furion",
    "beastmaster",
    "lycan",
    "enchantress",
    "chen",
    "terrorblade",
    "leshrac",
    "jakiro",
    "shadow_shaman",
    "arc_warden",
}


def _shorts(enemies: list[HeroInfo]) -> set[str]:
    return {hero.short for hero in enemies if hero is not None}


def has_role(
    hero: HeroInfo,
    meta: dict[int, HeroMeta] | None,
    role: str,
    fallback: set[str],
) -> bool:
    """优先用 OpenDota 的角色标签，缺数据时退回静态集合。"""
    info = meta.get(hero.hero_id) if meta else None
    if info is not None and info.roles:
        return role in info.roles
    return hero.short in fallback


def lineup_tips(
    enemies: list[HeroInfo],
    limit: int = 2,
    meta: dict[int, HeroMeta] | None = None,
) -> list[str]:
    """按敌方阵容给 1-2 条能立刻执行的建议。"""
    if not enemies:
        return []
    shorts = _shorts(enemies)
    tips: list[str] = []
    if shorts & STEALTH:
        tips.append("对面有隐身/游走：出门带粉，河道和野区补哨兵")

    disablers = sum(1 for hero in enemies if has_role(hero, meta, "Disabler", FALLBACK_CC))
    if disablers >= 2:
        tips.append("对面控制多：早出 BKB/分身，别站桩输出")
    elif disablers == 1:
        tips.append("对面有点控：留意先手，站位别贴脸")

    nukers = sum(1 for hero in enemies if has_role(hero, meta, "Nuker", FALLBACK_BURST))
    if nukers >= 2:
        tips.append("法系爆发高：先做挑战/笛子，血量别低于 60%")

    if shorts & SUSTAIN:
        tips.append("对面回复强：出大骨灰/散失，别打持久消耗")

    pushers = sum(1 for hero in enemies if has_role(hero, meta, "Pusher", FALLBACK_PUSH))
    if pushers >= 2:
        tips.append("对面推进强：先清线再打，别在塔下硬刚")
    return tips[:limit]


def lane_hint(xpos: float | None, ypos: float | None) -> str | None:
    """从自己的坐标粗略判断在哪条线（只用于对线期提示，不追求精确）。"""
    if xpos is None or ypos is None:
        return None
    if abs(ypos) <= 1500:
        return "你在中路"
    if ypos > 0:
        return "你在上路（天辉劣势路 / 夜魇优势路）"
    return "你在下路（天辉优势路 / 夜魇劣势路）"

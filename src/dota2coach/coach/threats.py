"""敌方阵容的威胁标签（先手 / 爆发 / 隐身）。

只用于主窗口的“一眼看懂”标记，规则保守：
- 先手：OpenDota 角色里有 Initiator 或 Disabler；
- 爆发：角色里有 Nuker；
- 隐身：常见隐身英雄名单（数据里没有“隐身”这个角色）。
"""

from __future__ import annotations

from ..knowledge.meta import HeroMeta
from ..vision.heroes import HeroInfo
from .advice import STEALTH

#: 展示顺序，也决定徽章配色
LABELS = ("先手", "爆发", "隐身")


def threat_labels(hero: HeroInfo | None, meta: dict[int, HeroMeta] | None) -> list[str]:
    """返回该英雄的威胁标签（最多 3 个，顺序固定）。"""
    if hero is None:
        return []
    roles: set[str] = set()
    info = (meta or {}).get(hero.hero_id)
    if info is not None:
        roles = set(info.roles)
    labels: list[str] = []
    if "Initiator" in roles or "Disabler" in roles:
        labels.append("先手")
    if "Nuker" in roles:
        labels.append("爆发")
    if hero.short in STEALTH:
        labels.append("隐身")
    return labels


def threat_summary(enemies: list[HeroInfo], meta: dict[int, HeroMeta] | None) -> dict[str, int]:
    """整队威胁计数，例如 {"先手": 2, "爆发": 3, "隐身": 1}。"""
    counts = {label: 0 for label in LABELS}
    for hero in enemies:
        for label in threat_labels(hero, meta):
            counts[label] += 1
    return counts

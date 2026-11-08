"""对线教练（M3）：前 10 分钟给"能马上做"的对线提示。

数据来源与边界：
- 自己走哪条线：GSI 只给自己的坐标，按 y 轴粗判（不追求精确）；
- 敌方阵容：决策时间面板识别（`Roster`），识别不全时只给与阵容无关的提示；
- 敌方分路：GSI 和截屏都拿不到可靠数据，所以**不猜"你对线的是谁"**，只按
  "敌方整体威胁类型"给站位/血线建议，并点名最有威胁的英雄；
- 威胁分类优先用 OpenDota 角色标签（`data/hero_meta.json`），缺数据时退回
  静态集合；隐身类不是角色标签，仍用静态集合。

提示都带稳定 key，由调用方去重，保证同一局不重复刷屏。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from ..knowledge.meta import HeroMeta
from ..knowledge.timing import HeroTiming
from ..vision.heroes import HeroInfo
from .advice import (
    STEALTH,
    has_role,
)
from .lane_style import plan_for
from .texts import t, join_names

LANING_END = 10 * 60.0


@dataclass(frozen=True)
class LaneTip:
    key: str
    text: str
    urgent: bool = False


def _names(heroes: Sequence[HeroInfo | None], limit: int = 2) -> str:
    labels = [hero.name_loc for hero in heroes if hero is not None][:limit]
    return "、".join(labels)


def _with_role(
    enemies: Sequence[HeroInfo | None],
    meta: dict[int, HeroMeta] | None,
    role: str,
    fallback: set[str],
) -> list[HeroInfo]:
    return [hero for hero in enemies if hero is not None and has_role(hero, meta, role, fallback)]


def lane_tips(
    *,
    lane: str,
    clock: float,
    enemies: Sequence[HeroInfo | None] = (),
    meta: dict[int, HeroMeta] | None = None,
    health_percent: float | None = None,
    mana_percent: float | None = None,
    last_hits: int | None = None,
    level: int | None = None,
    lane_enemies: Sequence[HeroInfo | None] | None = None,
    timing: dict[int, HeroTiming] | None = None,
    matchup_winrate: float | None = None,
    faction: str | None = None,
    self_hero: HeroInfo | None = None,
    guide_tips: object = (),
    limit: int = 2,
) -> list[LaneTip]:
    """返回 0..limit 条对线期提示（按优先级排序）。

    `lane_enemies` 只有在能确认同路敌人时才传（当前 GSI 拿不到敌方坐标）；
    传了就会按英雄强势期给“这局对线怎么打”，没传就退回整体阵容判断。
    """
    if not (0 <= clock <= LANING_END):
        return []

    tips: list[LaneTip] = []
    minute = int(clock // 60)

    # 1) 血量/蓝量：最紧急，按分钟去重（每分钟最多提醒一次）
    if health_percent is not None and health_percent < 0.35:
        tips.append(
            LaneTip(f"lane:hp:{minute}", t("hint_hp"), urgent=True)
        )
    elif mana_percent is not None and mana_percent < 0.15:
        tips.append(LaneTip(f"lane:mana:{minute}", t("hint_mana")))

    # 2) 开局站位 / 到 6 级（按自己英雄的打法走，见 lane_style.py）
    plan = plan_for(self_hero, meta, timing, guide_tips=guide_tips)
    if 20 <= clock < 120:
        tips.append(LaneTip("lane:plan:early", plan.early))
    elif 120 <= clock < 300:
        tips.append(LaneTip("lane:plan:mid", plan.mid))
    if level is not None and level >= 6 and clock < 600:
        tips.append(LaneTip("lane:six", t("hint_level6")))

    # 3) 眼位与夜晚：机制固定，不依赖阵容
    if 240 <= clock < 300:
        tips.append(LaneTip("lane:ward", t("hint_ward")))
    if 300 <= clock < 360:
        tips.append(LaneTip("lane:night", t("hint_night")))

    # 4) 阵容级威胁（先手多/推线强/爆发高）与是否同路无关，已按用户要求全部关闭；
    #    只保留“隐身”，因为它直接决定出门要不要带粉。
    if enemies and 60 <= clock < 420:
        stealth = [hero for hero in enemies if hero is not None and hero.short in STEALTH]
        if stealth:
            tips.append(
                LaneTip(
                    "lane:threat:stealth",
                    t("hint_stealth", names=_names(stealth)),
                )
            )

    # 4) 同路对位（能确认时）：按英雄强势期 + 历史对位胜率给打法
    if lane_enemies and 30 <= clock < 600:
        known = [hero for hero in lane_enemies if hero is not None][:2]
        if known:
            labels = join_names(hero.name_loc for hero in known)
            tips.append(LaneTip(f"lane:opp:{labels}", t("hint_opp", names=labels)))
            timing = timing or {}
            for hero in known:
                info = timing.get(hero.hero_id)
                if info is None or info.games < 500:
                    continue
                tips.append(
                    LaneTip(f"lane:opp:{hero.short}:{info.label}", f"{hero.name_loc}: {info.note}")
                )
            if matchup_winrate is not None and matchup_winrate < 0.48:
                tips.append(
                    LaneTip(
                        f"lane:opp:wr:{int(matchup_winrate * 100)}",
                        t("hint_opp_hard", rate=f"{matchup_winrate:.0%}"),
                    )
                )

    # 4b) 拿不到同路敌人时，退一步：对面后期英雄多，提醒对线期要压
    if not lane_enemies and enemies and timing and 60 <= clock < 420:
        late = [
            hero
            for hero in enemies
            if hero is not None and (timing.get(hero.hero_id) or None) and timing[hero.hero_id].label == "后期"
        ]
        if len(late) >= 2:
            tips.append(
                LaneTip(
                    "lane:late",
                    t("hint_late", names=_names(late)),
                )
            )

    # 4c) 拿不到同路敌人时，按分路常识猜一个“可能对位”（明确标“可能”）
    lane_key = "上" if "上路" in lane else ("下" if "下路" in lane else "")
    if not lane_enemies and enemies and meta and faction and lane_key and 30 <= clock < 600:
        safe = (lane_key == "下") if faction == "radiant" else (lane_key == "上")
        picks = _with_role(enemies, meta, "Carry", set()) if not safe else (
            _with_role(enemies, meta, "Durable", set()) or _with_role(enemies, meta, "Initiator", set())
        )
        picks = [hero for hero in picks if hero is not None][:2]
        if picks:
            labels = join_names(hero.name_loc for hero in picks)
            side = "优势路核心" if not safe else "劣势路先手"
            tips.append(
                LaneTip(
                    f"lane:guess:{labels}",
                    t("possible_opp", names=labels, side=t("possible_side_safe" if not safe else "possible_side_off")),
                )
            )
            timing = timing or {}
            for hero in picks:
                info = timing.get(hero.hero_id)
                if info is None or info.games < 500 or info.label not in ("前期", "后期"):
                    continue
                tips.append(
                    LaneTip(f"lane:guess:{hero.short}:{info.label}", f"{hero.name_loc}: {info.note}")
                )

    # 5) 补刀：只提醒“核心”玩家（辅助补刀少是正常的）
    if last_hits is not None and 180 <= clock < 600 and last_hits < 18:
        is_core = True
        if self_hero is not None and meta:
            info = meta.get(self_hero.hero_id)
            if info is not None:
                is_core = "Support" not in set(info.roles)
        if is_core:
            tips.append(LaneTip("lane:cs", t("hint_cs")))

    # 去重（同 key 只留第一条）并按优先级截断
    seen: set[str] = set()
    unique: list[LaneTip] = []
    for tip in tips:
        if tip.key in seen:
            continue
        seen.add(tip.key)
        unique.append(tip)

    def _rank(tip: LaneTip) -> int:
        if tip.key.startswith(("lane:hp", "lane:mana")):
            return 0
        if tip.key.startswith("lane:guess"):
            return 1
        return 2

    unique.sort(key=_rank)
    return unique[:limit]

"""团战与地图意识（M5）。

数据边界：
- GSI 不给敌方坐标，小地图也不认得出“红点是谁”，所以这里只做
  「数量/聚集/靠近」级别的判断，不做“谁在哪里”。
- 目标优先级（先打谁 / 绕开谁 / 小心谁的技能）用敌方阵容 + OpenDota 角色标签
  在开团时给一次，属于“阵容常识”，不是实时位置判断。
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from .texts import language
from .texts_fight import ftext

from ..vision.minimap import MinimapDots, Point, cluster_count, nearest_distance

FIGHT_START_MIN = 20 * 60  # 20 分钟后才开小地图提醒

_SKILLS = {
    "lion": "穿刺/妖术",
    "axe": "狂战士之吼",
    "sven": "风暴之锤",
    "tidehunter": "毁灭",
    "enigma": "黑洞",
    "warlock": "混乱之祭",
    "shadow_shaman": "枷锁",
    "doom_bringer": "末日",
    "batrider": "燃烧枷锁",
    "legion_commander": "决斗",
    "pudge": "肉钩",
    "skywrath_mage": "震荡光弹",
    "disruptor": "静态风暴",
    "faceless_void": "时间结界",
    "magnataur": "两极反转",
    "sand_king": "掘地穿刺",
    "earthshaker": "回音击",
    "slardar": "鱼人碎击",
    "centaur": "马蹄践踏",
    "spirit_breaker": "突袭",
    "storm_spirit": "电子涡流",
    "invoker": "连招",
}

_FALLBACK_AVOID = {"axe", "tidehunter", "enigma", "magnataur", "centaur", "slardar", "spirit_breaker"}
_FALLBACK_FOCUS = {"crystal_maiden", "lion", "lina", "zuus", "shadow_shaman", "witch_doctor", "skywrath_mage"}

# 刷钱路线（按阵营），一条一条轮换，避免每局重复
_ROUTES = {
    "radiant": [
        "下路兵线推过去 → 三角区两波野 → 己方远古（别过河）",
        "中路兵线 → 己方大野 → 上路三角（有视野再推）",
        "优势路二塔前兵线 → 野区绕后 → 回城补装",
    ],
    "dire": [
        "上路兵线推过去 → 三角区两波野 → 己方远古（别过河）",
        "中路兵线 → 己方大野 → 下路三角（有视野再推）",
        "优势路二塔前兵线 → 野区绕后 → 回城补装",
    ],
}

_WARDS = {
    "radiant": [
        "河道符点（下河道）插一个，能看到中路游走",
        "己方野区入口插一个，防绕后",
        "优势路一塔后插一个，防越塔",
    ],
    "dire": [
        "河道符点（上河道）插一个，能看到中路游走",
        "己方野区入口插一个，防绕后",
        "优势路一塔后插一个，防越塔",
    ],
}


@dataclass(frozen=True)
class FightHint:
    key: str
    text: str
    urgent: bool = False


@dataclass
class FightTracker:
    """按时间累积小地图统计，做“消失 / 聚集 / 开团”判断。"""

    enemy_history: deque[int] = field(default_factory=lambda: deque(maxlen=30))
    absent_since: float | None = None
    last_missing: float = -999.0
    last_group: float = -999.0
    last_fight: float = -999.0
    last_route: float = -999.0
    last_ward: float = -999.0

    def update(
        self,
        *,
        clock: float,
        dots: MinimapDots,
        roster,
        meta=None,
        roles: set[str] | None = None,
        side: str = "radiant",
        health_percent: float | None = None,
        self_hero=None,
        guide_tips: list[str] | None = None,
    ) -> list[FightHint]:
        if clock < FIGHT_START_MIN:
            return []
        hints: list[FightHint] = []
        enemies = dots.enemies
        allies = dots.allies

        self.enemy_history.append(len(enemies))
        recent_max = max(self.enemy_history)

        # 1) 敌方从视野里“少了人”
        if len(enemies) == 0 and recent_max >= 2:
            if self.absent_since is None:
                self.absent_since = clock
            if clock - self.absent_since >= 3 and clock - self.last_missing >= 60:
                self.last_missing = clock
                hints.append(
                    FightHint(
                        f"fight:missing:{int(clock // 60)}",
                        ftext("missing") or "对面红点全没了：小心开雾抓人，退到有视野的位置或跟队友走",
                        urgent=True,
                    )
                )
        else:
            self.absent_since = None

        # 2) 附近有人而且自己血少
        if dots.self_pos is not None and enemies:
            near = nearest_distance(enemies, dots.self_pos)
            if near <= 0.07 and (health_percent or 100) < 45:
                hints.append(
                    FightHint(
                        f"fight:near:{int(clock // 15)}",
                        ftext("near") or "小地图上有红点贴过来了，血量偏低：先拉走，别在兵线里硬打",
                        urgent=True,
                    )
                )

        # 3) 我方在聚集
        ally_cluster = cluster_count(allies, 0.10)
        if ally_cluster >= 3 and clock - self.last_group >= 90:
            self.last_group = clock
            hints.append(
                FightHint(
                    f"fight:group:{int(clock // 90)}",
                    ftext("group", n=ally_cluster) or f"队友 {ally_cluster} 人在附近集结：可以跟团，先确认大招和 BKB 状态",
                )
            )

        # 4) 团战爆发：红点聚成一团，且离自己/队友不远
        enemy_cluster = cluster_count(enemies, 0.10)
        ally_cluster2 = cluster_count(allies, 0.14)
        if enemy_cluster >= 3 and ally_cluster2 >= 2 and clock - self.last_fight >= 45:
            self.last_fight = clock
            plan = player_plan(self_hero, meta, roster, guide_tips)
            if plan:
                text = (ftext("engage") or "团战打起来了：") + ("; " if ftext("engage") else "；").join(plan)
            else:
                focus, avoid, watch = fight_targets(roster, meta)
                parts = []
                if focus:
                    parts.append(ftext("focus", name=focus) or f"先打 {focus}")
                if avoid:
                    parts.append(ftext("avoid", name=avoid) or f"绕开 {avoid}")
                if watch:
                    parts.append(ftext("watch", name=watch) or f"小心 {watch} 的技能")
                text = ((ftext("engage") or "团战打起来了：") + ("; " if ftext("engage") else "；").join(parts)) if parts else (ftext("fallback") or "团战打起来了：先看队友位置，别第一个上")
            hints.append(FightHint(f"fight:engage:{int(clock // 45)}", text, urgent=True))

        # 5) 没在打团时，按定位给路线/眼位
        if not hints:
            role_set = roles or set()
            if "Carry" in role_set and clock - self.last_route >= 180:
                self.last_route = clock
                routes = _ROUTES.get(side, _ROUTES["radiant"])
                index = int(clock // 180) % len(routes)
                hints.append(FightHint(f"farm:{int(clock // 180)}", ftext("farm_route") or f"刷钱路线：{routes[index]}"))
            elif "Support" in role_set and clock - self.last_ward >= 180:
                self.last_ward = clock
                wards = _WARDS.get(side, _WARDS["radiant"])
                index = int(clock // 180) % len(wards)
                hints.append(FightHint(f"ward:{int(clock // 180)}", ftext("ward_pos") or f"辅助眼位：{wards[index]}"))
        return hints


def fight_targets(roster, meta=None) -> tuple[str, str, str]:
    """按敌方阵容给“先打谁 / 绕开谁 / 小心谁”，返回中文名（可能为空串）。"""
    if roster is None or not getattr(roster, "enemies", None):
        return "", "", ""
    focus: list[str] = []
    avoid: list[str] = []
    watch: list[str] = []
    for hero in roster.enemies:
        if hero is None:
            continue
        info = (meta or {}).get(hero.hero_id)
        roles = set(getattr(info, "roles", ()) if info is not None else ())
        if roles & {"Durable", "Initiator"} or hero.short in _FALLBACK_AVOID:
            avoid.append(hero.name_loc)
        elif roles & {"Support", "Nuker"} or hero.short in _FALLBACK_FOCUS:
            focus.append(hero.name_loc)
        skill = _SKILLS.get(hero.short)
        if skill:
            # 技能昵称表只有中文，非中文只报英雄名，避免中英混排
            if language().startswith("zh"):
                watch.append(f"{hero.name_loc}（{skill}）")
            else:
                watch.append(hero.name_loc)
    return (
        "、".join(focus[:2]),
        "、".join(avoid[:2]),
        "、".join(watch[:2]),
    )


def _role_heroes(heroes, meta, wanted: set[str]) -> list:
    picked = []
    for hero in heroes or ():
        if hero is None:
            continue
        info = (meta or {}).get(hero.hero_id)
        roles = set(getattr(info, "roles", ()) if info is not None else ())
        if roles & wanted:
            picked.append(hero)
    return picked


def _pick(heroes, meta, wanted: set[str]) -> str:
    picked = _role_heroes(heroes, meta, wanted)
    return picked[0].name_loc if picked else ""


def player_plan(self_hero, meta, roster, guide_tips: list[str] | None = None) -> list[str]:
    """按“你自己的英雄标签”给团战该做什么：抗伤 / 盯人 / 甩技能 / 切入 / 保人。"""
    if self_hero is None:
        return []
    info = (meta or {}).get(self_hero.hero_id)
    roles = set(getattr(info, "roles", ()) if info is not None else ())
    enemies = [h for h in (getattr(roster, "enemies", ()) or ()) if h is not None]
    allies = [h for h in (getattr(roster, "allies", ()) or ()) if h is not None]

    squishy = _pick(enemies, meta, {"Support", "Nuker"}) or (enemies[0].name_loc if enemies else "")
    key_target = _pick(enemies, meta, {"Carry", "Nuker"}) or squishy
    ally_carry = _pick(allies, meta, {"Carry"}) or _pick(allies, meta, {"Nuker"})

    lines: list[str] = []
    if roles & {"Durable", "Initiator"}:
        lines.append(ftext("plan_tank") or "你是前排/先手：顶上去吃第一波伤害，别追残血")
    if "Disabler" in roles:
        lines.append(ftext("plan_cc", target=key_target) or f"你是控制：盯住 {key_target}，他一进场就交控")
    if "Nuker" in roles and "Carry" not in roles:
        line = ftext("plan_mage", squishy=squishy) or f"你是法系：技能优先甩给 {squishy}，别空放"
        if ally_carry:
            line += f"；同时护住 {ally_carry}"
        lines.append(line)
    if "Escape" in roles or ("Carry" in roles and "Nuker" not in roles):
        lines.append(ftext("plan_assassin", squishy=squishy) or f"你是刺客/核心：绕后切 {squishy}，打完就撤，别恋战")
    if not lines:
        if "Support" in roles:
            lines.append(ftext("plan_guard", ally=(ally_carry or "core")) or f"你是辅助：保 {ally_carry or '核心'}，先给控制/治疗再考虑输出")
        else:
            lines.append(ftext("plan_group", squishy=(squishy or "the squishiest")) or f"团战先跟队友，优先集火 {squishy or '对面最脆的'}")

    for tip in guide_tips or ():
        if any(word in tip for word in ("团", "切入", "开团")):
            lines.append(f"攻略：{tip}")
            break
    return lines[:2]

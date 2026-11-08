"""不同英雄的对线打法（M3）。

同一句“先补刀到 3 级”对小鱼人这种 1 级就能压的英雄是错的，
所以这里按“英雄自身 + OpenDota 强势期”给分阶段的打法建议：

- harass 压制：1 级就换血，把对面压出经验区
- trade  换血：能换就换，但别越塔
- farm   发育：以补刀为主，少换血
- safe   求稳：宁可漏刀，先保住血线

数据来源：手写表（20+ 常见英雄）+ 角色/强势期兜底。
"""

from __future__ import annotations

from dataclasses import dataclass

from ..knowledge.meta import HeroMeta
from ..knowledge.timing import HeroTiming
from ..vision.heroes import HeroInfo


@dataclass(frozen=True)
class LanePlan:
    style: str
    label: str
    early: str  # 20–120 秒
    mid: str  # 2–5 分钟


_STYLE_LABEL = {
    "harass": "压制",
    "trade": "换血",
    "farm": "发育",
    "safe": "求稳",
}

_STYLE_TIPS = {
    "harass": (
        "1 级就压上去：用技能换血，别让他安稳补刀",
        "抢到 2/3 级那波继续压，血线领先就卡线",
    ),
    "trade": (
        "可以换血：你有续航/控制，别只站后面补刀",
        "注意对面 2 级那波，血线 50% 就退",
    ),
    "farm": (
        "以补刀为主：别为了消耗丢正补",
        "对面压线就拉野把线控回来，5 分钟前别越线",
    ),
    "safe": (
        "稳住血线：宁可漏刀，别在线上硬拼",
        "等 6 级或关键装再找机会",
    ),
}

# 手写：常见英雄的对线打法（short -> (style, early, mid)）
_CURATED: dict[str, tuple[str, str, str]] = {
    "slark": ("harass", "1 级有黑暗契约：贴脸换血，压出经验区", "抢 3 级开雾绕后，别在线上硬拼"),
    "juggernaut": ("harass", "1 级剑刃风暴直接换血，转完就撤", "有治疗守卫就换，血线领先就卡线"),
    "ursa": ("harass", "1 级就压：越兵线换血，别让他补刀", "叠怒后再打一波，注意别越塔"),
    "axe": ("trade", "靠反击螺旋换血：他敢贴就转", "兵线过来就转，别空转"),
    "legion_commander": ("trade", "1 级靠压倒性优势换血", "血量领先就压制，注意魔免"),
    "sniper": ("farm", "保持射程：用散弹消耗，被贴脸就退", "塔下补刀为主，别过河"),
    "drow_ranger": ("farm", "保持距离补刀，别被贴脸", "6 级有大再考虑换血"),
    "anti_mage": ("farm", "专注补刀：别换血，法力损毁没成型", "对面压线就拉野，5 分钟前别越线"),
    "phantom_assassin": ("farm", "补刀为主，别用模糊去换血", "有 2 级模糊再找机会"),
    "medusa": ("safe", "先稳血线：秘术异蛇补刀", "分身斧前别硬拼"),
    "spectre": ("safe", "稳住补刀：别换血", "6 级后看大招找机会"),
    "zeus": ("harass", "1 级雷击换血，压出经验区", "2 级继续压，注意蓝量"),
    "lina": ("harass", "1 级龙破斩消耗，别让他补刀", "抢 2 级打一波"),
    "lion": ("trade", "1 级穿刺找机会，配合队友杀", "蓝量够就换，注意别空蓝"),
    "crystal_maiden": ("trade", "1 级水晶新星换血，别只站后面", "蓝量低就退，别硬撑"),
    "ogre_magi": ("trade", "1 级火焰爆轰换血，血厚敢换", "注意蓝量，别空蓝"),
    "axe": ("trade", "靠反击螺旋换血：他敢贴就转", "兵线过来就转，别空转"),
    "pudge": ("safe", "先稳：钩不到就别上", "6 级前别越线"),
    "invoker": ("farm", "补刀为主，技能留给补刀/消耗", "有 2 级符文再换血"),
    "shadow_fiend": ("harass", "1 级影压消耗，压出经验区", "抢 2 级打一波，注意别被绕后"),
    "templar_assassin": ("harass", "1 级折光换血，压线", "抢 2 级继续压"),
    "earthshaker": ("trade", "1 级沟壑换血+封路", "有魔就找机会"),
    "mars": ("trade", "1 级战神之矛换血", "血线领先就压"),
    "tidehunter": ("safe", "先稳：海妖外壳换血要谨慎", "6 级有大再打"),
    "razor": ("harass", "1 级静电连接换血，压制补刀", "抢 2 级继续压"),
}


def plan_for(
    hero: HeroInfo | None,
    meta: dict[int, HeroMeta] | None = None,
    timing: dict[int, HeroTiming] | None = None,
    guide_tips: list[object] | tuple[object, ...] | None = None,
) -> LanePlan:
    """按英雄给出对线打法；优先级：攻略库 → 手写表 → 角色/强势期兜底。"""
    if hero is None:
        return LanePlan("farm", _STYLE_LABEL["farm"], *_STYLE_TIPS["farm"])

    from_guides = plan_from_guides(hero.short, guide_tips or ())
    if from_guides is not None:
        return from_guides

    curated = _CURATED.get(hero.short)
    if curated is not None:
        style, early, mid = curated
        return LanePlan(style, _STYLE_LABEL[style], early, mid)

    roles: set[str] = set()
    if meta is not None:
        info = meta.get(hero.hero_id)
        if info is not None:
            roles = set(info.roles)
    label = ""
    if timing is not None:
        t = timing.get(hero.hero_id)
        if t is not None:
            label = t.label

    if "Nuker" in roles and roles & {"Escape", "Carry"} and label == "前期":
        style = "harass"
    elif "Durable" in roles or "Initiator" in roles:
        style = "trade"
    elif "Carry" in roles:
        style = "trade" if label == "前期" else "farm"
    else:
        style = "farm"

    early, mid = _STYLE_TIPS[style]
    return LanePlan(style, _STYLE_LABEL[style], early, mid)


# 从 B 站攻略文本里归纳打法：压线/换血 → 压制，补刀/拉野 → 发育，稳/退 → 求稳
_GUIDE_KEYWORDS = {
    "harass": ("压线", "压出", "换血", "消耗", "越线", "抢二", "抢2", "强势", "贴脸", "骚扰"),
    "farm": ("补刀", "发育", "拉野", "控线", "补兵", "刷钱", "别换血", "稳补"),
    "safe": ("别送", "苟", "稳住", "猥琐", "别硬拼", "退一步"),
    "trade": ("对拼", "打一波", "拼血", "敢于"),
}


def _clip(text: str, limit: int = 26) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def plan_from_guides(hero_short: str, tips: object) -> LanePlan | None:
    """从攻略库的文本里归纳该英雄的打法；证据不足返回 None。"""
    scores = {style: 0 for style in _STYLE_TIPS}
    best: dict[str, str] = {}
    for tip in tips or ():
        hero = str(getattr(tip, "hero", "") or "")
        if hero and hero not in (hero_short, "任意"):
            continue
        text = str(getattr(tip, "text", "") or "")
        if not text:
            continue
        for style, keywords in _GUIDE_KEYWORDS.items():
            hits = sum(1 for keyword in keywords if keyword in text)
            if hits:
                scores[style] += hits
                best.setdefault(style, text)

    style = max(scores, key=lambda name: scores[name])
    if scores[style] < 2:
        return None

    early, mid = _STYLE_TIPS[style]
    sample = best.get(style)
    if sample:
        early = _clip(sample)
    return LanePlan(style, _STYLE_LABEL[style] + "（攻略）", early, mid)

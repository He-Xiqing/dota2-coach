"""推荐装备：给出“为什么出”和“怎么用”，而不是只报一件装备名。

数据来源分两层：
- 出什么：OpenDota 的 itemPopularity（data/popularity.json，按英雄、分阶段热度），
  只在该英雄的主流出装里挑，避免推荐他不会做的装备；
- 为什么：对手阵容的威胁（沉默/强控/法系爆发/高回复/物理核心/高机动），
  用英雄中文名点出来，例如“对面有沉默（天怒法师、死亡先知）”；
- 怎么用：每件装备一句操作说明（下方 `_HOW`），写的是开团时机和注意事项。

这里不猜测具体技能等级/装备情况，只根据“阵容里有没有这类英雄”给保守建议。
"""

from __future__ import annotations

from dataclasses import dataclass

from ..knowledge.builds import ItemInfo, display_name
from .texts import join_names, language as ui_language
from .texts_how import how_en
from .texts_why import why as why_text
from ..knowledge.meta import HeroMeta
from ..vision.heroes import HeroInfo
from .traits import has_self_dispel

# 每件装备的用法说明（键是物品内部名，带 item_ 前缀）
_HOW: dict[str, str] = {
    "item_manta": "被沉默/先手时开，驱散并召分身；分身可带线/开视野",
    "item_black_king_bar": "开团前或吃控瞬间开；对面物理输出/刃甲时别硬顶，10 秒内打出收益",
    "item_pipe": "团战前给队友罩上抵法系爆发；CD 很长，等对面先手技能交了再开",
    "item_crimson_guard": "对面物理核心成型后开，减免普攻与物理技能；配合站位，别单吃",
    "item_spirit_vessel": "盯对面高回复目标（死灵法/神灵/戴泽），在他开治疗前挂上；也能救人",
    "item_lotus_orb": "被单点控制/沉默时给自己或队友套，能反弹指向性技能",
    "item_sheepstick": "先手秒关键目标；也可留作反手，羊住冲脸的核心",
    "item_orchid": "先手沉默对面核心阻止逃生/反打；5 秒打不死就撤",
    "item_ghost": "对面物理爆发高时开，物理免疫并降速；别在魔法爆发下开",
    "item_shivas_guard": "对面吸血/攻速/回复多时开，减治疗与攻速",
    "item_assault": "团战前给己方物理核心叠甲/攻速",
    "item_heavens_halberd": "对物理核心缴械 5 秒；也能给自己加闪避",
    "item_solar_crest": "救人或给己方核心加攻速/护甲",
    "item_glimmer_cape": "被物理追时套自己/队友，隐身+魔法抗性",
    "item_force_staff": "被近身时推自己/队友脱身，或把敌人推进己方阵型",
    "item_cyclone": "吹起对面关键目标或救队友，能打断持续施法",
    "item_aeon_disk": "被先手秒时自动触发，每 90 秒一次，别当常规保命",
    "item_skadi": "对面吸血/治疗多时出，减速+减治疗",
    "item_diffusal_blade": "对面有法力护盾/高蓝英雄时用，可驱散增益",
    "item_satanic": "被集火时开吸血脱战，注意别在控制链里开",
    "item_hurricane_pike": "被近身时推开敌人拉开距离，配合远程核心",
    "item_mask_of_madness": "刷钱/单挑时开；8 秒内攻速拉满，别在会被控时开",
    "item_aghanims_scepter": "大招质变件；有质变效果就尽早出，没质变别硬买",
    "item_aghanims_shard": "20 分钟后野店买，补强一个技能，性价比高",
    "item_sange_and_yasha": "双刀加移速/状态抗性，适合贴身拉扯、怕减速的英雄",
    "item_mjollnir": "对面分身/召唤物多时出，连锁闪电清场",
    "item_dragon_lance": "远程核心撑射程/血量，先手前多一段安全距离",
}

# 静态英雄集合（版本更新时在这里改；角色标签来自 OpenDota 的 heroStats）
_SILENCE = {
    "silencer",
    "death_prophet",
    "skywrath_mage",
    "night_stalker",
    "riki",
    "drow_ranger",
    "bloodseeker",
    "disruptor",
}
_HEAL = {"necrolyte", "dazzle", "huskar", "oracle", "io", "warlock"}
_ESCAPE = {"anti_mage", "storm_spirit", "queenofpain", "ember_spirit", "void_spirit", "morphling"}
_INVIS = {"riki", "bounty_hunter", "clinkz", "templar_assassin", "sand_king", "nyx_assassin"}

# 纯属性散件（价格 >=2000 也不能当"下一件"推荐）
_COMPONENTS = {
    "item_ultimate_orb",
    "item_blade_of_alacrity",
    "item_ogre_axe",
    "item_staff_of_wizardry",
    "item_void_stone",
    "item_energy_booster",
    "item_point_booster",
    "item_vitality_booster",
    "item_hyperstone",
    "item_demon_edge",
    "item_eaglesong",
    "item_reaver",
    "item_mystic_staff",
    "item_ring_of_health",
    "item_ring_of_regen",
    "item_sobi_mask",
    "item_boots_of_elvenskin",
    "item_belt_of_strength",
    "item_robe",
    "item_circlet",
    "item_slippers",
    "item_gauntlets",
    "item_mantle",
    "item_quelling_blade",
    "item_blight_stone",
    "item_orb_of_venom",
    "item_cloak",
    "item_chainmail",
    "item_platemail",
    "item_ring_of_protection",
    "item_ring_of_basilius",
    "item_headdress",
    "item_buckler",
    "item_talisman_of_evasion",
    "item_shadow_amulet",
    "item_gloves",
    "item_boots",
    "item_blades_of_attack",
}


@dataclass(frozen=True)
class ItemAdvice:
    name: str  # 内部名，例如 item_manta
    display: str  # 中文名，例如 幻影斧
    why: str
    how: str
    threat: str | None = None


@dataclass(frozen=True)
class _Threat:
    tag: str
    items: tuple[str, ...]
    reason: str


def _enemy_names(enemies: list[HeroInfo | None]) -> list[HeroInfo]:
    return [hero for hero in enemies if hero is not None]


def _has_role(heroes: list[HeroInfo], meta: dict[int, HeroMeta], role: str, fallback: set[str]) -> list[HeroInfo]:
    found: list[HeroInfo] = []
    for hero in heroes:
        info = meta.get(hero.hero_id)
        roles = set(info.roles) if info is not None else set()
        if role in roles or hero.short in fallback:
            found.append(hero)
    return found


def _pick(items: tuple[str, ...], by_id: dict[int, ItemInfo], owned: set[str]) -> str | None:
    """克制装不受英雄热度限制：对面有沉默就值得出分身/黑皇，哪怕不在热度前 12。"""
    known = {info.name for info in by_id.values()}
    for item in items:
        if item in known and item not in owned:
            return item
    return None


def _usable(popularity: dict, hero_id: int, by_id: dict[int, ItemInfo]) -> list[str]:
    """该英雄热度最高的整件（不含消耗品、散件），按 mid+late 顺序。"""
    hero = popularity.get(hero_id) or {}
    ordered: list[int] = []
    for phase in ("mid_game_items", "late_game_items"):
        for item_id, _ in sorted((hero.get(phase) or {}).items(), key=lambda kv: kv[1], reverse=True):
            ordered.append(item_id)
    names: list[str] = []
    for item_id in ordered:
        info = by_id.get(item_id)
        if info is None:
            continue
        if not info.created and (info.cost < 2000 or info.name in _COMPONENTS):
            continue
        if info.name in ("item_tango", "item_flask", "item_clarity", "item_ward_observer", "item_ward_sentry"):
            continue
        if info.name not in names:
            names.append(info.name)
    return names


def _how_text(item: str, fallback_zh: str) -> str:
    if ui_language() == "zh-CN":
        return _HOW.get(item, fallback_zh)
    return how_en(item)


def recommend(
    *,
    hero: HeroInfo | None,
    enemies: list[HeroInfo | None],
    popularity: dict,
    by_id: dict[int, ItemInfo],
    item_names: dict[str, str],
    meta: dict[int, HeroMeta] | None = None,
    owned: set[str] | None = None,
    limit: int = 2,
    guide_items: tuple[str, ...] = (),
) -> list[ItemAdvice]:
    """按“对手威胁 → 本英雄主流出装”给 1–2 件推荐，每件带理由与用法。"""
    if hero is None:
        return []
    owned = owned or set()

    # B 站攻略里的出装优先：按攻略顺序，跳过已拥有的
    if guide_items:
        by_display = {dname: name for name, dname in item_names.items() if dname}
        for dname in guide_items:
            item = by_display.get(dname)
            if item is None or item in owned:
                continue
            return [
                ItemAdvice(
                    name=item,
                    display=dname,
                    why=why_text("mainstream", hero=hero.name_loc) if ui_language() != "zh-CN" else f"B 站 {hero.name_loc} 攻略推荐",
                    how=_how_text(item, "按攻略在关键节点出"),
                )
            ]

    if not popularity:
        return []
    available = _usable(popularity, hero.hero_id, by_id)
    if not available:
        return []
    pool = _enemy_names(enemies)
    if not pool:
        # 敌方未识别：只按本英雄主流出装给，不编“针对”
        picks = [name for name in available if name in _HOW][:limit]
        return [
            ItemAdvice(
                name=item,
                display=display_name(item, item_names),
                why=why_text("mainstream", hero=hero.name_loc),
                how=_how_text(item, "按局势在关键节点合成"),
            )
            for item in picks
        ]

    threats: list[_Threat] = []
    silence = _has_role(pool, meta or {}, "Disabler", set())
    if any(h.short in _SILENCE for h in pool) and not has_self_dispel(hero.short):
        names = join_names(h.name_loc for h in pool if h.short in _SILENCE)[:32]
        threats.append(_Threat("silence", ("item_manta", "item_black_king_bar", "item_lotus_orb"), why_text("silence", names=names)))
    if len(silence) >= 2 or any(h.short in _SILENCE for h in pool):
        names = join_names(h.name_loc for h in silence[:2])
        # 自带驱散且已有黑皇：控制和沉默都能自己处理，不必再推分身
        if names and not (has_self_dispel(hero.short) and "item_black_king_bar" in owned):
            threats.append(_Threat("cc", ("item_black_king_bar", "item_aeon_disk", "item_manta"), why_text("cc", names=names)))
    nukers = _has_role(pool, meta or {}, "Nuker", set())
    self_roles = set((meta or {}).get(hero.hero_id).roles) if (meta or {}).get(hero.hero_id) is not None else set()
    carry_self = "Carry" in self_roles
    if len(nukers) >= 2 and not carry_self:
        names = join_names(h.name_loc for h in nukers[:2])
        threats.append(_Threat("magic", ("item_pipe", "item_black_king_bar", "item_glimmer_cape"), why_text("magic", names=names)))
    healers = [h for h in pool if h.short in _HEAL]
    if healers:
        names = join_names(h.name_loc for h in healers)[:32]
        threats.append(_Threat("heal", ("item_spirit_vessel", "item_skadi", "item_shivas_guard"), why_text("heal", names=names)))
    escapers = [h for h in pool if h.short in _ESCAPE]
    if escapers:
        names = join_names(h.name_loc for h in escapers)[:32]
        threats.append(_Threat("escape", ("item_orchid", "item_sheepstick", "item_nullifier"), why_text("escape", names=names)))
    physical = _has_role(pool, meta or {}, "Carry", set())
    if len(physical) >= 3 and not carry_self:
        threats.append(_Threat("physical", ("item_crimson_guard", "item_ghost", "item_assault"), why_text("physical")))

    result: list[ItemAdvice] = []
    used: set[str] = set()
    for threat in threats:
        item = _pick(threat.items, by_id, owned | used)
        if item is None:
            continue
        result.append(
            ItemAdvice(
                name=item,
                display=display_name(item, item_names),
                why=threat.reason,
                how=_how_text(item, "按局势在关键节点合成"),
                threat=threat.tag,
            )
        )
        used.add(item)
        if len(result) >= limit:
            return result

    for item in available:
        if len(result) >= limit:
            break
        if item in used or item in owned:
            continue
        result.append(
            ItemAdvice(
                name=item,
                display=display_name(item, item_names),
                why=why_text("mainstream", hero=hero.name_loc),
                how=_how_text(item, "按局势在关键节点合成"),
            )
        )
    return result

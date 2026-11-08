"""一次性补丁：团战提示按语言输出（中文保持原句式）。"""

from pathlib import Path

P = Path("src/dota2coach/coach/fight.py")
s = P.read_text(encoding="utf-8")

if "from .texts_fight import ftext" not in s:
    s = s.replace(
        "from .timers import upcoming",
        "from .timers import upcoming\nfrom .texts_fight import ftext",
        1,
    )

pairs = [
    (
        '"对面红点全没了：小心开雾抓人，退到有视野的位置或跟队友走"',
        'ftext("missing") or "对面红点全没了：小心开雾抓人，退到有视野的位置或跟队友走"',
    ),
    (
        '"小地图上有红点贴过来了，血量偏低：先拉走，别在兵线里硬打"',
        'ftext("near") or "小地图上有红点贴过来了，血量偏低：先拉走，别在兵线里硬打"',
    ),
    (
        'f"队友 {ally_cluster} 人在附近集结：可以跟团，先确认大招和 BKB 状态"',
        'ftext("group", n=ally_cluster) or f"队友 {ally_cluster} 人在附近集结：可以跟团，先确认大招和 BKB 状态"',
    ),
    (
        'text = "团战打起来了：" + "；".join(plan)',
        'text = (ftext("engage") or "团战打起来了：") + ("; " if ftext("engage") else "；").join(plan)',
    ),
    (
        'parts.append(f"先打 {focus}")',
        'parts.append(ftext("focus", name=focus) or f"先打 {focus}")',
    ),
    (
        'parts.append(f"绕开 {avoid}")',
        'parts.append(ftext("avoid", name=avoid) or f"绕开 {avoid}")',
    ),
    (
        'parts.append(f"小心 {watch} 的技能")',
        'parts.append(ftext("watch", name=watch) or f"小心 {watch} 的技能")',
    ),
    (
        'text = "团战打起来了：" + "；".join(parts) if parts else "团战打起来了：先看队友位置，别第一个上"',
        'text = ((ftext("engage") or "团战打起来了：") + ("; " if ftext("engage") else "；").join(parts)) if parts else (ftext("fallback") or "团战打起来了：先看队友位置，别第一个上")',
    ),
    (
        'f"刷钱路线：{routes[index]}"',
        'ftext("farm_route") or f"刷钱路线：{routes[index]}"',
    ),
    (
        'f"辅助眼位：{wards[index]}"',
        'ftext("ward_pos") or f"辅助眼位：{wards[index]}"',
    ),
]
for old, new in pairs:
    if old not in s:
        raise SystemExit(f"anchor missing: {old}")
    s = s.replace(old, new, 1)

# player_plan 中文行改为可被 ftext 覆盖
s = s.replace(
    'lines.append("你是前排/先手：顶上去吃第一波伤害，别追残血")',
    'lines.append(ftext("plan_tank") or "你是前排/先手：顶上去吃第一波伤害，别追残血")',
    1,
)
s = s.replace(
    'lines.append(f"你是控制：盯住 {key_target}，他一进场就交控")',
    'lines.append(ftext("plan_cc", target=key_target) or f"你是控制：盯住 {key_target}，他一进场就交控")',
    1,
)
s = s.replace(
    'line = f"你是法系：技能优先甩给 {squishy}，别空放"',
    'line = ftext("plan_mage", squishy=squishy) or f"你是法系：技能优先甩给 {squishy}，别空放"',
    1,
)
s = s.replace(
    'lines.append(f"你是刺客/核心：绕后切 {squishy}，打完就撤，别恋战")',
    'lines.append(ftext("plan_assassin", squishy=squishy) or f"你是刺客/核心：绕后切 {squishy}，打完就撤，别恋战")',
    1,
)
s = s.replace(
    "lines.append(f\"你是辅助：保 {ally_carry or '核心'}，先给控制/治疗再考虑输出\")",
    'lines.append(ftext("plan_guard", ally=(ally_carry or "core")) or f"你是辅助：保 {ally_carry or \'核心\'}，先给控制/治疗再考虑输出")',
    1,
)
s = s.replace(
    "lines.append(f\"团战先跟队友，优先集火 {squishy or '对面最脆的'}\")",
    'lines.append(ftext("plan_group", squishy=(squishy or "the squishiest")) or f"团战先跟队友，优先集火 {squishy or \'对面最脆的\'}")',
    1,
)
P.write_text(s, encoding="utf-8")
print("fight patched")

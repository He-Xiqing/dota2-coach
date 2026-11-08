"""一次性补丁：出装理由/用法按语言输出（非中文省略中文用法）。"""

from pathlib import Path

P = Path("src/dota2coach/coach/items_advice.py")
s = P.read_text(encoding="utf-8")

s = s.replace(
    "from ..knowledge.builds import ItemInfo, display_name",
    "from ..knowledge.builds import ItemInfo, display_name\nfrom .texts import language as ui_language\nfrom .texts_why import why as why_text",
    1,
)

pairs = [
    ('f"B 站 {hero.name_loc} 攻略推荐"', 'why_text("mainstream", hero=hero.name_loc) if ui_language() != "zh-CN" else f"B 站 {hero.name_loc} 攻略推荐"'),
    ('f"{hero.name_loc}主流出装（OpenDota 热度）"', 'why_text("mainstream", hero=hero.name_loc)'),
    ('f"对面有沉默（{names}）"', 'why_text("silence", names=names)'),
    ('f"对面控制多（{names}），先手易被秒"', 'why_text("cc", names=names)'),
    ('f"对面法系爆发高（{names}）"', 'why_text("magic", names=names)'),
    ('f"对面回复强（{names}），要减治疗"', 'why_text("heal", names=names)'),
    ('f"对面机动性高（{names}），需要硬控"', 'why_text("escape", names=names)'),
    ('"对面物理核心多，需要减伤/缴械"', 'why_text("physical")'),
]
for old, new in pairs:
    if old not in s:
        raise SystemExit(f"anchor missing: {old}")
    s = s.replace(old, new)

# 非中文：用法表是中文，直接省略（app 会跳过空 how）
s = s.replace(
    'how=_HOW.get(item, "按攻略在关键节点出"),',
    'how=_HOW.get(item, "按攻略在关键节点出") if ui_language() == "zh-CN" else "",',
    1,
)
s = s.replace(
    "                how=_HOW[item],",
    '                how=_HOW[item] if ui_language() == "zh-CN" else "",',
    1,
)
P.write_text(s, encoding="utf-8")
print("items_advice patched")

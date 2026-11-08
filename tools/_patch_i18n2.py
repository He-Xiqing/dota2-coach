"""一次性补丁：非中文省略中文用法表；英雄名按语言显示。"""

from pathlib import Path

P = Path("src/dota2coach/coach/items_advice.py")
s = P.read_text(encoding="utf-8")
s = s.replace(
    'how=_HOW.get(item, "按局势在关键节点合成"),',
    'how=_HOW.get(item, "按局势在关键节点合成") if ui_language() == "zh-CN" else "",',
    1,
)
s = s.replace(
    'how=_HOW.get(item, "按局势在关键节点合成"),',
    'how=_HOW.get(item, "按局势在关键节点合成") if ui_language() == "zh-CN" else "",',
    1,
)
P.write_text(s, encoding="utf-8")

A = Path("src/dota2coach/app.py")
t = A.read_text(encoding="utf-8")
if "from .knowledge.skills import load_hero_skills, skills_file_for" not in t:
    t = t.replace(
        "from .knowledge.builds import load_item_table",
        "from .knowledge.builds import load_item_table\nfrom .knowledge.skills import load_hero_skills, skills_file_for",
        1,
    )
t = t.replace(
        '        self._load_localized_items(config.data_dir)',
        '        self._load_localized_items(config.data_dir)\n'
        '        self.hero_skills = load_hero_skills(\n'
        '            skills_file_for(config.data_dir, config.app.language)\n'
        '        )',
        1,
)
A.write_text(t, encoding="utf-8")
print("patched")

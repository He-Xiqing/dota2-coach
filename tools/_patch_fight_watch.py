"""团战 watch 列表：非中文只报英雄名，避免中文技能名混排。"""

from pathlib import Path

p = Path("src/dota2coach/coach/fight.py")
s = p.read_text(encoding="utf-8")
s = s.replace("from .texts_fight import ftext", "from .texts import language\nfrom .texts_fight import ftext")
old = '''        skill = _SKILLS.get(hero.short)
        if skill:
            watch.append(f"{hero.name_loc}（{skill}）")'''
new = '''        skill = _SKILLS.get(hero.short)
        if skill:
            # 技能昵称表只有中文，非中文只报英雄名，避免中英混排
            if language().startswith("zh"):
                watch.append(f"{hero.name_loc}（{skill}）")
            else:
                watch.append(hero.name_loc)'''
print("hit", s.count(old))
s = s.replace(old, new)
p.write_text(s, encoding="utf-8")
print("patched")

"""一次性补丁：非中文用 ", " 而不是 "、" 连接名字。"""

from pathlib import Path

T = Path("src/dota2coach/coach/texts.py")
s = T.read_text(encoding="utf-8")
if "def join_names(" not in s:
    s += '''

def join_names(names) -> str:
    """中文用顿号，其余语言用逗号。"""
    sep = "、" if language() == "zh-CN" else ", "
    return sep.join(str(name) for name in names if name)


def _sep() -> str:
    return "、" if language() == "zh-CN" else ", "
'''
    T.write_text(s, encoding="utf-8")

L = Path("src/dota2coach/coach/lane.py")
t = L.read_text(encoding="utf-8")
t = t.replace(
    'labels = "、".join(hero.name_loc for hero in known)',
    'labels = join_names(hero.name_loc for hero in known)',
)
t = t.replace(
    'labels = "、".join(hero.name_loc for hero in picks)',
    'labels = join_names(hero.name_loc for hero in picks)',
)
t = t.replace(
    'labels = [hero.name_loc for hero in heroes if hero is not None][:limit]',
    'labels = [hero.name_loc for hero in heroes if hero is not None][:limit]',
)
if "join_names" in t and "from .texts import" in t:
    first = t.splitlines()[0]
    for line in t.splitlines():
        if line.startswith("from .texts import"):
            t = t.replace(line, line.rstrip() + ", join_names", 1)
            break
L.write_text(t, encoding="utf-8")

I = Path("src/dota2coach/coach/items_advice.py")
u = I.read_text(encoding="utf-8")
u = u.replace(
    "from .texts import language as ui_language",
    "from .texts import join_names, language as ui_language",
    1,
)
u = u.replace('names = "、".join(h.name_loc for h in pool if h.short in _SILENCE)[:18]', 'names = join_names(h.name_loc for h in pool if h.short in _SILENCE)[:32]')
u = u.replace('names = "、".join(h.name_loc for h in silence[:2])', 'names = join_names(h.name_loc for h in silence[:2])')
u = u.replace('names = "、".join(h.name_loc for h in nukers[:2])', 'names = join_names(h.name_loc for h in nukers[:2])')
u = u.replace('names = "、".join(h.name_loc for h in healers)[:18]', 'names = join_names(h.name_loc for h in healers)[:32]')
u = u.replace('names = "、".join(h.name_loc for h in escapers)[:18]', 'names = join_names(h.name_loc for h in escapers)[:32]')
I.write_text(u, encoding="utf-8")
print("join patched")

"""一次性补丁：非中文时把名单里的英雄名换成对应语言名。"""

from pathlib import Path

P = Path("src/dota2coach/app.py")
s = P.read_text(encoding="utf-8")

if "from dataclasses import replace" not in s:
    s = s.replace("from dataclasses import dataclass", "from dataclasses import dataclass, replace", 1)

helper = '''
    def _localize_roster(self, roster):
        """非中文界面：把名单中的英雄名替换为对应语言（来自 skills 数据）。"""
        if texts_language() == "zh-CN" or not getattr(self, "hero_skills", None):
            return roster

        def fix(hero):
            if hero is None:
                return None
            info = self.hero_skills.get(int(getattr(hero, "hero_id", 0) or 0))
            if info is None or not info.name:
                return hero
            return replace(hero, name_loc=info.name)

        return replace(
            roster,
            allies=tuple(fix(hero) for hero in roster.allies),
            enemies=tuple(fix(hero) for hero in roster.enemies),
        )

'''

anchor = "    def _identify(self, image, self_hero: HeroInfo | None, stamp: str):"
if anchor not in s:
    raise SystemExit("identify anchor missing")
s = s.replace(anchor, helper + anchor, 1)

s = s.replace(
    "        roster, bar = best\n        if roster.known >= 8:\n            return roster, bar",
    "        roster, bar = best\n        if roster.known >= 8:\n            return self._localize_roster(roster), bar",
    1,
)
s = s.replace(
    "        if roster2.known > roster.known:\n            roster = roster2\n        return roster, bar",
    "        if roster2.known > roster.known:\n            roster = roster2\n        return self._localize_roster(roster), bar",
    1,
)
P.write_text(s, encoding="utf-8")
print("roster names patched")

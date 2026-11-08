"""英雄技能简介的解析与截断。"""

from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path
from uuid import uuid4

from dota2coach.knowledge.skills import (
    MAX_DESC,
    Skill,
    load_hero_skills,
    skill_tips,
)


class SkillBriefTest(unittest.TestCase):
    def test_keeps_short_clause(self) -> None:
        skill = Skill("狂战士之吼", "嘲讽附近的敌方单位，强迫他们攻击自己")
        self.assertTrue(skill.brief.startswith("嘲讽附近的敌方单位"))
        self.assertLessEqual(len(skill.brief), MAX_DESC)

    def test_truncates_long_clause(self) -> None:
        long_text = "影魔对其正前方区域释放毁灭能量" * 10
        skill = Skill("毁灭阴影", long_text)
        self.assertLessEqual(len(skill.brief), MAX_DESC)
        self.assertTrue(skill.brief.endswith("…"))

    def test_empty_desc(self) -> None:
        self.assertEqual(Skill("空", "").brief, "")


class LoadTest(unittest.TestCase):
    def test_load_and_tips(self) -> None:
        payload = {
            "1": {
                "name": "敌法师",
                "bio": "被潮水般的侵略者摧毁的古老寺院",
                "abilities": [
                    {"name": "法力损毁", "desc": "每次攻击损毁魔法值并造成伤害。"},
                    {"name": "闪烁", "desc": "短距离传送，自由出入战场。"},
                ],
            }
        }
        tmp = Path(__file__).resolve().parent / "_tmp" / f"skills-{uuid4().hex[:8]}"
        tmp.mkdir(parents=True, exist_ok=True)
        try:
            path = tmp / "hero_skills.json"
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            data = load_hero_skills(path)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        self.assertIn(1, data)
        self.assertEqual(data[1].name, "敌法师")
        self.assertEqual(len(data[1].abilities), 2)
        tips = skill_tips(data, 1, limit=2)
        self.assertEqual(len(tips), 2)
        self.assertTrue(tips[0].startswith("法力损毁·"))

    def test_missing_file(self) -> None:
        self.assertEqual(load_hero_skills(Path("does-not-exist.json")), {})
        self.assertEqual(skill_tips({}, 1), [])


if __name__ == "__main__":
    unittest.main()

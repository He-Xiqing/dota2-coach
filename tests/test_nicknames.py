"""社区叫法/英文缩写的解析。"""

from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path
from uuid import uuid4

from dota2coach.knowledge.nicknames import load_nicknames


class NicknameTest(unittest.TestCase):
    def test_parse_forms(self) -> None:
        tmp = Path(__file__).resolve().parent / "_tmp" / f"nick-{uuid4().hex[:8]}"
        tmp.mkdir(parents=True, exist_ok=True)
        try:
            path = tmp / "hero_nicknames.json"
            path.write_text(
                json.dumps(
                    {"slark": "小鱼人|Slark", "lina": "|Lina", "axe": "斧王|"},
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            data = load_nicknames(path)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        self.assertEqual(data["slark"], "小鱼人 · Slark")
        self.assertEqual(data["lina"], "Lina")
        self.assertEqual(data["axe"], "斧王")

    def test_missing_file(self) -> None:
        self.assertEqual(load_nicknames(Path("does-not-exist.json")), {})
        self.assertEqual(load_nicknames(None), {})


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path
from uuid import uuid4

from dota2coach.coach.guides import GuideStore
from dota2coach.sources.bilibili import Comment, Video
from dota2coach.sources.guides_builder import (
    Evidence,
    clean_sentence,
    heuristic_tips,
    merge_tips,
    patch_key,
    select_videos,
    split_sentences,
    tip_id,
    trim,
    validate_tips,
)
from dota2coach.sources.patch import current_patch, find_patch

ROOT = Path(__file__).resolve().parents[1]
HEROES = {"juggernaut": "剑圣", "nevermore": "影魔", "pudge": "帕吉", "lina": "莉娜"}


def _video(bvid="BV1", title="7.41 上分", play=50000, duration=600, aid=1, description="") -> Video:
    return Video(
        bvid=bvid,
        aid=aid,
        title=title,
        author="up",
        play=play,
        danmaku=10,
        pubdate=1760000000,
        duration=duration,
        description=description,
        tag="DOTA2",
    )


class PatchTests(unittest.TestCase):
    def test_find_patch(self) -> None:
        self.assertEqual(find_patch("7.41f 更新速览"), "7.41f")
        self.assertEqual(find_patch("版本 7.41"), "7.41")
        self.assertIsNone(find_patch("没有版本号"))

    def test_patch_key(self) -> None:
        self.assertEqual(patch_key("7.41f"), "7.41")
        self.assertEqual(patch_key("7.41"), "7.41")

    def test_current_patch_uses_cache(self) -> None:
        tmp = ROOT / "tests" / "_tmp" / f"patch-{uuid4().hex[:8]}"
        tmp.mkdir(parents=True)
        try:
            cache = tmp / "patch.json"
            cache.write_text('{"patch": "7.41f", "fetched_at": 9999999999}', encoding="utf-8")
            self.assertEqual(current_patch(cache, now=1000.0), "7.41f")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class SelectTests(unittest.TestCase):
    def test_filters_patch_duration_and_play(self) -> None:
        videos = [
            _video("BV1", "7.41 上分", 90000),
            _video("BV2", "7.40 回顾", 90000),
            _video("BV3", "7.41 速览", 1000),
            _video("BV4", "7.41 超长", 90000, duration=3000),
            _video("BV1", "7.41 重复", 90000),
        ]
        picked = select_videos(videos, "7.41f", min_play=30000, limit=5)
        self.assertEqual([v.bvid for v in picked], ["BV1"])

    def test_limit_and_sort(self) -> None:
        videos = [_video(f"BV{i}", f"7.41 攻略 {i}", 10000 * i) for i in (1, 2, 3)]
        picked = select_videos(videos, "7.41", min_play=0, limit=2)
        self.assertEqual([v.bvid for v in picked], ["BV3", "BV2"])

    def test_drops_offtopic(self) -> None:
        videos = [
            _video("BV1", "7.41 英雄攻略", 90000),
            _video("BV2", "Ame 举哑铃为什么是对的", 200000),
            _video("BV3", "7.41 世界赛集锦", 200000),
        ]
        picked = select_videos(videos, "7.41", min_play=0, limit=5, hero_names=HEROES)
        self.assertEqual([v.bvid for v in picked], ["BV1"])


class HeuristicTests(unittest.TestCase):
    def _evidence(self, *, comments=(), danmaku=(), transcript="", summary="") -> Evidence:
        return Evidence(
            video=_video(),
            comments=list(comments),
            danmaku=list(danmaku),
            transcript=transcript,
            ai_summary=summary,
        )

    def test_comment_with_hero_and_imperative(self) -> None:
        ev = self._evidence(comments=[Comment("剑圣先出相位鞋，别裸狂战，对线太弱了", 120)])
        tips = heuristic_tips([ev], HEROES)
        self.assertEqual(len(tips), 1)
        self.assertEqual(tips[0]["hero"], "juggernaut")
        self.assertLessEqual(len(tips[0]["text"]), 24)
        self.assertIn("相位鞋", tips[0]["text"])

    def test_noise_and_low_like_filtered(self) -> None:
        ev = self._evidence(
            comments=[Comment("这期抽奖链接在哪里", 500), Comment("先出相位鞋", 1)]
        )
        self.assertEqual(heuristic_tips([ev], HEROES, min_likes=5), [])

    def test_text_without_imperative_filtered(self) -> None:
        ev = self._evidence(comments=[Comment("这主播真菜", 100)])
        self.assertEqual(heuristic_tips([ev], HEROES), [])

    def test_danmaku_needs_repeat(self) -> None:
        ev = self._evidence(danmaku=["剑圣先出相位鞋", "剑圣先出相位鞋", "随便说说"])
        tips = heuristic_tips([ev], HEROES)
        self.assertEqual(len(tips), 1)
        self.assertEqual(tips[0]["evidence"], "danmaku")

    def test_danmaku_without_hero_dropped(self) -> None:
        ev = self._evidence(danmaku=["先出相位鞋", "先出相位鞋"])
        self.assertEqual(heuristic_tips([ev], HEROES), [])

    def test_transcript_sentence(self) -> None:
        ev = self._evidence(transcript="这把影魔一定要先出魔瓶。别裸跳刀。")
        tips = heuristic_tips([ev], HEROES)
        self.assertTrue(any(t["evidence"] == "transcript" for t in tips))
        self.assertEqual(tips[0]["hero"], "nevermore")

    def test_trim_and_split(self) -> None:
        self.assertEqual(trim("一二三四五六", 4), "一二三…")
        self.assertEqual(split_sentences("a。b！c？"), ["a", "b", "c"])
        self.assertEqual(clean_sentence("1、 先出相位鞋。"), "先出相位鞋")


class ValidateTests(unittest.TestCase):
    def test_rejects_unknown_hero_and_trims(self) -> None:
        raw = [
            {"hero": "not_a_hero", "text": "这是一条很长很长很长很长很长很长很长很长的建议"},
            {"hero": "Juggernaut", "lane": "中路", "phase": "对线期", "text": "先出相位鞋"},
            {"hero": "pudge", "text": "先出相位鞋"},
        ]
        tips = validate_tips(raw, set(HEROES), max_tips=10)
        self.assertEqual(len(tips), 3)
        self.assertEqual(tips[0]["hero"], "")
        self.assertLessEqual(len(tips[0]["text"]), 24)
        self.assertEqual(tips[1]["hero"], "juggernaut")
        self.assertEqual(tips[1]["lane"], "任意")

    def test_tip_id_stable(self) -> None:
        self.assertEqual(tip_id("a", "b"), tip_id("a", "b"))
        self.assertNotEqual(tip_id("a", "b"), tip_id("a", "c"))

    def test_merge_sources_and_scores(self) -> None:
        a = {"hero": "juggernaut", "text": "先出相位鞋", "sources": ["BV1"], "score": 1.0, "evidence": "comments"}
        b = {"hero": "juggernaut", "text": "先出相位鞋", "sources": ["BV2"], "score": 1.5, "evidence": "transcript"}
        merged = merge_tips([a, b])
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["sources"], ["BV1", "BV2"])
        self.assertEqual(merged[0]["evidence"], "transcript")
        self.assertGreater(merged[0]["score"], 2.5)


class StoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = ROOT / "tests" / "_tmp" / f"guides-{uuid4().hex[:8]}"
        self.dir.mkdir(parents=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)

    def _write(self, name: str, payload: dict) -> None:
        (self.dir / name).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def test_load_and_filter(self) -> None:
        self._write(
            "7.41f.json",
            {
                "patch": "7.41f",
                "tips": [
                    {"id": "a", "hero": "juggernaut", "lane": "任意", "phase": "对线期", "text": "先出相位鞋", "score": 2.0},
                    {"id": "b", "hero": "", "lane": "中", "phase": "中期", "text": "中路多游走", "score": 1.0},
                ],
            },
        )
        store = GuideStore.load(self.dir, patch="7.41f")
        self.assertFalse(store.empty)
        tips = store.tips_for("juggernaut", "中", "对线期")
        self.assertEqual(tips[0].id, "a")
        self.assertEqual(store.tips_for("pudge", "上", "后期"), [])

    def test_missing_dir_is_empty(self) -> None:
        store = GuideStore.load(self.dir / "nope", patch="7.41f")
        self.assertTrue(store.empty)
        self.assertEqual(store.tips_for("juggernaut", "中", "对线期"), [])


if __name__ == "__main__":
    unittest.main()

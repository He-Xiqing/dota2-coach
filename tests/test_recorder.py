import json
import shutil
import sys
import unittest
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dota2coach.gsi.models import Snapshot  # noqa: E402
from dota2coach.gsi.recorder import GsiRecorder  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "gsi" / "playing.json"


class FakeClock:
    def __init__(self, start: float = 100.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class RecorderTest(unittest.TestCase):
    def setUp(self) -> None:
        # 沙箱不允许改系统 Temp 目录权限，测试统一用工作区内的临时目录
        self.dir = ROOT / "tests" / "_tmp" / f"recorder-{uuid4().hex[:8]}"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.clock = FakeClock()
        self.raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.recorder = GsiRecorder(self.dir, min_interval=0.2, clock=self.clock)

    def tearDown(self) -> None:
        self.recorder.close()
        shutil.rmtree(self.dir, ignore_errors=True)

    def _raw_file(self) -> Path:
        files = sorted((self.dir / "gsi_raw").glob("*.jsonl"))
        self.assertEqual(len(files), 1, files)
        return files[0]

    def test_throttles_raw_writes(self) -> None:
        for _ in range(3):
            self.recorder.record(Snapshot(self.raw))
        path = self._raw_file()
        self.assertEqual(path.name.split("-")[0], "7890123456")
        self.assertEqual(len(path.read_text(encoding="utf-8").splitlines()), 1)

        self.clock.advance(1.0)
        self.recorder.record(Snapshot(self.raw))
        self.assertEqual(len(path.read_text(encoding="utf-8").splitlines()), 2)
        self.assertEqual(self.recorder.records, 4)

    def test_key_inventory(self) -> None:
        self.recorder.record(Snapshot(self.raw))
        self.recorder.close()
        data = json.loads((self.dir / "gsi_keys.json").read_text(encoding="utf-8"))
        paths = data["paths"]
        self.assertIn("hero.level", paths)
        self.assertIn("abilities.ability0.name", paths)
        self.assertIn("map.game_state", paths)
        self.assertEqual(data["records"], 1)
        self.assertFalse(data["truncated"])

    def test_summary_line(self) -> None:
        self.recorder.record(Snapshot(self.raw))
        self.recorder.close()
        lines = (self.dir / "gsi_summary.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)
        entry = json.loads(lines[0])
        self.assertEqual(entry["hero"], "npc_dota_hero_nevermore")
        self.assertEqual(entry["match_id"], 7890123456)
        self.assertEqual(entry["game_time"], 312)


if __name__ == "__main__":
    unittest.main()

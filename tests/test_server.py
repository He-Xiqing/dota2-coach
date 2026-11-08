import json
import sys
import unittest
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dota2coach.gsi.models import Snapshot  # noqa: E402
from dota2coach.gsi.server import GsiServer  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "gsi" / "playing.json"


class ServerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.received: list[Snapshot] = []
        self.server = GsiServer("127.0.0.1", 0, on_snapshot=self.received.append)
        self.server.start()
        self.url = f"http://127.0.0.1:{self.server.port}/"

    def tearDown(self) -> None:
        self.server.stop()

    def _post(self, body: bytes) -> tuple[int, dict]:
        request = urllib.request.Request(
            self.url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def test_receives_payload(self) -> None:
        body = FIXTURE.read_bytes()
        status, payload = self._post(body)
        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(len(self.received), 1)
        self.assertEqual(self.received[0].hero_name, "npc_dota_hero_nevermore")

    def test_bad_json_returns_400(self) -> None:
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self._post(b"{not json")
        self.assertEqual(ctx.exception.code, 400)
        self.assertEqual(len(self.received), 0)

    def test_empty_body_returns_400(self) -> None:
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self._post(b"")
        self.assertEqual(ctx.exception.code, 400)

    def test_get_is_alive(self) -> None:
        with urllib.request.urlopen(self.url, timeout=5) as response:
            self.assertEqual(response.status, 200)


if __name__ == "__main__":
    unittest.main()

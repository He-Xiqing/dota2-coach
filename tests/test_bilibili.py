from __future__ import annotations

import json
import unittest
from pathlib import Path

from dota2coach.sources.bilibili import (
    NAV_URL,
    SEARCH_URL,
    BilibiliClient,
    RiskControl,
    audio_stream,
    danmaku_top,
    parse_danmaku,
    parse_duration,
    parse_replies,
    parse_search,
    sign_wbi,
    strip_em,
    wbi_keys,
    wbi_mixin_key,
)
from dota2coach.sources.bilibili import BilibiliError

FIXTURES = Path(__file__).parent / "fixtures" / "bilibili"


class FakeResponse:
    def __init__(self, payload: dict | None = None, *, text: str = "", status_code: int = 200) -> None:
        self.payload = payload or {}
        self.text = text
        self.status_code = status_code

    def json(self) -> dict:
        return self.payload


class FakeHttp:
    def __init__(self, mapping: dict[str, FakeResponse]) -> None:
        self.mapping = mapping
        self.calls: list[tuple[str, dict | None]] = []

    def get(self, url: str, params: dict | None = None, headers: dict | None = None) -> FakeResponse:
        self.calls.append((url, params))
        return self.mapping[url]


def _fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class ParseTests(unittest.TestCase):
    def test_strip_em(self) -> None:
        self.assertEqual(strip_em('<em class="keyword">7.41</em> 上分'), "7.41 上分")
        self.assertEqual(strip_em("a &amp; b"), "a & b")

    def test_parse_duration(self) -> None:
        self.assertEqual(parse_duration("12:34"), 754)
        self.assertEqual(parse_duration("1:02:03"), 3723)
        self.assertEqual(parse_duration("90"), 90)
        self.assertEqual(parse_duration("bad"), 0)

    def test_parse_search_keeps_only_videos(self) -> None:
        videos = parse_search(_fixture("search.json"))
        self.assertEqual([v.bvid for v in videos], ["BV1qZjxz4ETT", "BV1bad0ld0ld"])
        self.assertEqual(videos[0].title, "7.41 版本上分英雄推荐")
        self.assertEqual(videos[0].duration, 872)

    def test_parse_replies(self) -> None:
        comments = parse_replies(_fixture("replies.json"))
        self.assertEqual(len(comments), 3)
        self.assertEqual(comments[0].likes, 120)
        self.assertIn("相位鞋", comments[0].text)

    def test_parse_danmaku_and_top(self) -> None:
        text = (FIXTURES / "dm.xml").read_text(encoding="utf-8")
        items = parse_danmaku(text)
        self.assertEqual(len(items), 5)
        top = danmaku_top(items, top=5, min_count=2)
        self.assertEqual(top[0][1], 2)
        self.assertIn("先出相位鞋", [word for word, _ in top])

    def test_parse_danmaku_bad_xml(self) -> None:
        self.assertEqual(parse_danmaku("<i><d>broken"), [])

    def test_audio_stream(self) -> None:
        payload = {"code": 0, "data": {"dash": {"audio": [{"baseUrl": "https://cdn/a.m4a"}]}}}
        self.assertEqual(audio_stream(payload), "https://cdn/a.m4a")
        self.assertEqual(audio_stream({"code": 0, "data": {}}), "")


class SignTests(unittest.TestCase):
    def test_mixin_key_length(self) -> None:
        key = wbi_mixin_key("7cd084941338484aae1ad9425b84077c", "4932caff0ff746eab6f01bf08b70ac45")
        self.assertEqual(len(key), 32)

    def test_sign_is_stable_and_drops_illegal_chars(self) -> None:
        signed = sign_wbi({"keyword": "a!b'c", "page": 1}, "img", "sub", wts=1700000000)
        self.assertEqual(signed["keyword"], "abc")
        self.assertEqual(signed["wts"], "1700000000")
        self.assertIn("w_rid", signed)

    def test_wbi_keys_from_nav(self) -> None:
        img, sub = wbi_keys(_fixture("nav.json"))
        self.assertEqual(img, "7cd084941338484aae1ad9425b84077c")
        self.assertEqual(sub, "4932caff0ff746eab6f01bf08b70ac45")


class ClientTests(unittest.TestCase):
    def _client(self, mapping: dict[str, FakeResponse]) -> tuple[BilibiliClient, FakeHttp]:
        mapping = {NAV_URL: FakeResponse(_fixture("nav.json")), **mapping}
        http = FakeHttp(mapping)
        client = BilibiliClient(http, interval=0.0)
        return client, http

    def test_search_parses(self) -> None:
        client, http = self._client({SEARCH_URL: FakeResponse(_fixture("search.json"))})
        videos = client.search_videos("DOTA2 7.41", limit=5)
        self.assertEqual(len(videos), 2)
        # 第二次搜索不应重复取 nav
        client.search_videos("DOTA2 7.41", limit=5)
        nav_calls = [url for url, _ in http.calls if url == NAV_URL]
        self.assertEqual(len(nav_calls), 1)

    def test_search_sends_signature(self) -> None:
        client, http = self._client({SEARCH_URL: FakeResponse(_fixture("search.json"))})
        client.search_videos("DOTA2 7.41", limit=5)
        search_params = [params for url, params in http.calls if url == SEARCH_URL][0]
        self.assertIn("w_rid", search_params or {})
        self.assertIn("wts", search_params or {})

    def test_search_risk_control_on_voucher(self) -> None:
        payload = {"code": 0, "data": {"v_voucher": "voucher-x", "result": []}}
        client, _ = self._client({SEARCH_URL: FakeResponse(payload)})
        with self.assertRaises(RiskControl):
            client.search_videos("x")

    def test_http_412_raises_risk_control(self) -> None:
        client, _ = self._client({SEARCH_URL: FakeResponse({}, status_code=412)})
        with self.assertRaises(RiskControl):
            client.search_videos("x")

    def test_api_error_code(self) -> None:
        payload = {"code": -400, "message": "请求错误"}
        client, _ = self._client({SEARCH_URL: FakeResponse(payload)})
        with self.assertRaises(BilibiliError):
            client.search_videos("x")

    def test_throttle_calls_sleep(self) -> None:
        sleeps: list[float] = []
        http = FakeHttp({NAV_URL: FakeResponse(_fixture("nav.json")), SEARCH_URL: FakeResponse(_fixture("search.json"))})
        client = BilibiliClient(http, interval=1.0, sleep=sleeps.append)
        client.search_videos("a")
        client.search_videos("b")
        self.assertTrue(sleeps)
        self.assertGreater(sleeps[-1], 0)

    def test_ai_conclusion_without_sessdata_is_empty(self) -> None:
        client, _ = self._client({})
        self.assertEqual(client.ai_conclusion("BV1", 2), "")


if __name__ == "__main__":
    unittest.main()

"""YouTube 攻略源的离线解析测试（不联网）。"""

from __future__ import annotations

import json
import unittest

from dota2coach.sources.youtube import (
    YtVideo,
    YouTubeError,
    parse_duration,
    parse_search,
    parse_view_count,
)

SAMPLE = """
<html><script>var ytInitialData = {"contents":{"twoColumnSearchResultsRenderer":{"primaryContents":{
"sectionListRenderer":{"contents":[{"itemSectionRenderer":{"contents":[
{"videoRenderer":{"videoId":"abc123XYZ","title":{"runs":[{"text":"DOTA2 Slark guide 7.41f - carry like a pro"}]},
 "ownerText":{"runs":[{"text":"Dota Academy"}]},"viewCountText":{"simpleText":"123,456 views"},
 "lengthText":{"simpleText":"18:42"},"publishedTimeText":{"simpleText":"2 weeks ago"}}}
]}}]}}}}}};</script></html>
"""


class YouTubeParseTest(unittest.TestCase):
    def test_parse_view_count(self) -> None:
        self.assertEqual(parse_view_count("123,456 views"), 123456)
        self.assertEqual(parse_view_count("1.2M views"), 1_200_000)
        self.assertEqual(parse_view_count("no views"), 0)

    def test_parse_duration(self) -> None:
        self.assertEqual(parse_duration("18:42"), 1122)
        self.assertEqual(parse_duration("1:02:03"), 3723)
        self.assertEqual(parse_duration(""), 0)

    def test_parse_search(self) -> None:
        videos = parse_search(SAMPLE)
        self.assertEqual(len(videos), 1)
        video = videos[0]
        self.assertEqual(video.video_id, "abc123XYZ")
        self.assertEqual(video.views, 123456)
        self.assertEqual(video.duration, 1122)
        self.assertIn("Slark", video.title)
        self.assertTrue(video.url.startswith("https://www.youtube.com/watch?v="))

    def test_empty_payload(self) -> None:
        self.assertEqual(parse_search("<html></html>"), [])

    def test_error_type(self) -> None:
        self.assertTrue(issubclass(YouTubeError, RuntimeError))
        self.assertEqual(YtVideo("x", "t", "c", 1, 60, "now").url, "https://www.youtube.com/watch?v=x")


if __name__ == "__main__":
    unittest.main()

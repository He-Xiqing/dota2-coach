"""YouTube 攻略数据源（可选，需要可访问 YouTube 的网络或代理）。

- 搜索：抓 https://www.youtube.com/results 的 ytInitialData（无需 API key）
- 字幕：优先 youtube-transcript-api（可选依赖）
- 音频：优先 yt-dlp（可选依赖），交给 ASR 转写
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

import httpx

SEARCH_URL = "https://www.youtube.com/results"
WATCH_URL = "https://www.youtube.com/watch?v={video_id}"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
_INIT_RE = re.compile(r"var ytInitialData = (\{.*?\});</script>", re.S)


class YouTubeError(RuntimeError):
    pass


@dataclass(frozen=True)
class YtVideo:
    video_id: str
    title: str
    channel: str
    views: int
    duration: int
    published: str

    @property
    def url(self) -> str:
        return WATCH_URL.format(video_id=self.video_id)


def _text(node: dict | None) -> str:
    if not node:
        return ""
    if "simpleText" in node:
        return str(node["simpleText"])
    runs = node.get("runs") or []
    return "".join(str(run.get("text", "")) for run in runs)


def parse_view_count(text: str) -> int:
    """支持 "123,456 views"、"1.2M views"、"12K views"。"""
    match = re.search(r"([0-9][0-9.,]*)\s*([KMB]?)", str(text or ""), re.IGNORECASE)
    if not match:
        return 0
    raw, unit = match.group(1), match.group(2).upper()
    raw = raw.replace(",", "")
    try:
        value = float(raw)
    except ValueError:
        return 0
    multiplier = {"": 1, "K": 1_000, "M": 1_000_000, "B": 1_000_000_000}.get(unit, 1)
    return int(value * multiplier)


def parse_duration(text: str) -> int:
    parts = [p for p in (text or "").split(":") if p.isdigit()]
    seconds = 0
    for part in parts:
        seconds = seconds * 60 + int(part)
    return seconds


def _initial_data(html: str) -> str:
    """从页面里截出 ytInitialData 的 JSON（括号配平，避开字符串里的花括号）。"""
    index = (html or "").find("ytInitialData")
    if index < 0:
        return ""
    start = html.find("{", index)
    if start < 0:
        return ""
    depth = 0
    in_string = False
    escaped = False
    for pos in range(start, len(html)):
        char = html[pos]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return html[start : pos + 1]
    return ""


def parse_search(html: str) -> list[YtVideo]:
    payload = _initial_data(html or "")
    if not payload:
        match = _INIT_RE.search(html or "")
        payload = match.group(1) if match else ""
    if not payload:
        return []
    try:
        data = json.loads(payload)
    except ValueError:
        return []
    found: list[YtVideo] = []
    seen: set[str] = set()

    def walk(node: object) -> None:
        if isinstance(node, dict):
            renderer = node.get("videoRenderer")
            if isinstance(renderer, dict):
                vid = str(renderer.get("videoId") or "")
                if vid and vid not in seen:
                    seen.add(vid)
                    found.append(
                        YtVideo(
                            video_id=vid,
                            title=_text(renderer.get("title")),
                            channel=_text(renderer.get("ownerText")),
                            views=parse_view_count(_text(renderer.get("viewCountText"))),
                            duration=parse_duration(_text(renderer.get("lengthText"))),
                            published=_text(renderer.get("publishedTimeText")),
                        )
                    )
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(data)
    return found


class YouTubeClient:
    def __init__(
        self,
        http: httpx.Client | None = None,
        timeout: float = 20.0,
        proxy: str = "",
    ) -> None:
        self._owns = http is None
        self._proxy = proxy
        kwargs: dict = {"timeout": timeout, "follow_redirects": True}
        if proxy:
            kwargs["proxy"] = proxy
        self._http = http or httpx.Client(**kwargs)
        self._http.headers.setdefault("User-Agent", USER_AGENT)
        self._http.headers.setdefault("Accept-Language", "en-US,en;q=0.9")

    def close(self) -> None:
        if self._owns:
            self._http.close()

    def search(self, query: str, limit: int = 10) -> list[YtVideo]:
        try:
            response = self._http.get(SEARCH_URL, params={"search_query": query})
        except httpx.HTTPError as exc:  # pragma: no cover - 网络相关
            raise YouTubeError(f"YouTube 访问失败：{exc}") from exc
        if response.status_code != 200:
            raise YouTubeError(f"YouTube 返回 HTTP {response.status_code}")
        videos = parse_search(response.text)
        return videos[:limit]

    def transcript(self, video_id: str, languages: tuple[str, ...] = ("en",)) -> str | None:
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
        except Exception:
            return None
        try:
            if self._proxy:
                entries = YouTubeTranscriptApi.get_transcript(
                    video_id,
                    languages=list(languages),
                    proxies={"http": self._proxy, "https": self._proxy},
                )
            else:
                entries = YouTubeTranscriptApi.get_transcript(video_id, languages=list(languages))
        except TypeError:
            try:
                entries = YouTubeTranscriptApi.get_transcript(video_id, languages=list(languages))
            except Exception:
                return None
        except Exception:
            return None
        return "\n".join(str(item.get("text", "")) for item in entries).strip() or None

    def download_audio(self, video_id: str, dest: Path) -> Path | None:
        try:
            import yt_dlp
        except Exception:
            return None
        dest.parent.mkdir(parents=True, exist_ok=True)
        options = {
            "format": "bestaudio/best",
            "proxy": self._proxy or None,
            "outtmpl": str(dest.with_suffix("")),
            "quiet": True,
            "noprogress": True,
            "postprocessors": [
                {"key": "FFmpegExtractAudio", "preferredcodec": "m4a", "preferredquality": "96"}
            ],
        }
        try:
            with yt_dlp.YoutubeDL(options) as downloader:
                downloader.download([WATCH_URL.format(video_id=video_id)])
        except Exception:
            return None
        for path in dest.parent.glob(dest.stem + ".*"):
            if path.suffix.lower() in {".m4a", ".webm", ".opus", ".mp3"}:
                return path
        return None

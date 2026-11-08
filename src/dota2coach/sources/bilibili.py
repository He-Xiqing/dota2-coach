"""B 站公开接口的只读客户端。

设计要点：
- 只调用公开 web 接口，默认不登录；SESSDATA 仅用于可选的官方 AI 摘要。
- 单客户端串行请求，默认 1.2 秒间隔，遇 412 / v_voucher 抛 RiskControl 由上层中止。
- 所有解析函数都是纯函数，便于离线测试。
"""

from __future__ import annotations

import hashlib
import html
import re
import time
import urllib.parse
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any, Protocol

DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
SEARCH_URL = "https://api.bilibili.com/x/web-interface/wbi/search/type"
NAV_URL = "https://api.bilibili.com/x/web-interface/nav"
VIEW_URL = "https://api.bilibili.com/x/web-interface/view"
REPLY_URL = "https://api.bilibili.com/x/v2/reply"
DANMAKU_URL = "https://api.bilibili.com/x/v1/dm/list.so"
PLAYURL_URL = "https://api.bilibili.com/x/player/playurl"
CONCLUSION_URL = "https://api.bilibili.com/x/web-interface/view/conclusion/get"

_EM_RE = re.compile(r"<[^>]+>")
_DURATION_RE = re.compile(r"^(?:(\d+):)?(\d{1,2}):(\d{2})$")

# B 站 wbi 签名用的混淆表（公开算法）
_MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
    27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
    37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
    22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52,
]


def wbi_mixin_key(img_key: str, sub_key: str) -> str:
    raw = img_key + sub_key
    return "".join(raw[index] for index in _MIXIN_KEY_ENC_TAB if index < len(raw))[:32]


def sign_wbi(params: dict[str, Any], img_key: str, sub_key: str, wts: int | None = None) -> dict[str, str]:
    """给请求参数加 wts + w_rid；搜索接口现在必须签名，否则 412。"""
    signed = {str(key): str(value) for key, value in params.items() if value is not None}
    signed["wts"] = str(wts if wts is not None else int(time.time()))
    signed = dict(sorted(signed.items()))
    signed = {
        key: "".join(ch for ch in value if ch not in "!'()*")
        for key, value in signed.items()
    }
    query = urllib.parse.urlencode(signed)
    signed["w_rid"] = hashlib.md5((query + wbi_mixin_key(img_key, sub_key)).encode()).hexdigest()
    return signed


def wbi_keys(payload: dict[str, Any]) -> tuple[str, str]:
    """从 nav 返回里取 img_key / sub_key；取不到返回空串。"""
    data = (payload or {}).get("data") or {}
    wbi = data.get("wbi_img") or {}
    img = str(wbi.get("img_url") or "").rsplit("/", 1)[-1].split(".")[0]
    sub = str(wbi.get("sub_url") or "").rsplit("/", 1)[-1].split(".")[0]
    return img, sub


class BilibiliError(RuntimeError):
    """接口返回不可用（网络、风控、结构变化）。"""


class RiskControl(BilibiliError):
    """命中风控：需要 cookie 或稍后重试。"""


class HttpLike(Protocol):  # pragma: no cover - 仅用于类型提示
    def get(self, url: str, params: dict | None = None, headers: dict | None = None) -> Any: ...


@dataclass(frozen=True)
class Video:
    bvid: str
    aid: int
    title: str
    author: str
    play: int
    danmaku: int
    pubdate: int
    duration: int
    description: str = ""
    tag: str = ""
    cid: int = 0

    @property
    def url(self) -> str:
        return f"https://www.bilibili.com/video/{self.bvid}"

    def search_text(self) -> str:
        return f"{self.title} {self.description} {self.tag}".lower()


@dataclass(frozen=True)
class Comment:
    text: str
    likes: int
    author: str = ""


def strip_em(text: str) -> str:
    """搜索结果标题带 <em class="keyword"> 高亮，去掉标签并反转义。"""
    return html.unescape(_EM_RE.sub("", text or "")).strip()


def parse_duration(text: str) -> int:
    """'12:34' -> 754 秒；'1:02:03' -> 3723；解析失败返回 0。"""
    text = (text or "").strip()
    if text.isdigit():
        return int(text)
    match = _DURATION_RE.match(text)
    if not match:
        return 0
    hours = int(match.group(1) or 0)
    return hours * 3600 + int(match.group(2)) * 60 + int(match.group(3))


def parse_search(payload: dict[str, Any]) -> list[Video]:
    data = (payload or {}).get("data") or {}
    items = data.get("result") or []
    videos: list[Video] = []
    for item in items:
        if not isinstance(item, dict) or item.get("type") != "video":
            continue
        bvid = str(item.get("bvid") or "")
        if not bvid:
            continue
        videos.append(
            Video(
                bvid=bvid,
                aid=int(item.get("aid") or 0),
                title=strip_em(str(item.get("title") or "")),
                author=str(item.get("author") or ""),
                play=int(item.get("play") or 0),
                danmaku=int(item.get("danmaku") or 0),
                pubdate=int(item.get("pubdate") or 0),
                duration=parse_duration(str(item.get("duration") or "")),
                description=strip_em(str(item.get("description") or "")),
                tag=strip_em(str(item.get("tag") or "")),
            )
        )
    return videos


def parse_view(payload: dict[str, Any]) -> dict[str, Any]:
    data = (payload or {}).get("data") or {}
    return {
        "bvid": str(data.get("bvid") or ""),
        "aid": int(data.get("aid") or 0),
        "cid": int(data.get("cid") or 0),
        "title": strip_em(str(data.get("title") or "")),
        "description": strip_em(str(data.get("desc") or "")),
        "pubdate": int(data.get("pubdate") or 0),
        "duration": int(data.get("duration") or 0),
        "author": str((data.get("owner") or {}).get("name") or ""),
        "play": int((data.get("stat") or {}).get("view") or 0),
        "danmaku": int((data.get("stat") or {}).get("danmaku") or 0),
        "tag": strip_em(str(data.get("tname") or "")),
    }


def parse_replies(payload: dict[str, Any], limit: int = 20) -> list[Comment]:
    data = (payload or {}).get("data") or {}
    replies = data.get("replies") or []
    out: list[Comment] = []
    for item in replies[:limit]:
        if not isinstance(item, dict):
            continue
        content = item.get("content") or {}
        message = str(content.get("message") or "").strip()
        if not message:
            continue
        out.append(
            Comment(
                text=strip_em(message),
                likes=int(item.get("like") or 0),
                author=str((item.get("member") or {}).get("uname") or ""),
            )
        )
    return out


def parse_danmaku(xml_text: str, limit: int = 1000) -> list[str]:
    """弹幕 XML：<d p="时间,模式,...">文本</d>。解析失败返回空表。"""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    out: list[str] = []
    for node in root.iter("d"):
        text = (node.text or "").strip()
        if text:
            out.append(text)
        if len(out) >= limit:
            break
    return out


def danmaku_top(items: list[str], top: int = 30, min_count: int = 2) -> list[tuple[str, int]]:
    """统计重复弹幕，过滤单次出现的噪声。"""
    counts: dict[str, int] = {}
    for text in items:
        key = text.strip()
        if 2 <= len(key) <= 30:
            counts[key] = counts.get(key, 0) + 1
    ranked = sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))
    return [pair for pair in ranked if pair[1] >= min_count][:top]


def audio_stream(payload: dict[str, Any]) -> str:
    """从 playurl(fnval=16) 取第一条 DASH 音频地址。"""
    data = (payload or {}).get("data") or {}
    dash = data.get("dash") or {}
    audios = dash.get("audio") or []
    if not audios:
        return ""
    first = audios[0] or {}
    return str(first.get("baseUrl") or first.get("base_url") or "")


class BilibiliClient:
    def __init__(
        self,
        http: HttpLike | None = None,
        *,
        interval: float = 1.2,
        timeout: float = 15.0,
        sessdata: str | None = None,
        sleep=time.sleep,
    ) -> None:
        self._sleep = sleep
        self.interval = interval
        self.sessdata = sessdata
        self._injected = http is not None
        if http is not None:
            self._http = http
        else:  # pragma: no cover - 真实网络
            import httpx

            self._http = httpx.Client(
                timeout=timeout,
                follow_redirects=True,
                headers={"User-Agent": DEFAULT_UA, "Referer": "https://www.bilibili.com/"},
            )
        self._last = 0.0
        self._wbi_keys: tuple[str, str] | None = None
        self._danmaku_failures = 0
        self._danmaku_blocked = False

    def close(self) -> None:  # pragma: no cover - 真实网络
        close = getattr(self._http, "close", None)
        if callable(close):
            close()

    def _throttle(self) -> None:
        now = time.monotonic()
        wait = self.interval - (now - self._last)
        if wait > 0:
            self._sleep(wait)
        self._last = time.monotonic()

    def _headers(self) -> dict[str, str]:
        headers = {"User-Agent": DEFAULT_UA, "Referer": "https://www.bilibili.com/"}
        if self.sessdata:
            headers["Cookie"] = f"SESSDATA={self.sessdata}"
        return headers

    def _get(self, url: str, params: dict | None = None) -> Any:
        self._throttle()
        try:
            response = self._http.get(url, params=params, headers=self._headers())
        except Exception as exc:  # noqa: BLE001 - 网络异常统一转换
            raise BilibiliError(f"请求失败：{exc}") from exc
        status = getattr(response, "status_code", 200)
        if status == 412:
            raise RiskControl("B 站风控 412：请稍后重试或配置 BILIBILI_SESSDATA")
        if status >= 400:
            raise BilibiliError(f"HTTP {status}：{url}")
        return response

    def _json(self, url: str, params: dict | None = None) -> dict[str, Any]:
        response = self._get(url, params)
        try:
            payload = response.json()
        except Exception as exc:  # noqa: BLE001
            raise BilibiliError(f"返回不是 JSON：{exc}") from exc
        if not isinstance(payload, dict):
            raise BilibiliError("返回结构不是对象")
        code = int(payload.get("code") or 0)
        if code == -412:
            raise RiskControl("B 站风控 -412")
        if code != 0:
            raise BilibiliError(f"接口错误 code={code} message={payload.get('message')}")
        return payload

    def _warmup(self) -> None:
        """先访问一次首页拿到 buvid3；没有 cookie 时 nav 会返回 -101 且不给 wbi_img。"""
        if self._injected:  # pragma: no cover - 测试注入的客户端不发真实请求
            return
        try:
            self._http.get("https://www.bilibili.com/", headers=self._headers())
        except Exception:  # noqa: BLE001 - 预热失败不致命，后面会报真正的错
            pass

    def _nav(self) -> dict[str, Any]:
        """nav 未登录时返回 code=-101，但 data 里仍可能带 wbi_img，不能按错误处理。"""
        response = self._get(NAV_URL)
        try:
            payload = response.json()
        except Exception as exc:  # noqa: BLE001
            raise BilibiliError(f"nav 返回不是 JSON：{exc}") from exc
        return payload if isinstance(payload, dict) else {}

    def _wbi(self) -> tuple[str, str]:
        if self._wbi_keys is None:
            keys = ("", "")
            for attempt in range(2):
                if attempt:
                    self._warmup()
                keys = wbi_keys(self._nav())
                if keys[0] and keys[1]:
                    break
            if not (keys[0] and keys[1]):
                raise BilibiliError("取不到 wbi 签名密钥（nav 未返回 wbi_img）")
            self._wbi_keys = keys
        return self._wbi_keys

    def search_videos(self, keyword: str, limit: int = 10) -> list[Video]:
        img_key, sub_key = self._wbi()
        signed = sign_wbi(
            {
                "search_type": "video",
                "keyword": keyword,
                "order": "click",
                "page": 1,
                "page_size": max(1, min(limit, 30)),
            },
            img_key,
            sub_key,
        )
        payload = self._json(SEARCH_URL, signed)
        if payload.get("data", {}).get("v_voucher"):
            raise RiskControl("搜索命中风控（v_voucher 空结果），请稍后再试")
        return parse_search(payload)[:limit]

    def video_info(self, bvid: str) -> Video:
        payload = self._json(VIEW_URL, {"bvid": bvid})
        info = parse_view(payload)
        return Video(
            bvid=info["bvid"] or bvid,
            aid=info["aid"],
            title=info["title"],
            author=info["author"],
            play=info["play"],
            danmaku=info["danmaku"],
            pubdate=info["pubdate"],
            duration=info["duration"],
            description=info["description"],
            tag=info["tag"],
            cid=info["cid"],
        )

    def top_comments(self, aid: int, limit: int = 20) -> list[Comment]:
        payload = self._json(REPLY_URL, {"type": 1, "oid": aid, "sort": 2, "pn": 1, "ps": limit})
        return parse_replies(payload, limit)

    def danmaku(self, cid: int, limit: int = 1000) -> list[str]:
        """弹幕接口风控最严，命中 412 时退避 5 秒重试一次；连续失败两次后本次进程不再尝试。"""
        if self._danmaku_blocked:
            return []
        for attempt in range(2):
            try:
                response = self._get(DANMAKU_URL, {"oid": cid})
                text = getattr(response, "text", "")
                return parse_danmaku(text, limit)
            except RiskControl:
                if attempt:
                    self._danmaku_failures += 1
                    if self._danmaku_failures >= 2:
                        self._danmaku_blocked = True
                    raise
                self._sleep(5.0)
        return []
    def ai_conclusion(self, bvid: str, cid: int, up_mid: int = 0) -> str:
        """官方 AI 摘要，需要 SESSDATA；没有登录态时返回空串。"""
        if not self.sessdata:
            return ""
        try:
            payload = self._json(
                CONCLUSION_URL, {"bvid": bvid, "cid": cid, "up_mid": up_mid}
            )
        except (RiskControl, BilibiliError):
            return ""
        data = payload.get("data") or {}
        model = data.get("model_result") or {}
        summary = str(model.get("summary") or "").strip()
        return strip_em(summary)

    def audio_stream_url(self, bvid: str, cid: int) -> str:
        payload = self._json(
            PLAYURL_URL, {"bvid": bvid, "cid": cid, "fnval": 16, "fourk": 0}
        )
        return audio_stream(payload)

    def download(self, url: str, dest, *, referer: str = "https://www.bilibili.com/") -> int:
        """下载音频到 dest，返回字节数（调用方负责删除）。"""
        self._throttle()
        headers = {"User-Agent": DEFAULT_UA, "Referer": referer}
        response = self._http.get(url, headers=headers)
        status = getattr(response, "status_code", 200)
        if status >= 400:
            raise BilibiliError(f"下载失败 HTTP {status}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        written = 0
        with dest.open("wb") as handle:
            for chunk in response.iter_bytes(1 << 16):
                handle.write(chunk)
                written += len(chunk)
        if written < 1024:
            raise BilibiliError(f"下载内容过小（{written} 字节），可能被风控")
        return written

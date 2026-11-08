from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from .bilibili import Comment, Video, danmaku_top

__all__ = [
    "Evidence",
    "SYSTEM_PROMPT",
    "BUILD_SYSTEM_PROMPT",
    "build_prompt",
    "clean_sentence",
    "extract_build",
    "extract_hero",
    "extract_lane",
    "extract_phase",
    "heuristic_tips",
    "is_guide",
    "matches_patch",
    "merge_tips",
    "patch_key",
    "select_videos",
    "split_sentences",
    "tip_id",
    "trim",
    "validate_builds",
    "validate_tips",
]

MAX_TEXT = 24
MAX_WHY = 40

IMPERATIVE = (
    "先出",
    "别",
    "不要",
    "一定要",
    "必须",
    "记得",
    "优先",
    "早点",
    "马上",
    "直接",
    "多",
    "少",
    "要",
    "可以",
    "尽量",
    "最好",
    "注意",
    "千万别",
    "赶紧",
    "抓",
    "压",
    "换血",
    "补",
)

NOISE_MARKERS = (
    "抽奖",
    "链接",
    "三连",
    "关注",
    "群号",
    "QQ群",
    "qq群",
    "点赞",
    "投币",
    "收藏",
    "私信",
    "广告",
    "优惠",
    "淘宝",
    "礼物",
    "舰长",
    "粉丝",
    "互关",
    "打卡",
    "直播",
)

TOPIC_MARKERS = (
    "攻略",
    "出装",
    "打法",
    "教学",
    "上分",
    "对线",
    "技巧",
    "思路",
    "节奏",
    "加点",
    "第一件",
    "怎么玩",
    "详解",
    "解析",
    "新手",
    "入门",
    "教程",
)

OFFTOPIC = (
    "比赛",
    "赛事",
    "世界赛",
    "TI",
    "解说",
    "集锦",
    "高光",
    "搞笑",
    "主播",
    "选手",
    "直播",
    "转会",
    "战队",
    "吃瓜",
    "娱乐",
    "AME",
    "XG",
    "电竞",
    "新闻",
)

# 社区常用简称 → 内部名（短名以英雄表为准，中文名由 hero_names 提供）
NICKS = {
    "小鱼人": "slark",
    "剑圣": "juggernaut",
    "小黑": "drow_ranger",
    "蓝胖": "ogre_magi",
    "火女": "lina",
    "蓝猫": "storm_spirit",
    "紫猫": "void_spirit",
    "卡尔": "invoker",
    "屠夫": "pudge",
    "白虎": "mirana",
    "大牛": "elder_titan",
    "幽鬼": "spectre",
    "骷髅王": "skeleton_king",
    "毒狗": "shadow_demon",
    "小鹿": "enchantress",
    "先知": "furion",
    "蜘蛛": "broodmother",
    "蚂蚁": "weaver",
    "电魂": "razor",
    "钢背": "bristleback",
    "大鱼人": "slardar",
    "小狗": "life_stealer",
    "拍拍": "ursa",
    "滚滚": "pangolier",
    "大锤": "dawnbreaker",
    "冰女": "crystal_maiden",
    "神牛": "earthshaker",
    "火猫": "ember_spirit",
    "土猫": "earth_spirit",
    "死灵法": "necrolyte",
    "血魔": "bloodseeker",
}


@dataclass(frozen=True)
class Evidence:
    video: Video
    comments: list[Comment]
    danmaku: list[str]
    transcript: str = ""
    ai_summary: str = ""


SYSTEM_PROMPT = """你是 Dota 2 教练知识库的编辑。用户会给你若干条 B 站视频的证据（标题、热评、弹幕、解说转写）。
请提炼成"能直接指挥玩家"的短句，要求：
1. 每条 24 字以内，动宾结构，直接可执行；不要"建议/可以尝试"这类废话。
2. 必须点名英雄；写清是"对线期/中期/后期"。
3. 只写证据里明确出现的内容，不确定就不写；不复述视频标题。
4. 至少 1 条写清"对线期怎么打"：1 级该压还是该苟、几级换血/越线、先出什么小件。
5. 另外用 "builds" 给出装顺序和加点，只能写视频里明确提到的：
   {"hero":"juggernaut","items":["相位鞋","狂战斧","幻影斧"],"skill":"主1副2，有大点大"}
6. 只输出 JSON：{"tips":[...],"builds":[...]}；没有可靠内容就返回空数组。
7. 最多 12 条 tips、最多 1 条 builds；不废话、不复述视频。"""

BUILD_SYSTEM_PROMPT = """你是 Dota 2 出装整理助手。用户会给你一段视频解说转写，只提取里面明确提到的装备和加点。
只输出 JSON：{"items":["中文物品名",...],"skill":"一句话加点"}。
物品名用游戏内中文名（如 黑皇杖/闪烁匕首/幻影斧），不要用 BKB、跳刀这类简称；没有就返回空数组。最多 4 件。"""

ITEM_ALIASES = {
    "bkb": "黑皇杖",
    "a杖": "阿哈利姆神杖",
    "蓝杖": "阿哈利姆神杖",
    "跳刀": "闪烁匕首",
    "飞鞋": "远行鞋",
    "大炮": "代达罗斯之殇",
    "大骨灰": "魂之灵瓮",
    "分身斧": "幻影斧",
    "龙心": "恐鳌之心",
    "撒旦": "撒旦之邪力",
    "冰甲": "希瓦的守护",
    "强袭": "强袭胸甲",
    "莲花": "清莲宝珠",
    "笛子": "洞察烟斗",
    "魔晶": "阿哈利姆魔晶",
    "双刀": "散夜对剑",
    "圣化护符": "圣化护服",
}


def trim(text: str, limit: int) -> str:
    """超长截断，保留 limit-1 个字符再加省略号。"""
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: max(1, limit - 1)] + "…"


def clean_sentence(text: str) -> str:
    """去掉编号/表情/多余标点，留一句干净的话。"""
    text = re.sub(r"^[\s\d、.．)）]+", "", text or "")
    text = re.sub(r"[\s]+", " ", text)
    return text.strip(" \t\r\n。！？，,.!?、;；:：\"'")


def split_sentences(text: str) -> list[str]:
    """按句号切；长句再按逗号/分号切小句（ASR 转写常常没有句号）。"""
    out: list[str] = []
    for chunk in re.split(r"[。！？!?\n]+", text or ""):
        chunk = chunk.strip()
        if not chunk:
            continue
        if len(chunk) <= 40:
            out.append(chunk)
            continue
        for part in re.split(r"[，,；;、]+", chunk):
            part = part.strip()
            if part:
                out.append(part)
    return out


def _aliases(hero_names: dict[str, str] | None) -> dict[str, str]:
    aliases = {local: short for short, local in (hero_names or {}).items() if local}
    aliases.update(NICKS)
    return aliases


def extract_hero(text: str, hero_names: dict[str, str] | None = None) -> str:
    """从一句话里找英雄：先长名后短名，命中返回内部名。"""
    if not text:
        return ""
    names = _aliases(hero_names)
    hits = [(name, short) for name, short in names.items() if name and name in text]
    hits += [(short, short) for short in (hero_names or {}) if short and short in text]
    if not hits:
        return ""
    hits.sort(key=lambda pair: -len(pair[0]))
    return hits[0][1]


def extract_lane(text: str) -> str:
    if "上" in text:
        return "上"
    if "下" in text:
        return "下"
    if "中" in text:
        return "中"
    return "任意"


def extract_phase(text: str) -> str:
    if "对线" in text or "前期" in text or "1 级" in text or "一级" in text:
        return "对线期"
    if "中期" in text or "打架" in text or "节奏" in text:
        return "中期"
    if "后期" in text or "六神" in text:
        return "后期"
    return "任意"


def is_guide(video: Video, hero_names: dict[str, str] | None = None) -> bool:
    """判断是不是"能用的攻略"：标题+标签不能是赛事/集锦，且要像教学。"""
    title_tag = f"{video.title} {video.tag}"
    if any(marker in title_tag for marker in OFFTOPIC):
        return False
    text = f"{title_tag} {video.description}"
    if not any(marker in text for marker in TOPIC_MARKERS):
        return False
    return True


def _has_imperative(text: str) -> bool:
    return any(marker in text for marker in IMPERATIVE)


def _is_noise(text: str) -> bool:
    return any(marker in text for marker in NOISE_MARKERS)


def heuristic_tips(
    evidences: list[Evidence],
    hero_names: dict[str, str],
    max_tips: int = 12,
    min_likes: int = 5,
) -> list[dict]:
    """没有 LLM 时的兜底：从评论/弹幕/转写里挑"点名英雄 + 祈使句"的句子。"""
    out: list[dict] = []
    seen: set[str] = set()

    def add(text: str, video: Video, evidence: str, score: float, likes: int = 0) -> None:
        text = clean_sentence(text)
        hero = extract_hero(text, hero_names)
        if not hero or not _has_imperative(text) or _is_noise(text):
            return
        if evidence in ("comments", "danmaku") and not hero:
            return
        key = f"{hero}|{text}"
        if key in seen:
            return
        seen.add(key)
        out.append(
            {
                "hero": hero,
                "lane": extract_lane(text),
                "phase": extract_phase(text),
                "text": trim(text, MAX_TEXT),
                "why": "",
                "sources": [video.bvid],
                "score": score,
                "evidence": evidence,
                "likes": likes,
            }
        )

    for evidence in evidences:
        for comment in sorted(evidence.comments, key=lambda item: -item.likes):
            if comment.likes < min_likes:
                continue
            add(comment.text, evidence.video, "comments", 1.0, comment.likes)

        counts: dict[str, int] = {}
        for line in evidence.danmaku or []:
            line = line.strip()
            if line and len(line) <= 60:
                counts[line] = counts.get(line, 0) + 1
        for line, count in counts.items():
            if count >= 2:
                add(line, evidence.video, "danmaku", 1.0, count)

        if evidence.transcript:
            for sentence in split_sentences(evidence.transcript):
                if len(sentence) < 6:
                    continue
                add(sentence, evidence.video, "transcript", 1.5)

    out.sort(key=lambda item: (-float(item.get("score") or 0), item.get("text") or ""))
    return out[:max_tips]


def validate_tips(
    raw: list[dict],
    hero_shorts: set[str],
    max_tips: int = 12,
    hero_names: dict[str, str] | None = None,
) -> list[dict]:
    """校验模型输出：英雄名回翻、文本截断、分路/阶段归一化；无法识别英雄的条目保留为通用。"""
    aliases = _aliases(hero_names)
    out: list[dict] = []
    for item in raw or []:
        if not isinstance(item, dict):
            continue
        raw_hero = str(item.get("hero") or "").strip()
        hero = raw_hero.lower()
        if hero not in hero_shorts:
            hero = aliases.get(raw_hero, "") or NICKS.get(raw_hero, "")
        text = trim(clean_sentence(str(item.get("text") or "")), MAX_TEXT)
        if not text:
            continue
        lane = str(item.get("lane") or "任意")
        if lane not in ("上", "中", "下"):
            lane = "任意"
        phase = str(item.get("phase") or "任意")
        if phase not in ("对线期", "中期", "后期", "任意"):
            phase = "任意"
        out.append(
            {
                "hero": hero,
                "lane": lane,
                "phase": phase,
                "text": text,
                "why": trim(str(item.get("why") or ""), MAX_WHY),
            }
        )
        if len(out) >= max_tips:
            break
    return out


def validate_builds(
    raw: list[dict],
    hero_shorts: set[str],
    item_names: set[str],
    *,
    max_items: int = 4,
    hero_names: dict[str, str] | None = None,
) -> list[dict]:
    """校验模型给出的出装/加点，只保留能对上英雄表和中文物品名的内容。"""
    aliases = _aliases(hero_names)
    out: list[dict] = []
    seen: set[str] = set()
    for item in raw or []:
        if not isinstance(item, dict):
            continue
        hero = str(item.get("hero") or "").strip().lower()
        if hero and hero not in hero_shorts:
            hero = aliases.get(str(item.get("hero") or "").strip(), "")
        if not hero or hero in seen:
            continue
        items = [str(name).strip() for name in item.get("items") or [] if str(name).strip() in item_names]
        skill = trim(str(item.get("skill") or ""), 40)
        if not items and not skill:
            continue
        seen.add(hero)
        out.append({"hero": hero, "items": items[:max_items], "skill": skill})
    return out


def extract_build(data: dict, hero_short: str, item_names: set[str], *, max_items: int = 4) -> list[dict]:
    """把"解说提取"的返回值收敛成一条 build，无法对上的物品直接丢弃。"""
    names: list[str] = []
    for raw in data.get("items") or []:
        name = str(raw).strip()
        name = ITEM_ALIASES.get(name.lower(), name)
        if name in item_names and name not in names:
            names.append(name)
    skill = trim(str(data.get("skill") or ""), 40)
    if not names and not skill:
        return []
    return [{"hero": hero_short, "items": names[:max_items], "skill": skill}]


def tip_id(hero: str, text: str) -> str:
    digest = hashlib.sha1(f"{hero}|{text}".encode("utf-8")).hexdigest()
    return digest[:12]


def patch_key(patch: str) -> str:
    return re.sub(r"[a-z]$", "", (patch or "").strip().lower())


def matches_patch(video: Video, patch: str) -> bool:
    key = patch_key(patch)
    return not key or key in video.search_text()


def select_videos(
    videos: list[Video],
    patch: str,
    min_play: int,
    limit: int,
    hero_names: dict[str, str] | None = None,
) -> list[Video]:
    """版本匹配 + 时长/热度/题材过滤 + 按播放排序；同一 bvid 只留一次。"""
    picked: list[Video] = []
    seen: set[str] = set()
    for video in videos:
        if video.bvid in seen:
            continue
        if video.duration < 120 or video.duration > 2400:
            continue
        if video.play < min_play:
            continue
        if not matches_patch(video, patch):
            continue
        if not is_guide(video, hero_names):
            continue
        seen.add(video.bvid)
        picked.append(video)
    picked.sort(key=lambda item: -item.play)
    return picked[:limit]


def merge_tips(tips: list[dict]) -> list[dict]:
    """同一 (hero, text) 的多条证据合并：来源取并集，分数相加，≥2 个来源再 +1。"""
    merged: dict[str, dict] = {}
    for item in tips:
        key = f"{item.get('hero') or ''}|{item.get('text') or ''}"
        if not key.strip("|"):
            continue
        current = merged.get(key)
        if current is None:
            merged[key] = dict(item)
            continue
        sources = set(current.get("sources") or []) | set(item.get("sources") or [])
        current["sources"] = sorted(sources)
        current["score"] = float(current.get("score") or 1.0) + float(item.get("score") or 1.0)
        if len(sources) >= 2:
            current["score"] = float(current["score"]) + 1.0
        if item.get("evidence") == "transcript":
            current["evidence"] = "transcript"
    out = list(merged.values())
    out.sort(key=lambda item: (-float(item.get("score") or 0), item.get("text") or ""))
    for tip in out:
        tip["id"] = tip_id(str(tip.get("hero") or ""), str(tip.get("text") or ""))
        tip["score"] = round(float(tip.get("score") or 1.0), 2)
    return out


def build_prompt(evidence: Evidence, hero_names: dict[str, str], max_chars: int = 4000) -> str:
    video = evidence.video
    parts = [
        f"补丁：{video.tag or ''}",
        f"标题：{video.title}",
        f"简介：{video.description[:300]}",
        "热评：",
    ]
    for comment in sorted(evidence.comments, key=lambda item: -item.likes)[:10]:
        parts.append(f"- [{comment.likes}赞] {comment.text[:120]}")
    if evidence.danmaku:
        parts.append("弹幕高频：" + "；".join(text for text, _ in danmaku_top(evidence.danmaku, top=15)))
    if evidence.ai_summary:
        parts.append("官方摘要：" + evidence.ai_summary[:600])
    if evidence.transcript:
        parts.append("解说转写（关键句优先）：")
        sentences = split_sentences(evidence.transcript)
        if sentences:
            # 祈使句排前面，剩下的按原顺序补齐，避免只塞几句导致模型看不到上下文。
            key = [s for s in sentences if any(marker in s for marker in IMPERATIVE)]
            rest = [s for s in sentences if s not in key]
            body = "。".join(key + rest)
        else:
            body = evidence.transcript
        parts.append(body[: max(0, max_chars - sum(len(p) for p in parts))])
    text = "\n".join(parts)
    return text[:max_chars]

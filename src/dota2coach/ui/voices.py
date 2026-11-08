"""内置语音包：不同的 edge-tts 音色 + 语速/音量预设（按语言分组）。"""

from __future__ import annotations

import re

from dataclasses import dataclass


@dataclass(frozen=True)
class VoicePack:
    id: str
    name: str
    desc: str
    edge: str
    rate: int = 0
    volume: int = 100
    lang: str = "zh-CN"


PACKS: tuple[VoicePack, ...] = (
    # 简体中文
    VoicePack("xiaoxiao", "晓晓 · 温柔女声", "默认，清楚不刺耳", "zh-CN-XiaoxiaoNeural", 0, 100, "zh-CN"),
    VoicePack("xiaoyi", "晓伊 · 活泼女声", "语速稍快，适合快节奏", "zh-CN-XiaoyiNeural", 2, 100, "zh-CN"),
    VoicePack("yunxi", "云希 · 沉稳男声", "偏低沉，适合讲解", "zh-CN-YunxiNeural", -1, 100, "zh-CN"),
    VoicePack("yunjian", "云健 · 激昂男声", "像解说/播报，适合团战", "zh-CN-YunjianNeural", 2, 100, "zh-CN"),
    VoicePack("yunyang", "云扬 · 新闻播报腔", "字正腔圆，正式", "zh-CN-YunyangNeural", 0, 100, "zh-CN"),
    # 其他语言
    VoicePack("zh-tw", "曉臻 · 繁體中文", "台湾中文女声", "zh-TW-HsiaoChenNeural", 0, 100, "zh-TW"),
    VoicePack("aria", "Aria · English", "英语女声，练英文用", "en-US-AriaNeural", 0, 100, "en"),
    VoicePack("fr", "Denise · Français", "法语女声", "fr-FR-DeniseNeural", 0, 100, "fr"),
    VoicePack("ru", "Svetlana · Русский", "俄语女声", "ru-RU-SvetlanaNeural", 0, 100, "ru"),
    VoicePack("de", "Katja · Deutsch", "德语女声", "de-DE-KatjaNeural", 0, 100, "de"),
    VoicePack("pt", "Francisca · Português", "巴西葡语女声", "pt-BR-FranciscaNeural", 0, 100, "pt"),
    VoicePack("es", "Elvira · Español", "西班牙语女声", "es-ES-ElviraNeural", 0, 100, "es"),
    VoicePack("tr", "Emel · Türkçe", "土耳其语女声", "tr-TR-EmelNeural", 0, 100, "tr"),
    VoicePack("custom", "自定义", "使用下面填写的 edge 音色名", "", 0, 100, "zh-CN"),
)

PACK_BY_ID: dict[str, VoicePack] = {pack.id: pack for pack in PACKS}
DEFAULT_PACK = "xiaoxiao"
DEFAULT_EDGE = "zh-CN-XiaoxiaoNeural"
_EDGE_ID = re.compile(r"^[a-z]{2,3}-[A-Za-z]{2,4}-[A-Za-z0-9]+Neural$")


def normalize_edge_voice(raw: str) -> str:
    """把“晓伊”“云健 · 激昂男声”这类显示名还原成 edge 音色 id。"""
    text = (raw or "").strip()
    if not text:
        return DEFAULT_EDGE
    if _EDGE_ID.match(text):
        return text
    head = text.split("·")[0].strip()
    for pack in PACKS:
        if not pack.edge:
            continue
        if head and (head in pack.name or text.startswith(pack.name)):
            return pack.edge
    return DEFAULT_EDGE

# 切换界面语言时优先选的语音包
PACK_FOR_LANGUAGE: dict[str, str] = {
    "zh-CN": "xiaoxiao",
    "zh-TW": "zh-tw",
    "en": "aria",
    "fr": "fr",
    "ru": "ru",
    "de": "de",
    "pt": "pt",
    "es": "es",
    "tr": "tr",
}


def pack_name(pack_id: str) -> str:
    pack = PACK_BY_ID.get(pack_id)
    return pack.name if pack else pack_id


def pack_for_language(language: str) -> str:
    """按界面语言挑一个语音包；未知语言回落到默认中文包。"""
    return PACK_FOR_LANGUAGE.get(language or "", DEFAULT_PACK)


def packs_for_language(language: str) -> tuple[VoicePack, ...]:
    """该语言的语音包（自定义包始终附在最后）。"""
    items = [pack for pack in PACKS if pack.lang == language and pack.id != "custom"]
    custom = PACK_BY_ID["custom"]
    return tuple(items) + (custom,)


def effective_pack(pack_id: str, language: str) -> str:
    """语言换了就让语音包跟着语言走；自定义包保持用户选择。"""
    pack = PACK_BY_ID.get(pack_id)
    if pack is None or pack.id == "custom":
        return pack_id
    if pack.lang != language:
        return pack_for_language(language)
    return pack_id


def resolve(pack_id: str, edge_voice: str, rate: int, volume: int) -> tuple[str, int, int]:
    """返回实际使用的 (edge 音色, 语速, 音量)；自定义包沿用配置里的值。"""
    pack = PACK_BY_ID.get(pack_id)
    if pack is None or pack.id == "custom" or not pack.edge:
        return edge_voice, int(rate), int(volume)
    return pack.edge, pack.rate, pack.volume

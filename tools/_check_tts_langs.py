"""九语言语音合成冒烟：只验证 edge-tts 能出声，不占扬声器。"""

from __future__ import annotations

import asyncio

import edge_tts

from dota2coach.coach.texts import set_language, t
from dota2coach.i18n import LANGUAGES
from dota2coach.ui.voices import effective_pack, resolve
from dota2coach.ui.tts_text import speakable

SAMPLE = {
    "zh-CN": "对线期 · 总经济 6.8k · 战绩 4/1/5",
    "zh-TW": "對線期，正反補 28/4",
    "en": "Laning - net worth 6.8k - KDA 4/1/5",
    "fr": "Phase de ligne, net worth 6.8k",
    "ru": "Лейнинг, нетворс 6.8k",
    "de": "Laning, Networth 6.8k",
    "pt": "Laning, net worth 6.8k",
    "es": "Fase de línea, net worth 6.8k",
    "tr": "Lane aşaması, net worth 6.8k",
}


async def check(lang: str) -> tuple[str, int]:
    pack_id = effective_pack("xiaoxiao", lang)
    voice, rate, _ = resolve(pack_id, "", 0, 100)
    text = speakable(SAMPLE.get(lang, "test"))
    payload = b""
    async for chunk in edge_tts.Communicate(text, voice, rate=f"{rate:+d}%").stream():
        if chunk["type"] == "audio":
            payload += chunk["data"]
    return voice, len(payload)


def main() -> int:
    for lang in LANGUAGES:
        set_language(lang)
        voice, size = asyncio.run(check(lang))
        print(f"{lang:6} {voice:28} {size:7} bytes  {t('item_hand_of_midas')[:40]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

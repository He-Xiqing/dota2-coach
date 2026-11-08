"""从 YouTube 抓攻略（可选；需要能访问 YouTube 的网络或代理）。

用法：
    python scripts/fetch_youtube_guides.py --heroes hoodwink,slark --per-hero 2
    python scripts/fetch_youtube_guides.py --all-heroes --asr base
    HTTPS_PROXY=http://127.0.0.1:7890 python scripts/fetch_youtube_guides.py --heroes slark

说明：
- 搜索不需要 API key，解析的是 youtube.com/results 页面里的 ytInitialData。
- 字幕优先 youtube-transcript-api；没有字幕时用 yt-dlp 下载音频再走 faster-whisper。
- 结果写入 data/guides/<patch>.json（与 B 站攻略合并，不覆盖）。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from dota2coach.config import load_dotenv  # noqa: E402
from dota2coach.sources.asr import Transcriber, asr_available  # noqa: E402
from dota2coach.sources.bilibili import Video  # noqa: E402
from dota2coach.sources.guides_builder import (  # noqa: E402
    Evidence,
    is_guide,
    merge_tips,
    validate_tips,
)
from dota2coach.sources.patch import current_patch  # noqa: E402
from dota2coach.sources.youtube import YtVideo, YouTubeClient, YouTubeError  # noqa: E402
from fetch_guides import llm_tips_for, write_outputs  # noqa: E402

SKIP_WORDS = ("shorts", "clip", "highlights", "funny", "meme")


def load_heroes() -> dict[str, dict]:
    path = ROOT / "data" / "heroes.json"
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return {value["short"]: {"name_loc": value.get("name_loc", value["short"]), **value} for value in data.values()}


def to_video(item: YtVideo, hero: str) -> Video:
    return Video(
        bvid=item.video_id,
        aid=0,
        title=item.title,
        author=item.channel,
        play=item.views,
        danmaku=0,
        pubdate=0,
        duration=item.duration,
        description=item.title,
        tag=hero,
        cid=0,
    )


def pick(videos: list[YtVideo], hero: str, hero_name: str, limit: int, min_views: int) -> list[YtVideo]:
    picked: list[YtVideo] = []
    for item in videos:
        title = item.title.lower()
        if any(word in title for word in SKIP_WORDS):
            continue
        if hero.replace("_", " ") not in title and hero_name.lower() not in title:
            continue
        if item.views < min_views or not 120 <= item.duration <= 3600:
            continue
        picked.append(item)
        if len(picked) >= limit:
            break
    return picked


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="从 YouTube 抓 DOTA2 攻略")
    parser.add_argument("--patch", default="auto", help="版本号，auto 表示自动检测")
    parser.add_argument("--heroes", default="", help="英雄 short 列表，逗号分隔")
    parser.add_argument("--all-heroes", action="store_true", help="处理 data/heroes.json 里的全部英雄")
    parser.add_argument("--per-hero", type=int, default=2, help="每个英雄最多取几个视频")
    parser.add_argument("--min-views", type=int, default=5000, help="最低播放量")
    parser.add_argument("--asr", default="off", choices=["off", "base", "small"], help="无字幕时用 ASR")
    parser.add_argument("--no-llm", action="store_true", help="不用 LLM，只做启发式")
    parser.add_argument("--proxy", default="", help="HTTP 代理，如 http://127.0.0.1:7890")
    parser.add_argument("--out", default="", help="输出目录，默认 data/guides")
    args = parser.parse_args(argv)

    load_dotenv(ROOT / ".env")
    heroes = load_heroes()
    patch = current_patch(cache_path=ROOT / "data" / "patch.json") if args.patch == "auto" else args.patch
    if not patch:
        print("无法确定版本号，请加 --patch 7.41f")
        return 2
    if args.all_heroes:
        targets = sorted(heroes)
    elif args.heroes:
        targets = [name.strip() for name in args.heroes.split(",") if name.strip()]
    else:
        print("请用 --heroes 或 --all-heroes 指定英雄")
        return 2

    llm = None
    if not args.no_llm:
        from dota2coach.llm.client import LlmClient

        llm = LlmClient()
        if not llm.available:
            print("DEEPSEEK_API_KEY 未设置：改用启发式（--no-llm）")
            llm = None

    translator = None
    if args.asr != "off":
        if not asr_available():
            print("未安装 faster-whisper：跳过 ASR")
        else:
            translator = Transcriber(model=args.asr)

    client = YouTubeClient(proxy=args.proxy)
    out_dir = Path(args.out) if args.out else ROOT / "data" / "guides"
    hero_names = {short: info.get("name_loc", short) for short, info in heroes.items()}
    all_tips: list[dict] = []
    all_videos: list[dict] = []
    builds: list[dict] = []

    for index, short in enumerate(targets, start=1):
        info = heroes.get(short)
        if not info:
            print(f"[{index}/{len(targets)}] 跳过未知英雄 {short}")
            continue
        name_loc = info.get("name_loc", short)
        query = f"DOTA2 {name_loc} guide {patch}"
        try:
            found = client.search(query, limit=12)
        except YouTubeError as exc:
            print(f"[{index}/{len(targets)}] {name_loc}：{exc}")
            break
        chosen = pick(found, short, name_loc, args.per_hero, args.min_views)
        print(f"[{index}/{len(targets)}] {name_loc}：搜到 {len(found)}，采用 {len(chosen)}")
        evidences = []
        for item in chosen:
            transcript = client.transcript(item.video_id, languages=("en",))
            if not transcript and translator is not None:
                audio = client.download_audio(item.video_id, ROOT / "data" / "guides" / "audio" / f"{item.video_id}.m4a")
                if audio:
                    transcript = translator.transcribe(str(audio))
            if not transcript:
                print(f"  - 跳过（无字幕/无法转写）：{item.title[:40]}")
                continue
            video = to_video(item, name_loc)
            evidences.append(Evidence(video=video, comments=[], danmaku=[], transcript=transcript, ai_summary=""))
            all_videos.append(
                {
                    "bvid": video.bvid,
                    "title": video.title,
                    "author": video.author,
                    "play": video.play,
                    "pubdate": video.pubdate,
                    "url": f"https://www.youtube.com/watch?v={video.bvid}",
                }
            )
        if not evidences:
            continue
        tips: list[dict] = []
        hero_builds: list[dict] = []
        if llm is not None:
            for evidence in evidences:
                one_tips, one_builds = llm_tips_for(
                    llm, evidence, hero_names, args.per_hero, target_short=short
                )
                tips.extend(one_tips)
                hero_builds.extend(one_builds)
        if not tips and not args.no_llm:
            print("  - LLM 没给出可用提示")
        tips = validate_tips(tips, set(heroes), max_tips=4, hero_names=hero_names)
        all_tips = merge_tips(all_tips + tips)
        builds.extend(hero_builds)

    if not all_tips and not builds:
        print("没有可写入的攻略（检查网络/代理或换关键词）")
        return 1
    path = write_outputs(
        out_dir,
        patch,
        all_videos,
        all_tips,
        llm=llm is not None,
        asr=args.asr,
        hero_names=hero_names,
        builds=builds,
    )
    print(f"完成：{len(all_tips)} 条提示 -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

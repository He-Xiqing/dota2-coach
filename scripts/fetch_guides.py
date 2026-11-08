"""抓取 B 站当前版本攻略，生成 data/guides/<patch>.json。

用法：
    python scripts\\fetch_guides.py                 # L1：元数据 + 评论 + 弹幕
    python scripts\\fetch_guides.py --asr base      # + 音频转写（需 faster-whisper）
    python scripts\\fetch_guides.py --no-llm        # 强制启发式
    python scripts\\fetch_guides.py --dry-run       # 只打印不做网络请求
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dota2coach.config import load_dotenv  # noqa: E402
from dota2coach.sources.asr import Transcriber, asr_available  # noqa: E402
from dota2coach.sources.bilibili import (  # noqa: E402
    BilibiliClient,
    BilibiliError,
    RiskControl,
    Video,
)
from dota2coach.sources.guides_builder import (  # noqa: E402
    SYSTEM_PROMPT,
    Evidence,
    build_prompt,
    extract_hero,
    heuristic_tips,
    is_guide,
    merge_tips,
    patch_key,
    select_videos,
    validate_builds,
    validate_tips,
)
from dota2coach.sources.guides_builder import BUILD_SYSTEM_PROMPT, extract_build  # noqa: E402
from dota2coach.sources.patch import current_patch  # noqa: E402
KEYWORDS = (
    "DOTA2 {patch} 英雄攻略",
    "DOTA2 {patch} 出装 教学",
    "DOTA2 {patch} 对线 技巧",
    "DOTA2 {patch} 上分 思路",
)


def _show(text: str) -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("gbk", "replace").decode("gbk", "replace"))


def load_hero_names(path: Path) -> tuple[dict[str, str], set[str]]:
    raw = json.loads(path.read_text(encoding="utf-8-sig"))
    names: dict[str, str] = {}
    for item in raw.values() if isinstance(raw, dict) else raw:
        if not isinstance(item, dict):
            continue
        short = str(item.get("short") or "")
        local = str(item.get("name_loc") or "")
        if short:
            names[short] = local
    return names, set(names)


def _field(item, key: str, default=None):
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def load_existing(path: Path) -> tuple[list[dict], list[dict]]:
    """读回上一次的 tips/videos，保证断点续跑时不丢数据。"""
    if not path.exists():
        return [], []
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return [], []
    tips = [item for item in payload.get("tips") or [] if isinstance(item, dict)]
    videos = [item for item in payload.get("videos") or [] if isinstance(item, dict)]
    return tips, videos


def covered_heroes(tips: list[dict]) -> set[str]:
    return {str(item.get("hero") or "") for item in tips if item.get("hero")}


def search_one(
    client: BilibiliClient,
    name_loc: str,
    patch: str,
    *,
    min_play: int,
    used: set[str],
    hero_names: dict[str, str],
    short: str = "",
) -> Video | None:
    """给一个英雄找一个最像攻略的视频。"""
    keywords = (
        f"{name_loc} DOTA2 {patch} 出装",
        f"{name_loc} {patch} 攻略",
        f"{name_loc} dota2 教学",
    )
    import re

    def wrong_patch(video: Video) -> bool:
        text = f"{video.title} {video.tag}"
        for match in re.finditer(r"7\.\d{1,2}[a-z]?", text):
            if patch_key(match.group(0)) != patch_key(patch):
                return True
        return False

    for keyword in keywords:
        for attempt in range(2):
            try:
                videos = client.search_videos(keyword, limit=20)
                break
            except RiskControl as exc:
                if attempt:
                    _show(f"  [风控] {name_loc}：{exc}")
                    videos = []
                    break
                _show("  搜索命中风控，等 60 秒…")
                client._sleep(60.0)  # noqa: SLF001
            except BilibiliError as exc:
                _show(f"  搜索失败（{keyword}）：{exc}")
                videos = []
                break
        for video in videos:
            if video.play < min_play:
                continue
            # duration=0 表示接口没给，按未知放过
            if video.duration and not (60 <= video.duration <= 3600):
                continue
            head = f"{video.title} {video.tag}"
            text = f"{head} {video.description}"
            if name_loc and name_loc not in head:
                continue
            # 同一个视频被别的英雄用过时，只有标题里明确提到本英雄才复用
            if video.bvid in used and (not name_loc or name_loc not in head):
                continue
            # 排除"剧毒术士"当成"术士"这类包含关系误命中
            if any(
                other != name_loc and name_loc in other and other in head
                for other in hero_names.values()
            ):
                continue
            # 标题里本英雄必须是最先出现的英雄名（避免"斧王…随便主宰对线"这类借用词）
            title_pos = video.title.find(name_loc)
            if title_pos > 0:
                for other_short, other_loc in hero_names.items():
                    if other_short == short or not other_loc or other_loc == name_loc:
                        continue
                    other_pos = video.title.find(other_loc)
                    if 0 <= other_pos < title_pos:
                        subject_ok = False
                        break
                else:
                    subject_ok = True
                if not subject_ok:
                    continue
            # 必须真是 Dota 内容（避免"工程师"命中 F1 视频这种）
            low = text.lower()
            if not ("dota" in low or "刀塔" in text or "moba" in low):
                continue
            if wrong_patch(video):
                continue
            if not is_guide(video, hero_names):
                continue
            return video
    return None


def llm_tips_for(
    llm,
    evidence: Evidence,
    hero_names: dict[str, str],
    per_video: int,
    target_short: str = "",
    item_names: set[str] | None = None,
) -> tuple[list[dict], list[dict]]:
    try:
        data = llm.chat_json(SYSTEM_PROMPT, build_prompt(evidence, hero_names))
    except Exception as exc:  # noqa: BLE001
        _show(f"  [llm] 失败：{exc}")
        return [], []
    got: list[dict] = []
    for item in data.get("tips") or []:
        if not isinstance(item, dict):
            continue
        item = dict(item)
        hero = str(item.get("hero") or "").strip()
        # 视频就是给这个英雄找的：模型没写英雄、或写的是昵称别名，都归到这个英雄名下
        if target_short and hero not in hero_names:
            item["hero"] = target_short
        item["sources"] = [evidence.video.bvid]
        item["evidence"] = "llm"
        item["score"] = 2.0
        got.append(item)
    builds: list[dict] = []
    if item_names:
        builds = validate_builds(
            data.get("builds") or [],
            set(hero_names),
            item_names,
            hero_names=hero_names,
        )
        # 主提示词常忽略 builds：单独问一次“解说里出了什么装”，能多捞回不少
        if not builds and target_short:
            source_text = evidence.transcript or "。".join(
                comment.text for comment in evidence.comments[:20]
            )
            if source_text:
                try:
                    payload = llm.chat_json(
                        BUILD_SYSTEM_PROMPT, "解说文本：\n" + source_text[:3500]
                    )
                    builds = extract_build(payload, target_short, item_names)
                except Exception as exc:  # noqa: BLE001
                    _show(f"  [builds] 失败：{exc}")
        for build in builds:
            build["sources"] = [evidence.video.bvid]
    return got[:per_video], builds


def run_all_heroes(
    client: BilibiliClient,
    llm,
    hero_names: dict[str, str],
    hero_order: list[tuple[str, str]],
    hero_shorts: set[str],
    patch: str,
    args,
    guides_dir: Path,
    transcriber,
    item_names: list[str],
    existing_tips: list[dict],
    existing_videos: list[dict],
    existing_builds: list[dict] | None = None,
) -> int:
    out_path = guides_dir / f"{patch or 'unknown'}.json"
    tips = list(existing_tips)
    videos = list(existing_videos)
    builds = list(existing_builds or [])
    used = {str(_field(video, "bvid", "")) for video in videos}
    done = covered_heroes(tips)
    todo = [(short, name) for short, name in hero_order if short not in done]
    _show(f"全英雄模式：已覆盖 {len(done)} 个，本次处理 {len(todo)} 个")
    if not todo:
        return 0

    for index, (short, name_loc) in enumerate(todo, 1):
        _show(f"[{index}/{len(todo)}] {name_loc} ({short})")
        video = search_one(
            client,
            name_loc,
            patch,
            min_play=args.hero_min_play,
            used=used,
            hero_names=hero_names,
            short=short,
        )
        if video is None:
            _show("  没找到合适的视频，跳过")
            continue
        _show(f"  {video.title}（{video.play} 播放）")
        evidence = collect_evidence(client, video, with_danmaku=not args.no_danmaku, use_ai=False)
        if transcriber is not None and args.asr_max_videos > 0 and index <= args.asr_max_videos:
            evidence = maybe_transcribe(
                client,
                evidence,
                transcriber,
                asr_dir=ROOT / "logs" / "asr",
                transcript_dir=guides_dir / "transcripts",
                hero_names=hero_names,
                item_names=item_names,
            )
        got: list[dict] = []
        new_builds: list[dict] = []
        if llm is not None:
            got, new_builds = llm_tips_for(
                llm,
                evidence,
                hero_names,
                per_video=args.per_hero_tips,
                target_short=short,
                item_names=set(item_names),
            )
        if new_builds:
            by_hero = {str(build.get("hero") or ""): build for build in builds}
            for build in new_builds:
                by_hero[str(build.get("hero") or "")] = build
            builds = list(by_hero.values())
        validated = validate_tips(got, hero_shorts, max_tips=args.per_hero_tips, hero_names=hero_names)
        if not validated:
            _show("  LLM 没有给出可用提示")
        tips.extend(validated)
        videos.append(video)
        used.add(video.bvid)
        tips = merge_tips(tips)
        write_outputs(
            guides_dir,
            patch,
            videos,
            tips,
            llm=llm is not None,
            asr=args.asr,
            hero_names=hero_names,
            json_path=out_path,
            builds=builds,
        )
    return 0


def collect_evidence(
    client: BilibiliClient,
    video: Video,
    *,
    with_danmaku: bool,
    use_ai: bool,
) -> Evidence:
    info = video
    try:
        info = client.video_info(video.bvid)
    except BilibiliError as exc:
        _show(f"  [view] {video.bvid} 失败：{exc}")
    comments = []
    try:
        comments = client.top_comments(info.aid or video.aid, limit=20)
    except BilibiliError as exc:
        _show(f"  [reply] {video.bvid} 失败：{exc}")
    danmaku: list[str] = []
    if with_danmaku and info.cid:
        try:
            danmaku = client.danmaku(info.cid, limit=1000)
        except BilibiliError as exc:
            _show(f"  [dm] {video.bvid} 失败：{exc}")
    summary = ""
    if use_ai and info.cid:
        summary = client.ai_conclusion(info.bvid, info.cid)
    return Evidence(video=info, comments=comments, danmaku=danmaku, ai_summary=summary)


def maybe_transcribe(
    client: BilibiliClient,
    evidence: Evidence,
    transcriber: Transcriber | None,
    *,
    asr_dir: Path,
    transcript_dir: Path,
    hero_names: dict[str, str],
    item_names: list[str],
) -> Evidence:
    if transcriber is None or evidence.ai_summary or not evidence.video.cid:
        return evidence
    cached = transcript_dir / f"{evidence.video.bvid}.txt"
    if cached.exists():
        try:
            text = cached.read_text(encoding="utf-8")
        except OSError:
            text = ""
        if text.strip():
            _show(f"  [asr] 复用本地转写稿 {len(text)} 字")
            return Evidence(
                video=evidence.video,
                comments=evidence.comments,
                danmaku=evidence.danmaku,
                transcript=text,
                ai_summary=evidence.ai_summary,
            )
    try:
        url = client.audio_stream_url(evidence.video.bvid, evidence.video.cid)
    except BilibiliError as exc:
        _show(f"  [playurl] {evidence.video.bvid} 失败：{exc}")
        return evidence
    if not url:
        _show(f"  [playurl] {evidence.video.bvid} 没有音频流")
        return evidence
    audio = asr_dir / f"{evidence.video.bvid}.m4a"
    started = time.monotonic()
    try:
        size = client.download(url, audio)
        _show(f"  [asr] 下载 {size / 1048576:.1f}MB → 转写中…")
        prompt = transcriber.hotwords_prompt(list(hero_names.values()), item_names)
        text = transcriber.transcribe(audio, initial_prompt=prompt)
        transcript_dir.mkdir(parents=True, exist_ok=True)
        (transcript_dir / f"{evidence.video.bvid}.txt").write_text(text, encoding="utf-8")
        _show(f"  [asr] 完成 {len(text)} 字，用时 {time.monotonic() - started:.0f}s")
        return Evidence(
            video=evidence.video,
            comments=evidence.comments,
            danmaku=evidence.danmaku,
            transcript=text,
            ai_summary=evidence.ai_summary,
        )
    except Exception as exc:  # noqa: BLE001 - 单个视频失败不影响整批
        _show(f"  [asr] {evidence.video.bvid} 失败：{exc}")
        return evidence
    finally:
        try:
            audio.unlink(missing_ok=True)
        except OSError:
            pass


def write_outputs(
    out_dir: Path,
    patch: str,
    videos: list,
    tips: list[dict],
    llm: bool,
    asr: str,
    hero_names: dict[str, str] | None = None,
    json_path: Path | None = None,
    builds: list[dict] | None = None,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = json_path or (out_dir / f"{patch or 'unknown'}.json")
    # 定时任务可能只跑少量视频；先合并旧数据，避免把已覆盖的英雄冲掉
    old_tips, old_videos = load_existing(json_path)
    old_builds: list[dict] = []
    if json_path.exists():
        try:
            old_builds = list(json.loads(json_path.read_text(encoding="utf-8-sig")).get("builds") or [])
        except (OSError, json.JSONDecodeError):
            old_builds = []
    merged_builds: dict[str, dict] = {}
    for item in old_builds + list(builds or []):
        key = str(item.get("hero") or "")
        if key:
            merged_builds[key] = item
    if old_tips:
        merged: dict[str, dict] = {}
        for item in old_tips + tips:
            key = str(item.get("id") or "")
            if key:
                merged[key] = item
        tips = list(merged.values())
    normalized = [
        {
            "bvid": _field(video, "bvid", ""),
            "title": _field(video, "title", ""),
            "author": _field(video, "author", ""),
            "play": _field(video, "play", 0),
            "pubdate": _field(video, "pubdate", 0),
            "url": _field(video, "url", ""),
        }
        for video in videos
    ]
    seen = {item["bvid"] for item in normalized}
    for item in old_videos or []:
        bvid = str(item.get("bvid") or "")
        if bvid and bvid not in seen:
            normalized.append(item)
            seen.add(bvid)
    payload = {
        "patch": patch,
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "llm": llm,
        "asr": asr,
        "videos": normalized,
        "tips": tips,
        "builds": list(merged_builds.values()),
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    display = dict(hero_names or {})
    lines = [f"# {patch or '未知版本'} 攻略摘要", "", f"生成时间：{payload['generated_at']}", ""]
    for tip in tips:
        hero_short = tip.get("hero") or ""
        hero = display.get(hero_short, hero_short) or "通用"
        lines.append(f"- **{hero}**（{tip.get('lane')}/{tip.get('phase')}）：{tip.get('text')}")
    lines.append("")
    lines.append("来源：")
    for video in videos:
        lines.append(
            f"- [{_field(video, 'title', '')}]({_field(video, 'url', '')}) · "
            f"{_field(video, 'author', '')} · 播放 {_field(video, 'play', 0)}"
        )
    (out_dir / f"{patch or 'unknown'}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    index_path = out_dir / "index.json"
    index = {"latest": patch, "files": []}
    if index_path.exists():
        try:
            index = json.loads(index_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            pass
    files = set(index.get("files") or [])
    files.add(f"{patch or 'unknown'}.json")
    index["latest"] = patch
    index["files"] = sorted(files)
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    return json_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="抓取 B 站当前版本 DOTA2 攻略")
    parser.add_argument("--patch", default="auto", help="版本号，auto=从 Steam 新闻取")
    parser.add_argument("--limit", type=int, default=6, help="最多几个视频")
    parser.add_argument("--min-play", type=int, default=30000)
    parser.add_argument("--no-llm", action="store_true", help="不用 DeepSeek，走启发式")
    parser.add_argument("--asr", choices=("off", "base", "small"), default="off", help="音频转写模型")
    parser.add_argument("--asr-max-videos", type=int, default=3)
    parser.add_argument("--max-tips", type=int, default=12)
    parser.add_argument("--no-danmaku", action="store_true")
    parser.add_argument("--bvid", action="append", default=[], help="直接指定视频 BV 号（可重复），跳过搜索")
    parser.add_argument("--all-heroes", action="store_true", help="全英雄覆盖：逐个英雄搜一个攻略视频（断点续跑）")
    parser.add_argument("--per-hero-tips", type=int, default=3, help="全英雄模式下每个英雄最多几条提示")
    parser.add_argument("--hero-min-play", type=int, default=5000, help="全英雄模式的播放量下限")
    parser.add_argument("--heroes", default="", help="只处理这些英雄（short 名，逗号分隔，调试用）")
    parser.add_argument("--dry-run", action="store_true", help="只打印计划，不写文件")
    parser.add_argument("--check-key", action="store_true", help="只检查 DeepSeek key 是否可用")
    args = parser.parse_args(argv)

    try:
        sys.stdout.reconfigure(errors="replace")  # 控制台是 GBK 时只替换不能编码的字，别强转 UTF-8
    except (AttributeError, ValueError):
        pass
    load_dotenv(ROOT / ".env")
    key = (os.environ.get("DEEPSEEK_API_KEY") or "").strip()
    hint = "未设置"
    if key:
        hint = f"已设置（长度 {len(key)}，前缀 {key[:3]}…；正常 sk- 开头、35 位左右）"
    _show(f".env：{'已找到' if (ROOT / '.env').exists() else '不存在'}；DEEPSEEK_API_KEY：{hint}")
    env_path = ROOT / ".env"
    if env_path.exists():
        stat = env_path.stat()
        _show(f".env 修改时间：{datetime.fromtimestamp(stat.st_mtime):%Y-%m-%d %H:%M:%S}，大小 {stat.st_size} 字节")
    if args.check_key:
        from dota2coach.llm.client import LlmClient  # 局部导入：不检查 key 时少一次依赖

        _show(f"key 检查：{LlmClient().ping()}")
        return 0
    data_dir = ROOT / "data"
    guides_dir = data_dir / "guides"
    hero_names, hero_shorts = load_hero_names(data_dir / "heroes.json")
    item_names: list[str] = []
    item_path = data_dir / "item_names_zh.json"
    if item_path.exists():
        try:
            item_names = list(json.loads(item_path.read_text(encoding="utf-8-sig")).values())
        except (OSError, json.JSONDecodeError):
            item_names = []

    patch = args.patch
    if patch == "auto":
        patch = current_patch(data_dir / "patch.json")
    if not patch:
        _show("取不到版本号：加 --patch 7.41f 再试")
        return 2
    _show(f"版本：{patch}（匹配 {patch_key(patch)}）")

    llm = None
    if not args.no_llm:
        from dota2coach.llm.client import LlmClient

        llm = LlmClient()
        if not llm.available:
            _show("未配置 DEEPSEEK_API_KEY，改用启发式摘要")
            llm = None

    transcriber = None
    if args.asr != "off":
        if not asr_available():
            _show("未安装 faster-whisper，跳过转写（scripts\\setup_asr.ps1）")
        else:
            transcriber = Transcriber(args.asr, model_dir=ROOT / "logs" / "models")
            _show(f"转写模型：{args.asr}（前 {args.asr_max_videos} 个视频）")
    if llm is not None:
        _show(f"LLM：{llm.model}")

    if args.dry_run:
        _show(f"[dry-run] 关键词：{[k.format(patch=patch) for k in KEYWORDS]}")
        _show(f"[dry-run] 计划抓 {args.limit} 个视频，min_play={args.min_play}，asr={args.asr}")
        return 0

    sessdata = os.environ.get("BILIBILI_SESSDATA", "").strip() or None
    client = BilibiliClient(sessdata=sessdata)
    try:
        if args.all_heroes:
            hero_order = sorted(
                (
                    (str(item.get("short")), str(item.get("name_loc") or item.get("short")))
                    for item in json.loads(
                        (data_dir / "heroes.json").read_text(encoding="utf-8-sig")
                    ).values()
                    if isinstance(item, dict) and item.get("short")
                ),
                key=lambda pair: pair[1],
            )
            if args.heroes.strip():
                wanted = {part.strip() for part in args.heroes.split(",") if part.strip()}
                hero_order = [
                    pair
                    for pair in hero_order
                    if pair[0] in wanted or pair[1] in wanted
                ]
            existing_tips, existing_videos = load_existing(guides_dir / f"{patch or 'unknown'}.json")
            existing_builds: list[dict] = []
            current = guides_dir / f"{patch or 'unknown'}.json"
            if current.exists():
                try:
                    existing_builds = list(json.loads(current.read_text(encoding="utf-8-sig")).get("builds") or [])
                except (OSError, json.JSONDecodeError):
                    existing_builds = []
            return run_all_heroes(
                client,
                llm,
                hero_names,
                hero_order,
                hero_shorts,
                patch,
                args,
                guides_dir,
                transcriber,
                item_names,
                existing_tips,
                existing_videos,
                existing_builds,
            )
        found: list[Video] = []
        if args.bvid:
            for bvid in args.bvid:
                try:
                    found.append(client.video_info(bvid))
                except BilibiliError as exc:
                    _show(f"取视频失败（{bvid}）：{exc}")
            picked = found[: args.limit]
        for template in KEYWORDS if not args.bvid else ():
            keyword = template.format(patch=patch)
            for attempt in range(2):
                try:
                    found.extend(client.search_videos(keyword, limit=10))
                    break
                except RiskControl as exc:
                    if attempt:
                        _show(f"风控中止：{exc}（等几分钟再试）")
                        return 2
                    _show("搜索命中风控，等 60 秒重试…")
                    client._sleep(60.0)  # noqa: SLF001 - 脚本里简单退避
                except BilibiliError as exc:
                    _show(f"搜索失败（{keyword}）：{exc}")
                    break
        if not args.bvid:
            picked = select_videos(found, patch, args.min_play, args.limit, hero_names)
        _show(f"候选 {len(found)} 个，入选 {len(picked)} 个")
        if not picked:
            _show("没有匹配版本且热度达标的视频，稍后再试或加 --patch 指定版本")
            return 1

        evidences: list[Evidence] = []
        for index, video in enumerate(picked):
            _show(f"[{index + 1}/{len(picked)}] {video.title}（{video.play} 播放）")
            evidence = collect_evidence(
                client,
                video,
                with_danmaku=not args.no_danmaku,
                use_ai=bool(sessdata),
            )
            if transcriber is not None and index < args.asr_max_videos:
                evidence = maybe_transcribe(
                    client,
                    evidence,
                    transcriber,
                    asr_dir=ROOT / "logs" / "asr",
                    transcript_dir=guides_dir / "transcripts",
                    hero_names=hero_names,
                    item_names=item_names,
                )
            evidences.append(evidence)

        tips: list[dict] = []
        llm_failures = 0
        per_video = max(3, args.max_tips // max(1, min(3, len(evidences))))
        if llm is not None:
            for evidence in evidences[:3]:
                try:
                    data = llm.chat_json(SYSTEM_PROMPT, build_prompt(evidence, hero_names))
                except Exception as exc:  # noqa: BLE001
                    llm_failures += 1
                    _show(f"  [llm] 失败：{exc}")
                    continue
                got = []
                for item in data.get("tips") or []:
                    if isinstance(item, dict):
                        item = dict(item)
                        item["sources"] = [evidence.video.bvid]
                        item["evidence"] = "llm"
                        item["score"] = 2.0
                        got.append(item)
                # 每个视频限量，避免第一个视频把 max_tips 名额吃光
                tips.extend(got[:per_video])
        if llm is not None and llm_failures == min(3, len(evidences)):
            _show("  [llm] 全部失败：请检查 .env 里的 DEEPSEEK_API_KEY 是否有效（或换成新的 key），"
                  "本次退回启发式，质量会差很多")
        tips.extend(heuristic_tips(evidences, hero_names, max_tips=args.max_tips * 2))
        tips = validate_tips(tips, hero_shorts, max_tips=args.max_tips, hero_names=hero_names)
        tips = merge_tips(tips)
    finally:
        client.close()

    display_names = dict(hero_names)
    path = write_outputs(guides_dir, patch, picked, tips, llm=llm is not None, asr=args.asr, hero_names=hero_names)
    _show(f"完成：{len(tips)} 条提示 → {path}")
    for tip in tips[:5]:
        hero_short = tip.get("hero") or ""
        hero = display_names.get(hero_short, hero_short) or "通用"
        _show(f"  · {hero}：{tip.get('text')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""命令行入口：python -m dota2coach [--probe]"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="dota2coach",
        description="Dota 2 实时教练（外部 Overlay，基于官方 GSI + 屏幕识别）",
    )
    parser.add_argument("--probe", action="store_true", help="无界面模式：只验证 GSI 并把报文写入 logs/")
    parser.add_argument("--duration", type=float, default=None,
                        help="探针自动退出前运行的秒数（用于冒烟测试，正常使用不要加）")
    parser.add_argument("--screenshot", type=Path, default=None,
                        help="用一张截图代替实时截屏（离线调试界面用）")
    parser.add_argument("--snapshot", type=Path, default=None,
                        help="用一份 GSI JSON 快照代替实时报文（离线调试界面用）")
    parser.add_argument("--seconds", type=float, default=None,
                        help="界面模式下自动退出的秒数（冒烟测试用）")
    parser.add_argument("--save-overlay", type=Path, default=None,
                        help="渲染后把卡片存成 PNG（冒烟测试用）")
    parser.add_argument("--config", type=Path, default=None, help="指定 config.toml 路径")
    parser.add_argument("--test-voice", action="store_true", help="测试语音与提示音，打印各后端结果")
    parser.add_argument(
        "--test-sound",
        nargs="?",
        const="chime",
        choices=["chime", "urgent"],
        default=None,
        help="只播放一次提示音（chime 普通 / urgent 紧急）",
    )
    parser.add_argument("--update-guides", action="store_true", help="更新 B 站攻略库（每周自动跑一次）")
    parser.add_argument("--prune-guides", action="store_true", help="只清理攻略库里的旧条目和垃圾")
    parser.add_argument("--legacy", action="store_true", help="只显示置顶卡片，不打开主窗口（打包出的卡片版 exe 用）")
    parser.add_argument("--version", action="store_true", help="打印版本号")
    return parser.parse_args(argv)


def _show(text: str) -> None:
    """控制台是 GBK 时，打印含替换字符的异常文本不至于崩溃。"""
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "gbk"
        print(text.encode(encoding, "replace").decode(encoding, "replace"))


def _test_voice(cfg) -> int:
    """逐项检查语音链路：SAPI 能否枚举/发声、提示音能否播放、回退是否生效。"""
    from .ui.voice import Speaker

    voice = cfg.voice
    print(
        "语音配置: enabled={} speak={} beep={} rate={} volume={}".format(
            voice.enabled, voice.speak, voice.beep, voice.rate, voice.volume
        )
    )
    speaker = Speaker(
        enabled=voice.enabled,
        speak=voice.speak,
        backend=voice.backend,
        edge_voice=voice.edge_voice,
        rate=voice.rate,
        volume=voice.volume,
        min_interval=voice.min_interval,
        beep=voice.beep,
        log_path=cfg.log_dir / "voice.log",
    )
    print(f"朗读后端: {speaker.backend}")
    print(f"后端偏好: {voice.backend}  在线朗读(edge-tts)可用: {speaker.edge_available}")
    if speaker.last_error:
        print(f"初始化问题: {speaker.last_error}")
    if speaker._voice is not None:  # noqa: SLF001 - 自检命令，直接看内部状态
        try:
            tokens = speaker._voice.GetVoices()  # noqa: SLF001
            print(f"SAPI 音色数: {tokens.Count}")
            for index in range(tokens.Count):
                print(f"  [{index}] {tokens.Item(index).GetDescription()}")
        except Exception as exc:  # noqa: BLE001
            _show(f"音色枚举失败: {exc}")

    print("正在尝试发声：正常时应先听到提示音，再听到“语音测试…”")
    speaker.say("语音测试：听到这句话说明朗读正常", force=True)
    speaker.wait(10.0)
    _show(f"发声后状态: backend={speaker.backend} last_error={speaker.last_error or '无'}")
    ps_log = cfg.log_dir / "voice_ps.log"
    if ps_log.exists():
        try:
            lines = ps_log.read_text(encoding="utf-8", errors="replace").strip().splitlines()
            for line in lines[-5:]:
                _show(f"  {line}")
        except Exception:  # noqa: BLE001
            pass
    print(f"日志: {cfg.log_dir / 'voice.log'}")
    print("如果没听到声音：把上面几行和 logs\\voice.log、logs\\voice_ps.log 一起发我。")
    return 0


def _hero_shorts(cfg) -> set[str]:
    from .vision.heroes import load_hero_table

    table = load_hero_table(cfg.vision.heroes_json)
    return {hero.short for hero in table.values()}


def _prune_guides(cfg) -> int:
    from .sources.prune import prune_file

    shorts = _hero_shorts(cfg)
    total = 0
    for path in sorted(cfg.guides.dir.glob("*.json")):
        if path.name == "index.json":
            continue
        try:
            stats = prune_file(path, shorts)
        except (OSError, ValueError) as exc:
            print(f"清理失败 {path.name}: {exc}")
            continue
        total += stats.get("dropped_garbage", 0) + stats.get("dropped_old", 0) + stats.get("dropped_dup", 0)
        print(
            f"清理 {path.name}: 保留 {stats.get('kept', 0)} 条，删垃圾 {stats.get('dropped_garbage', 0)}、"
            f"过旧 {stats.get('dropped_old', 0)}、重复 {stats.get('dropped_dup', 0)}"
        )
    print(f"清理完成，共删除 {total} 条")
    return 0


def _update_guides(cfg) -> int:
    root = Path(cfg.root)
    scripts = root / "scripts"
    sys.path.insert(0, str(scripts))
    try:
        import fetch_guides  # type: ignore[import-not-found]
    except Exception as exc:  # noqa: BLE001
        print(f"找不到更新脚本 scripts/fetch_guides.py：{exc}")
        return 3
    old = os.getcwd()
    try:
        os.chdir(root)
        try:
            code = int(fetch_guides.main(["--all-heroes", "--per-hero-tips", "2", "--hero-min-play", "1000"]))
        except SystemExit as exc:
            code = int(getattr(exc, "code", 0) or 0)
    finally:
        os.chdir(old)
    print(f"更新进程退出码：{code}")
    _prune_guides(cfg)
    return code


def _ensure_stdio(cfg=None) -> None:
    """打包成 windowed exe 后 sys.stdout/stderr 是 None，任何 print 都会崩；
    这里把输出接到 logs/console.log（或 %LOCALAPPDATA% 下的兜底位置）。"""
    if sys.stdout is not None and sys.stderr is not None:
        return
    try:
        if cfg is not None:
            base = cfg.log_dir
        else:
            from .config import PROJECT_ROOT

            base = Path(PROJECT_ROOT) / "logs"
        base.mkdir(parents=True, exist_ok=True)
        stream = open(base / "console.log", "a", encoding="utf-8", buffering=1)  # noqa: SIM115
    except OSError:
        stream = open(os.devnull, "w", encoding="utf-8")  # noqa: SIM115
    if sys.stdout is None:
        sys.stdout = stream
    if sys.stderr is None:
        sys.stderr = stream


def main(argv: list[str] | None = None) -> int:
    try:
        return _main(argv)
    except BaseException:  # noqa: BLE001 - 打包版没有控制台，必须落到文件
        import traceback

        _ensure_stdio()
        traceback.print_exc()
        raise


def _main(argv: list[str] | None = None) -> int:
    _ensure_stdio()
    # 被 run.ps1 通过管道转发时，默认块缓冲会让控制台迟迟不出字
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except (AttributeError, ValueError):
        pass
    args = _parse_args(argv)

    if args.version:
        from . import __version__

        print(__version__)
        return 0

    if sys.version_info < (3, 11):
        print(f"需要 Python 3.11+（推荐 3.12），当前是 {sys.version.split()[0]}。")
        print("请先从 https://www.python.org/downloads/windows/ 安装 Python 3.12。")
        return 2

    from .config import load_config

    cfg = load_config(args.config)
    _ensure_stdio(cfg)
    print(f"项目根目录: {cfg.root}")

    if args.test_voice:
        return _test_voice(cfg)

    if args.test_sound:
        import time

        from .ui.sounds import ensure_sounds, play

        sounds = ensure_sounds(cfg.log_dir / "sounds")
        path = sounds["urgent" if args.test_sound == "urgent" else "normal"]
        print(f"播放提示音：{path}")
        play(path)
        time.sleep(1.4)
        return 0

    if args.prune_guides:
        return _prune_guides(cfg)

    if args.update_guides:
        return _update_guides(cfg)

    if args.probe:
        from .probe import run_probe

        return run_probe(cfg, duration=args.duration)

    from .app import CoachApp

    coach = CoachApp(
        cfg,
        screenshot=args.screenshot,
        seconds=args.seconds,
        save_overlay=args.save_overlay,
        snapshot_path=args.snapshot,
    )
    legacy = bool(args.legacy or args.screenshot or args.snapshot or args.seconds or args.save_overlay)
    if legacy:
        # 离线自检/冒烟：不建主窗口，直接跑卡片
        return coach.run()

    from PyQt6.QtWidgets import QApplication

    from .ui.branding import app_icon, set_windows_app_id
    from .ui.panel import run_panel

    set_windows_app_id()
    qt = QApplication([sys.argv[0] or "dota2coach"])
    icon = app_icon(cfg.data_dir)
    if not icon.isNull():
        qt.setWindowIcon(icon)
    coach.attach(qt)
    coach.overlay.hide()  # 面板模式下由“开始”按钮控制卡片
    return run_panel(qt, coach, cfg)


if __name__ == "__main__":
    raise SystemExit(main())

"""无界面探针：验证 Dota 2 的 GSI 是否接通，并把报文记录到 logs/。

这是 M0 的交付物：先证明"数据能拿到"，再谈识别和建议。
"""

from __future__ import annotations

import sys
import time
from datetime import datetime

from .config import Config
from .gsi.models import Snapshot
from .gsi.recorder import GsiRecorder
from .gsi.server import GsiServer

_STATE_PREFIX = "DOTA_GAMERULES_STATE_"
_HERO_PREFIX = "npc_dota_hero_"


def format_clock(seconds: int | None) -> str:
    if seconds is None:
        return "--:--"
    sign = "-" if seconds < 0 else ""
    total = abs(int(seconds))
    return f"{sign}{total // 60:02d}:{total % 60:02d}"


def format_line(snapshot: Snapshot) -> str:
    hero = snapshot.hero_name or "-"
    if hero.startswith(_HERO_PREFIX):
        hero = hero[len(_HERO_PREFIX):]
    state = snapshot.game_state or "-"
    if state.startswith(_STATE_PREFIX):
        state = state[len(_STATE_PREFIX):]
    hp = snapshot.health_percent
    hp_text = f"{hp:.0f}%" if hp is not None else "-"
    level = "-" if snapshot.level is None else str(snapshot.level)
    gold = "-" if snapshot.gold is None else str(snapshot.gold)
    return (
        f"[{datetime.now():%H:%M:%S}] {state:<14} t={format_clock(snapshot.game_time):>6} "
        f"hero={hero:<16} lvl={level:>2} hp={hp_text:>4} "
        f"ab={snapshot.ability_count:>2} it={snapshot.item_count:>2} "
        f"kda={snapshot.kda():<7} gold={gold:>5}"
    )


def run_probe(cfg: Config, duration: float | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:
        pass

    cfg.ensure_dirs()
    recorder: GsiRecorder | None = None
    if cfg.gsi.log_raw:
        recorder = GsiRecorder(cfg.log_dir, min_interval=cfg.gsi.min_log_interval)

    state = {"count": 0, "last_print": 0.0}

    def handle(snapshot: Snapshot) -> None:
        state["count"] += 1
        if recorder is not None:
            recorder.record(snapshot)
        now = time.monotonic()
        if state["count"] == 1:
            keys = ", ".join(snapshot.top_level_keys)
            draft = "有 draft 字段" if "draft" in snapshot.top_level_keys else "无 draft 字段（当前情境不下发）"
            print(f"\n[已接通] 顶层字段: {keys}")
            print(f"         {draft}")
        if state["count"] == 1 or now - state["last_print"] >= 1.0:
            state["last_print"] = now
            print(format_line(snapshot), flush=True)

    server = GsiServer(cfg.gsi.host, cfg.gsi.port, on_snapshot=handle)
    try:
        server.start()
    except OSError as exc:
        print(f"[错误] 无法监听 {cfg.gsi.host}:{cfg.gsi.port}：{exc}")
        print(f"       端口被占用的话: netstat -ano | findstr {cfg.gsi.port}")
        return 1

    print("=" * 72)
    print("dota2-coach · GSI 探针 (M0)")
    print(f"监听地址 : {server.url}")
    print(f"原始报文 : {cfg.log_dir / 'gsi_raw'}")
    print(f"字段清单 : {cfg.log_dir / 'gsi_keys.json'}")
    print("下一步   : 启动 Dota 2，打一局人机/本地大厅，回来按 Ctrl+C 停止")
    print("=" * 72, flush=True)

    started = time.monotonic()
    deadline = started + duration if duration else None
    warned = False
    try:
        while True:
            time.sleep(0.5)
            if deadline is not None and time.monotonic() >= deadline:
                print(f"\n已运行 {duration:.0f} 秒，自动停止 ...")
                break
            if not warned and state["count"] == 0 and time.monotonic() - started > 45:
                warned = True
                print(
                    "\n[提示] 45 秒内没有收到报文，逐项检查：\n"
                    f"  1) docs\\gsi.cfg 是否已复制到 {cfg.gsi_cfg_dir}\n"
                    "  2) 放好配置文件后必须完全重启 Dota 2\n"
                    "  3) 文件名必须以 .cfg 结尾，内容用 UTF-8 保存\n"
                    f"  4) 端口是否冲突: netstat -ano | findstr {cfg.gsi.port}\n",
                    flush=True,
                )
    except KeyboardInterrupt:
        print("\n正在停止 ...")
    finally:
        server.stop()
        if recorder is not None:
            recorder.close()

    raw_lines = recorder.raw_lines if recorder is not None else 0
    summary_lines = recorder.summary_lines if recorder is not None else 0
    print(f"共收到 {state['count']} 个报文；原始 {raw_lines} 行，摘要 {summary_lines} 行。")
    if state["count"] == 0:
        if duration is not None:
            print("（自动退出模式）本次没有收到报文，退出。")
            return 0
        print("没有收到任何报文，说明 GSI 配置没生效。请把上面的检查项过一遍。")
        return 1
    return 0

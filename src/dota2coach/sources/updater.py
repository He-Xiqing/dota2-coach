"""攻略库维护：判断是否该更新、启动一次后台更新、清理旧/垃圾提示。"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path


def latest_guide_file(guides_dir: Path) -> Path | None:
    if not guides_dir.exists():
        return None
    files = [p for p in guides_dir.glob("*.json") if p.name != "index.json"]
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def guide_stats(guides_dir: Path) -> tuple[int, float | None, str]:
    """返回 (提示条数, 距上次更新天数, patch)。"""
    path = latest_guide_file(guides_dir)
    if path is None:
        return 0, None, ""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        count = len(payload.get("tips") or [])
        patch = str(payload.get("patch") or path.stem)
    except (OSError, ValueError):
        return 0, None, path.stem
    age = max(0.0, (time.time() - path.stat().st_mtime) / 86400.0)
    return count, age, patch


def update_due(guides_dir: Path, refresh_days: int) -> bool:
    _, age, _ = guide_stats(guides_dir)
    if age is None:
        return True
    return age >= max(1, int(refresh_days))


def _command(root: Path) -> list[str]:
    if getattr(sys, "frozen", False):
        return [sys.executable, "--update-guides"]
    return [sys.executable, "-m", "dota2coach", "--update-guides"]


def start_update(root: Path, log_path: Path, extra: tuple[str, ...] = ()) -> bool:
    """后台起一个更新进程；返回是否成功拉起。"""
    argv = _command(root) + list(extra)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        log = log_path.open("a", encoding="utf-8", errors="replace")
        flags = 0
        if os.name == "nt":
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "DETACHED_PROCESS", 0)
        subprocess.Popen(  # noqa: S603
            argv,
            cwd=str(root),
            stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=flags,
            close_fds=True,
        )
        return True
    except OSError as exc:
        try:
            log_path.write_text(f"启动更新失败: {exc}\n", encoding="utf-8")
        except OSError:
            pass
        return False

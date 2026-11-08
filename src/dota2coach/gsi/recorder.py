"""把 GSI 报文落到磁盘，供离线回放、字段排查和后续复盘。

产物（都在 logs/ 下）：
- gsi_raw/<matchid>-<session>.jsonl  原始报文，一行一个 {"ts","payload"}
- gsi_summary.jsonl                  每秒一行的摘要
- gsi_keys.json                      到目前为止见过的所有字段路径及出现次数
                                      （用来确认 draft 之类的字段到底存不存在）
"""

from __future__ import annotations

import json
import os
import threading
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Callable

from .models import Snapshot

_MAX_PATHS = 4000
_MAX_DEPTH = 8


def _iter_paths(value, prefix: str = "", depth: int = 0):
    """递归产出 (字段路径, 出现次数=1)。列表只取前 3 个元素，避免爆炸。"""
    if depth > _MAX_DEPTH:
        return
    if isinstance(value, dict):
        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            yield path
            yield from _iter_paths(item, path, depth + 1)
    elif isinstance(value, list):
        for index, item in enumerate(value[:3]):
            yield from _iter_paths(item, f"{prefix}[{index}]", depth + 1)


class GsiRecorder:
    def __init__(self, log_dir: Path | str, min_interval: float = 0.2,
                 clock: Callable[[], float] = time.monotonic) -> None:
        self.log_dir = Path(log_dir)
        self.raw_dir = self.log_dir / "gsi_raw"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.summary_path = self.log_dir / "gsi_summary.jsonl"
        self.keys_path = self.log_dir / "gsi_keys.json"

        self._min_interval = max(0.0, float(min_interval))
        self._clock = clock
        self._lock = threading.Lock()
        self._session = datetime.now().strftime("%Y%m%d-%H%M%S")

        self._last_raw = 0.0
        self._last_summary = 0.0
        self._last_top_keys: tuple[str, ...] = ()
        self._key_counts: Counter[str] = Counter()
        self._key_overflow = False

        self._records = 0
        self.raw_lines = 0
        self.summary_lines = 0

    # --- 公开接口 -----------------------------------------------------
    def record(self, snapshot: Snapshot) -> None:
        with self._lock:
            now = self._clock()
            top_keys = snapshot.top_level_keys
            first = self._records == 0
            keys_changed = top_keys != self._last_top_keys

            if first or keys_changed or (now - self._last_raw) >= self._min_interval:
                self._write_raw(snapshot)
            if first or (now - self._last_summary) >= 1.0:
                self._write_summary(snapshot, now)

            self._last_top_keys = top_keys
            self._records += 1
            self._collect_paths(snapshot.raw)
            if self._records % 200 == 0:
                self._write_keys()

    def close(self) -> None:
        with self._lock:
            self._write_keys()

    @property
    def records(self) -> int:
        return self._records

    @property
    def paths(self) -> dict[str, int]:
        return dict(self._key_counts)

    # --- 内部 ---------------------------------------------------------
    def _write_raw(self, snapshot: Snapshot) -> None:
        # 每条都打开-写入-关闭：显式关闭能让文件大小/内容立刻可见（常驻句柄
        # 在沙箱里要等进程退出才刷新），探针运行中也能 tail 日志。
        match_id = snapshot.match_id or "unknown"
        path = self.raw_dir / f"{match_id}-{self._session}.jsonl"
        line = json.dumps({"ts": round(time.time(), 3), "payload": snapshot.raw},
                          ensure_ascii=False, separators=(",", ":"))
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(line + "\n")
        self._last_raw = self._clock()
        self.raw_lines += 1

    def _write_summary(self, snapshot: Snapshot, now: float) -> None:
        entry = {"ts": round(time.time(), 3), **snapshot.summary()}
        with self.summary_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self._last_summary = now
        self.summary_lines += 1

    def _collect_paths(self, payload: dict) -> None:
        for path in _iter_paths(payload):
            if path in self._key_counts:
                self._key_counts[path] += 1
            elif len(self._key_counts) < _MAX_PATHS:
                self._key_counts[path] = 1
            else:
                self._key_overflow = True

    def _write_keys(self) -> None:
        data = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "records": self._records,
            "truncated": self._key_overflow,
            "paths": dict(sorted(self._key_counts.items())),
        }
        tmp = self.keys_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, self.keys_path)

"""把录下来的 GSI 报文回放给本地服务：不开游戏也能调 Overlay / 规则。

用法（在项目根目录执行）：

    python tools/replay_gsi.py logs/gsi_raw/7890123456-20261107-100447.jsonl
    python tools/replay_gsi.py <文件> --speed 20 --limit 200

先另开一个窗口启动服务：

    python -m dota2coach --probe
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


def _unwrap(item) -> tuple[float | None, dict | None]:
    if isinstance(item, dict) and isinstance(item.get("payload"), dict):
        ts = item.get("ts")
        return (float(ts) if isinstance(ts, (int, float)) else None), item["payload"]
    if isinstance(item, dict):
        return None, item
    return None, None


def iter_records(path: Path):
    """逐条产出 (时间戳, 报文)。

    兼容三种文件：录制出来的 JSONL（{"ts","payload"}）、裸报文 JSONL、
    以及单个格式化过的 JSON 报文（例如 tests/fixtures/gsi/playing.json）。
    """
    text = path.read_text(encoding="utf-8")
    stripped = text.strip()

    # 先按"整份 JSON"试一次：fixture 和手工整理过的样本都是这种
    if stripped.startswith("{"):
        try:
            whole = json.loads(stripped)
        except json.JSONDecodeError:
            whole = None
        if isinstance(whole, dict):
            ts, payload = _unwrap(whole)
            if payload is not None:
                yield ts, payload
                return

    for line_no, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            print(f"[skip] 第 {line_no} 行不是合法 JSON")
            continue
        ts, payload = _unwrap(item)
        if payload is not None:
            yield ts, payload


def post(url: str, payload: dict, timeout: float = 5.0) -> int:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="回放 GSI 报文到本地教练服务")
    parser.add_argument("file", type=Path, help="logs/gsi_raw/*.jsonl")
    parser.add_argument("--url", default="http://127.0.0.1:31982/")
    parser.add_argument("--speed", type=float, default=10.0, help="倍速，默认 10")
    parser.add_argument("--limit", type=int, default=0, help="只回放前 N 条，0 表示全部")
    parser.add_argument("--max-gap", type=float, default=2.0, help="两次发送之间的最大等待（秒）")
    args = parser.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:
        pass

    if not args.file.exists():
        print(f"找不到文件: {args.file}")
        return 2

    speed = max(0.1, args.speed)
    sent = 0
    previous_ts = None
    for ts, payload in iter_records(args.file):
        if args.limit and sent >= args.limit:
            break
        if previous_ts is not None and isinstance(ts, (int, float)):
            gap = max(0.0, float(ts) - previous_ts) / speed
            time.sleep(min(gap, args.max_gap))
        if isinstance(ts, (int, float)):
            previous_ts = float(ts)
        try:
            status = post(args.url, payload)
        except (urllib.error.URLError, OSError) as exc:
            print(f"[错误] 发不出去: {exc}")
            print("       先启动服务：python -m dota2coach --probe")
            return 1
        sent += 1
        if status != 200:
            print(f"[warn] 第 {sent} 条返回 {status}")

    print(f"回放完成：{sent} 条")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

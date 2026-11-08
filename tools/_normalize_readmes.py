"""README 空行规范化：每个二级标题前保证一个空行，删除连续空行。"""

from __future__ import annotations

from pathlib import Path


def normalize(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    for line in lines:
        if line.startswith("## ") and out and out[-1].strip():
            out.append("")
        if not line.strip() and out and not out[-1].strip():
            continue
        out.append(line)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("normalized", path.name)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    for path in sorted(root.glob("README*.md")):
        normalize(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

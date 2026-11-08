"""修正 README：删除重复主图，规范“截图”标题与前后的空行。"""

from __future__ import annotations

from pathlib import Path

from tools._enhance_readmes import I18N


def fix(path: Path, heading: str) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()

    for i, line in enumerate(lines):
        if 'alt="DOTA2 Coach lineup"' in line:
            start, end = i - 1, i + 1
            if lines[start].strip() == '<p align="center">' and lines[end].strip() == "</p>":
                del lines[start : end + 1]
                if start < len(lines) and not lines[start].strip():
                    del lines[start]
            break

    # 确保空行结构：</p> / 空行 / ## 截图 / 空行 / <p ...>
    out: list[str] = []
    for line in lines:
        if line.strip() == heading:
            while out and not out[-1].strip():
                out.pop()
            if out:
                out.append("")
            out.append(line)
            out.append("")
            continue
        out.append(line)

    # 标题后如果紧跟空行已加，避免重复
    cleaned: list[str] = []
    for line in out:
        if not line.strip() and cleaned and not cleaned[-1].strip():
            continue
        cleaned.append(line)

    path.write_text("\n".join(cleaned) + "\n", encoding="utf-8")
    print("fixed", path.name)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    for code, t in I18N.items():
        fix(root / f"README.{code}.md", t["shots"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

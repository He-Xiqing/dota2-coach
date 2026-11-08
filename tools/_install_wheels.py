"""临时脚本：pip 在当前沙箱无法删除临时目录，改为直连镜像下载 wheel 并解压。

用法：python tools/_install_wheels.py [包名...]
"""
from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path
from urllib.parse import urljoin

import httpx

INDEX = "https://pypi.tuna.tsinghua.edu.cn/simple/{name}/"
ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / ".venv" / "Lib" / "site-packages"
CACHE = ROOT / ".tmp" / "wheels"


def _version_key(filename: str) -> tuple:
    match = re.search(r"-(\d+)\.(\d+)(?:\.(\d+))?", filename)
    if not match:
        return (0, 0, 0)
    return tuple(int(x or 0) for x in match.groups())


def pick_wheel(name: str, html: str) -> str:
    hrefs = re.findall(r'href=[\'"]([^\'"]+?\.whl)(?:#[^\'"]*)?[\'"]', html)
    hrefs = [h.split("#", 1)[0] for h in hrefs]
    if not hrefs:
        raise SystemExit(f"{name}: 索引里没有 wheel（共 {len(html)} 字节）")
    if name == "pyinstaller":
        candidates = [h for h in hrefs if "py3-none-win_amd64.whl" in h]
    else:
        candidates = [h for h in hrefs if "py3-none-any.whl" in h]
    if not candidates:
        candidates = hrefs
    return max(candidates, key=lambda h: _version_key(h.rsplit("/", 1)[-1]))


def main(argv: list[str]) -> int:
    CACHE.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=180.0, follow_redirects=True) as client:
        for name in argv:
            index = INDEX.format(name=name)
            html = client.get(index).text
            href = pick_wheel(name, html)
            url = urljoin(index, href)
            target = CACHE / url.rsplit("/", 1)[-1]
            if not target.exists() or target.stat().st_size < 1024:
                response = client.get(url)
                response.raise_for_status()
                target.write_bytes(response.content)
            with zipfile.ZipFile(target) as archive:
                archive.extractall(DEST)
            print(f"{name}: {target.name} -> {DEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(
        main(
            sys.argv[1:]
            or [
                "pyinstaller",
                "altgraph",
                "pywin32-ctypes",
                "pyinstaller-hooks-contrib",
                "setuptools",
            ]
        )
    )

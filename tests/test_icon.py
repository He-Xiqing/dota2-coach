"""应用图标资源与生成脚本。"""

from __future__ import annotations

import struct
import sys
import unittest
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from make_icon import make_icon  # noqa: E402

from dota2coach.ui.branding import icon_path  # noqa: E402


def ico_sizes(path: Path) -> list[int]:
    """读取 ICO 目录里的尺寸（宽，0 表示 256）。"""
    data = path.read_bytes()
    if data[:4] != b"\x00\x00\x01\x00":
        raise AssertionError("不是 ICO 文件")
    count = struct.unpack_from("<H", data, 4)[0]
    out: list[int] = []
    for index in range(count):
        offset = 6 + index * 16
        width = data[offset]
        out.append(256 if width == 0 else width)
    return out


class IconTest(unittest.TestCase):
    def test_repo_icon_exists(self) -> None:
        ico = ROOT / "data" / "app.ico"
        self.assertTrue(ico.exists(), "data/app.ico 应随仓库分发")
        sizes = ico_sizes(ico)
        self.assertIn(16, sizes)
        self.assertIn(32, sizes)
        self.assertIn(256, sizes)
        self.assertTrue((ROOT / "data" / "app.png").exists())

    def test_icon_path_fallback(self) -> None:
        self.assertTrue(str(icon_path(ROOT / "data")).endswith(".ico"))
        self.assertTrue(str(icon_path(ROOT / "no-such-dir")).endswith(".png"))

    def test_make_icon_generates_valid_files(self) -> None:
        tmp = Path(__file__).resolve().parent / "_tmp" / f"icon-{uuid4().hex[:8]}"
        try:
            png, ico = make_icon(tmp)
            self.assertEqual(png.name, "app.png")
            self.assertEqual(ico.name, "app.ico")
            self.assertGreater(png.stat().st_size, 1024)
            sizes = ico_sizes(ico)
            self.assertIn(16, sizes)
            self.assertIn(256, sizes)
        finally:
            import shutil

            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

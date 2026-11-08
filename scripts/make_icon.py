"""生成应用图标（原创图形：深蓝圆角底 + 金色 D2 字标 + 哨声弧线）。

用法：
    python scripts/make_icon.py            # 输出到 data/app.png 与 data/app.ico

只依赖 Pillow；图标产物已提交到仓库，正常构建不需要重新生成。
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SIZE = 512
RADIUS = 112
GOLD = (242, 193, 78, 255)
NAVY_TOP = (22, 35, 63)
NAVY_BOTTOM = (11, 18, 32)
ICO_SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\seguisb.ttf",
]


def _gradient() -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE))
    px = img.load()
    for y in range(SIZE):
        t = y / (SIZE - 1)
        color = tuple(
            int(NAVY_TOP[i] + (NAVY_BOTTOM[i] - NAVY_TOP[i]) * t) for i in range(3)
        ) + (255,)
        for x in range(SIZE):
            px[x, y] = color
    return img


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def make_icon(out_dir: Path | str = ROOT / "data") -> tuple[Path, Path]:
    """生成 PNG 与多尺寸 ICO，返回 (png, ico)。"""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    base = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, SIZE - 1, SIZE - 1), RADIUS, fill=255)
    base.paste(_gradient(), (0, 0), mask)

    draw = ImageDraw.Draw(base)
    # 外描边，让图标在浅色任务栏上也有边界
    draw.rounded_rectangle(
        (2, 2, SIZE - 3, SIZE - 3), RADIUS, outline=(255, 255, 255, 38), width=4
    )

    # 金色字标 D2：按实际字形宽度缩放，保证居中
    text = "D2"
    font = _font(300)
    box = draw.textbbox((0, 0), text, font=font)
    tw, th = box[2] - box[0], box[3] - box[1]
    target_w = int(SIZE * 0.62)
    if tw > 0:
        font = _font(max(80, int(font.size * target_w / tw)))
        box = draw.textbbox((0, 0), text, font=font)
        tw, th = box[2] - box[0], box[3] - box[1]
    tx = (SIZE - tw) // 2 - box[0]
    ty = (SIZE - th) // 2 - box[1] + int(SIZE * 0.02)
    draw.text((tx, ty), text, font=font, fill=GOLD)

    # 右上角哨声弧线（两段圆弧，留出缺口）
    ring_box = (int(SIZE * 0.62), int(SIZE * 0.06), int(SIZE * 1.06), int(SIZE * 0.50))
    draw.arc(ring_box, start=200, end=340, fill=GOLD, width=int(SIZE * 0.035))

    png_path = out / "app.png"
    ico_path = out / "app.ico"
    base.save(png_path, format="PNG")
    base.save(ico_path, format="ICO", sizes=ICO_SIZES)
    return png_path, ico_path


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    out = Path(args[0]) if args else ROOT / "data"
    png, ico = make_icon(out)
    print(f"png: {png} ({png.stat().st_size} bytes)")
    print(f"ico: {ico} ({ico.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

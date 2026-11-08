"""一次性补丁：小地图可配置（位置/大小/偏移）与自动定位接入。"""

from pathlib import Path

C = Path("src/dota2coach/config.py")
s = C.read_text(encoding="utf-8")

if "class MinimapConfig" not in s:
    s = s.replace(
        "@dataclass\nclass AssistConfig:",
        '''@dataclass
class MinimapConfig:
    """小地图位置/大小：自动定位失败时用这里的值兜底。"""

    side: str = "auto"  # auto / left / right
    size_percent: int = 100
    offset_x: int = 0
    offset_y: int = 0


@dataclass
class AssistConfig:''',
        1,
    )

    s = s.replace(
        "    guides: GuidesConfig",
        "    guides: GuidesConfig\n    minimap: MinimapConfig",
        1,
    )
    s = s.replace(
        "        guides=GuidesConfig(",
        "        minimap=MinimapConfig(\n            side=str(mm.get(\"side\", \"auto\")),\n            size_percent=int(mm.get(\"size_percent\", 100)),\n            offset_x=int(mm.get(\"offset_x\", 0)),\n            offset_y=int(mm.get(\"offset_y\", 0)),\n        ),\n        guides=GuidesConfig(",
        1,
    )
    s = s.replace(
        "    guides_raw = raw.get(\"guides\") or {}",
        "    guides_raw = raw.get(\"guides\") or {}\n    mm = raw.get(\"minimap\") or {}",
        1,
    )
    s = s.replace(
        '    sections.append("[guides]")',
        '''    sections.append("[minimap]")
    sections.append(f"side = {_quote(cfg.minimap.side)}")
    sections.append(f"size_percent = {int(cfg.minimap.size_percent)}")
    sections.append(f"offset_x = {int(cfg.minimap.offset_x)}")
    sections.append(f"offset_y = {int(cfg.minimap.offset_y)}")
    sections.append("")
    sections.append("[guides]")''',
        1,
    )
    s = s.replace(
        '    if side not in {"auto", "left", "right"}:',
        '    if side not in {"auto", "left", "right"}:',
        1,
    )
    if "def _validate_minimap" not in s:
        s = s.replace(
            "def validate_config(cfg: Config) -> list[str]:",
            '''def _validate_minimap(cfg: Config) -> list[str]:
    problems: list[str] = []
    mm = cfg.minimap
    if mm.side not in {"auto", "left", "right"}:
        problems.append("小地图位置只能是 auto/left/right")
    if not 60 <= int(mm.size_percent) <= 160:
        problems.append("小地图大小需在 60%–160% 之间")
    if abs(int(mm.offset_x)) > 300 or abs(int(mm.offset_y)) > 300:
        problems.append("小地图偏移需在 ±300 像素内")
    return problems


def validate_config(cfg: Config) -> list[str]:''',
            1,
        )
        s = s.replace(
            "    problems.extend(_validate_hotkeys(cfg))",
            "    problems.extend(_validate_hotkeys(cfg))\n    problems.extend(_validate_minimap(cfg))",
            1,
        )
C.write_text(s, encoding="utf-8")

A = Path("src/dota2coach/app.py")
a = A.read_text(encoding="utf-8")
a = a.replace(
    "from .vision.minimap import MINIMAP_FRAC, MinimapDots, StaticFilter, crop_minimap, detect_dots",
    "from .vision.minimap import (\n    MINIMAP_FRAC,\n    MinimapDots,\n    StaticFilter,\n    crop_minimap,\n    detect_dots,\n    locate_minimap,\n)",
    1,
)
a = a.replace(
    "    def _minimap_region(self):\n        from .vision.capture import Region, dota_window_rect\n\n        rect = dota_window_rect()",
    '''    def _minimap_region(self):
        from .vision.capture import Region, dota_window_rect

        if self._mm_rect is not None:
            return Region(
                self._mm_rect.left,
                self._mm_rect.top,
                self._mm_rect.width,
                self._mm_rect.height,
            )
        rect = dota_window_rect()''',
    1,
)
a = a.replace(
    "        width = int(rect.width * (MINIMAP_FRAC[2] - MINIMAP_FRAC[0]))\n        height = int(rect.height * (MINIMAP_FRAC[3] - MINIMAP_FRAC[1]))\n        if width < 40 or height < 40:\n            return None\n        return Region(left, top, width, height)",
    '''        width = int(rect.width * (MINIMAP_FRAC[2] - MINIMAP_FRAC[0]))
        height = int(rect.height * (MINIMAP_FRAC[3] - MINIMAP_FRAC[1]))
        mm = self.config.minimap
        if mm.side == "left":
            left = rect.left + int(rect.width * 0.002)
        scale = max(0.6, min(1.6, mm.size_percent / 100.0))
        width = max(1, int(width * scale))
        height = max(1, int(height * scale))
        left += int(mm.offset_x)
        top += int(mm.offset_y)
        if width < 40 or height < 40:
            return None
        return Region(left, top, width, height)

    def _auto_minimap(self) -> None:
        """多帧尝试自动定位小地图；失败就留空，走配置兜底。"""
        from .vision.capture import Region

        if self.capture is None:
            return
        frames = []
        for _ in range(5):
            try:
                frames.append(self.capture.grab())
            except Exception:
                break
        if not frames:
            return
        side = self.config.minimap.side
        sides = (side,) if side in ("left", "right") else ("right", "left")
        rect = locate_minimap(frames, sides=sides)
        if rect is None:
            return
        self._mm_rect = Region(rect.left, rect.top, rect.width, rect.height)
        self._mm_misses = 0
        print(
            f"[小地图] 自动定位：({rect.left}, {rect.top}) {rect.width}x{rect.height}"
        )''',
    1,
)
a = a.replace(
    "        clock = clock_time(snapshot)\n        if clock < 20 * 60:",
    "        clock = clock_time(snapshot)\n        if clock < 10 * 60:",
    1,
)
A.write_text(a, encoding="utf-8")
print("config/app patched")

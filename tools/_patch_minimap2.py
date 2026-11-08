"""修复 Config 字段默认值，并接入小地图扫描逻辑。"""

from pathlib import Path

C = Path("src/dota2coach/config.py")
s = C.read_text(encoding="utf-8")
s = s.replace(
    "    guides: GuidesConfig\n    minimap: MinimapConfig = field(default_factory=GuidesConfig)",
    "    guides: GuidesConfig = field(default_factory=GuidesConfig)\n"
    "    minimap: MinimapConfig = field(default_factory=MinimapConfig)",
)
C.write_text(s, encoding="utf-8")

A = Path("src/dota2coach/app.py")
a = A.read_text(encoding="utf-8")

old_scan = """        self._mm_at = now + 1.0
        region = self._minimap_region()"""
new_scan = """        self._mm_at = now + 1.0
        if self._mm_rect is None and self.config.minimap.side == "auto":
            self._auto_minimap()
        region = self._minimap_region()"""
a = a.replace(old_scan, new_scan, 1)

old_dots = """        crop = crop_minimap(image)
        dots = detect_dots(crop)"""
new_dots = """        crop = crop_minimap(image)
        dots = detect_dots(crop)
        if dots.enemies:
            self._mm_misses = 0
        else:
            self._mm_misses += 1
            if self._mm_misses >= 45:
                self._mm_rect = None
                self._mm_misses = 0
                self._print("[小地图] 连续 45 秒没有红点，重新定位小地图")"""
a = a.replace(old_dots, new_dots, 1)
A.write_text(a, encoding="utf-8")
print("patched")

"""初始化小地图定位状态。"""

from pathlib import Path

A = Path("src/dota2coach/app.py")
a = A.read_text(encoding="utf-8")
a = a.replace(
    "        self._mm_at = 0.0\n",
    "        self._mm_at = 0.0\n        self._mm_rect = None\n        self._mm_misses = 0\n",
    1,
)
a = a.replace(
    "            self._mm_at = 0.0\n",
    "            self._mm_at = 0.0\n            self._mm_rect = None\n            self._mm_misses = 0\n",
    1,
)
A.write_text(a, encoding="utf-8")
print("init patched")

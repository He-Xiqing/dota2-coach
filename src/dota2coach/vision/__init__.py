"""屏幕截取与英雄识别。

当前实现：
- `capture.py`：mss 抓屏（Windows 下走 DXGI，比 PIL.ImageGrab 快）
- `heroes.py`：在"战友与宿敌"面板 / 顶部英雄栏里定位 10 个英雄格子并做模板匹配

注意：GSI 永远不会下发敌方英雄，识别只能靠屏幕。相关实测见 docs/data-sources.md。
"""

from .capture import Region, ScreenCapture

__all__ = ["Region", "ScreenCapture"]

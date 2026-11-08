"""屏幕截取：mss 抓屏，返回 OpenCV 的 BGR 数组。

重要：Dota 2 在“窗口化/无边框窗口”下只占桌面的一部分。
如果直接抓整个显示器，面板比例（0.84, 0.14…）就会指到桌面右下角，识别必然失败。
所以默认先找 Dota 2 的窗口矩形（win32gui），只抓游戏客户区；
找不到窗口（独占全屏、或非 Windows）时退回整屏。
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Region:
    """屏幕上的一个矩形（物理像素）。"""

    left: int
    top: int
    width: int
    height: int

    def as_dict(self) -> dict[str, int]:
        return {"left": self.left, "top": self.top, "width": self.width, "height": self.height}


def _window_pid(hwnd: int) -> int:
    import win32process

    try:
        _thread, pid = win32process.GetWindowThreadProcessId(hwnd)
        return int(pid)
    except Exception:  # noqa: BLE001
        return 0


def dota_pids() -> set[int]:
    """当前所有 Dota 2 窗口的进程号（标题含 Dota 2）。"""
    if sys.platform != "win32":
        return set()
    try:
        import win32gui
    except ImportError:
        return set()
    pids: set[int] = set()

    def collect(hwnd: int, _extra) -> None:
        try:
            if not win32gui.IsWindowVisible(hwnd):
                return
            if "dota 2" in (win32gui.GetWindowText(hwnd) or "").lower():
                pid = _window_pid(hwnd)
                if pid:
                    pids.add(pid)
        except Exception:  # noqa: BLE001
            return

    try:
        win32gui.EnumWindows(collect, None)
    except Exception:  # noqa: BLE001
        return set()
    return pids


def _pid_is_dota(pid: int) -> bool:
    """进程可执行名是不是 dota2.exe（不依赖窗口标题，最稳）。"""
    if not pid:
        return False
    try:
        import ctypes
        from ctypes import wintypes

        process = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)  # QUERY_LIMITED_INFORMATION
        if not process:
            return False
        try:
            buffer = ctypes.create_unicode_buffer(1024)
            size = wintypes.DWORD(len(buffer))
            ok = ctypes.windll.kernel32.QueryFullProcessImageNameW(
                process, 0, buffer, ctypes.byref(size)
            )
            return bool(ok) and buffer.value.lower().endswith("dota2.exe")
        finally:
            ctypes.windll.kernel32.CloseHandle(process)
    except Exception:  # noqa: BLE001
        return False


def dota_foreground() -> bool:
    """当前前台窗口是不是 Dota 2。

    多重判断：窗口类 SDL_app / 前台进程 dota2.exe / 前台窗口或其祖先在 Dota 窗口列表里。
    """
    if sys.platform != "win32":
        return False
    try:
        import win32gui
    except ImportError:
        return False
    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return False
        try:
            if (win32gui.GetClassName(hwnd) or "") == "SDL_app":
                return True
        except Exception:  # noqa: BLE001
            pass
        if _pid_is_dota(_window_pid(hwnd)):
            return True

        hwnds: set[int] = set()

        def collect(candidate: int, _extra) -> None:
            try:
                if not win32gui.IsWindowVisible(candidate):
                    return
                if "dota 2" in (win32gui.GetWindowText(candidate) or "").lower():
                    hwnds.add(candidate)
            except Exception:  # noqa: BLE001
                return

        win32gui.EnumWindows(collect, None)
        if not hwnds:
            return False
        if hwnd in hwnds:
            return True
        try:
            if win32gui.GetAncestor(hwnd, 2) in hwnds:  # GA_ROOT
                return True
        except Exception:  # noqa: BLE001
            pass
        return _window_pid(hwnd) in {_window_pid(h) for h in hwnds}
    except Exception:  # noqa: BLE001
        return False


def dota_window_rect() -> Region | None:
    """返回 Dota 2 窗口客户区（屏幕坐标）；找不到时返回 None。"""
    if sys.platform != "win32":
        return None
    try:
        import win32gui
    except ImportError:
        return None

    matches: list[tuple[int, str]] = []

    def collect(hwnd: int, _extra) -> None:
        if not win32gui.IsWindowVisible(hwnd):
            return
        title = win32gui.GetWindowText(hwnd)
        if "dota 2" in title.lower():
            try:
                cls = win32gui.GetClassName(hwnd)
            except Exception:  # noqa: BLE001
                cls = ""
            matches.append((hwnd, cls))

    try:
        win32gui.EnumWindows(collect, None)
        if not matches:
            return None
        # Dota 2 的窗口类是 SDL_app；Steam 浏览器里的页面标题也可能带 "Dota 2"，优先排除
        hwnd = next((h for h, cls in matches if cls == "SDL_app"), matches[0][0])
        if not any(cls == "SDL_app" for _h, cls in matches) and len(matches) > 1:
            def area(item: tuple[int, str]) -> int:
                rect = win32gui.GetClientRect(item[0])
                return int(rect[2]) * int(rect[3])

            hwnd = max(matches, key=area)[0]
        left, top = win32gui.ClientToScreen(hwnd, (0, 0))
        right, bottom = win32gui.ClientToScreen(hwnd, win32gui.GetClientRect(hwnd)[2:4])
        width, height = right - left, bottom - top
        if width < 640 or height < 480:
            return None
        return Region(int(left), int(top), int(width), int(height))
    except Exception:  # noqa: BLE001 - 窗口 API 失败不应影响抓屏
        return None


class ScreenCapture:
    """抓屏：默认只抓 Dota 2 窗口，找不到时抓主显示器。

    mss 的实例不能跨线程共享，所以这里按需创建、显式 close。
    """

    def __init__(self, monitor: int = 1, game_window: bool = True) -> None:
        self._monitor_index = monitor
        self._game_window = game_window
        self._sct = None
        self.last_region: Region | None = None

    def _ensure(self):
        if self._sct is None:
            import mss  # 延迟导入：不抓屏的单元测试不需要它

            self._sct = mss.mss()
        return self._sct

    def monitor(self, index: int | None = None) -> Region:
        sct = self._ensure()
        monitors = sct.monitors
        idx = self._monitor_index if index is None else index
        if idx >= len(monitors):
            idx = 0
        m = monitors[idx]
        return Region(int(m["left"]), int(m["top"]), int(m["width"]), int(m["height"]))

    def game_region(self) -> Region:
        """游戏窗口矩形；没有窗口（全屏/非 Windows）就退回整屏。"""
        if self._game_window:
            rect = dota_window_rect()
            if rect is not None:
                return rect
        return self.monitor()

    def grab(self, region: Region | None = None) -> np.ndarray:
        sct = self._ensure()
        box = region or self.game_region()
        self.last_region = box
        shot = sct.grab(box.as_dict())
        rgb = np.frombuffer(shot.rgb, dtype=np.uint8).reshape(shot.height, shot.width, 3)
        # mss 给的是 RGB，OpenCV 用 BGR
        return rgb[:, :, ::-1].copy()

    def size(self) -> tuple[int, int]:
        region = self.monitor()
        return region.width, region.height

    def close(self) -> None:
        if self._sct is not None:
            try:
                self._sct.close()
            finally:
                self._sct = None

    def __enter__(self) -> "ScreenCapture":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()

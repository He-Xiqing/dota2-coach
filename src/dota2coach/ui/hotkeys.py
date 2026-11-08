"""全局快捷键（默认 F8 显示/隐藏卡片，F9 试听语音）。

Windows 下用 RegisterHotKey + 原生事件过滤；注册失败不影响其它功能。
键位可在设置页改成 F1–F12（写进 config.toml 的 [hotkeys]）。
"""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes

from PyQt6.QtCore import QAbstractNativeEventFilter, QObject

WM_HOTKEY = 0x0312
MOD_NOREPEAT = 0x4000

_VK = {f"F{index}": 0x6F + index for index in range(1, 13)}  # F1 = 0x70


class _Filter(QAbstractNativeEventFilter):
    def __init__(self, owner: "Hotkeys") -> None:
        super().__init__()
        self.owner = owner

    def nativeEventFilter(self, event_type, message):  # noqa: N802 - Qt 命名
        if event_type in (b"windows_generic_MSG", "windows_generic_MSG"):
            try:
                msg = ctypes.cast(int(message), ctypes.POINTER(wintypes.MSG)).contents
            except (TypeError, ValueError):
                return False, 0
            if msg.message == WM_HOTKEY:
                hotkey_id = int(msg.wParam)
                self.owner.trigger(hotkey_id)
                return True, 0
        return False, 0


class Hotkeys(QObject):
    """注册两个全局热键；回调由调用方提供，键位可热改。"""

    def __init__(
        self,
        on_toggle_card,
        on_test_voice,
        toggle_key: str = "F8",
        voice_key: str = "F9",
    ) -> None:
        super().__init__()
        self._on_toggle = on_toggle_card
        self._on_voice = on_test_voice
        self.toggle_key = (toggle_key or "F8").upper()
        self.voice_key = (voice_key or "F9").upper()
        self._ids: dict[int, callable] = {}
        self._filter: _Filter | None = None
        self._qt_app = None
        self._user32 = ctypes.windll.user32 if sys.platform == "win32" else None

    @property
    def active(self) -> bool:
        return bool(self._ids)

    def register(self, qt_app) -> list[str]:
        """注册热键，返回失败项（例如被其它软件占用）。"""
        self._qt_app = qt_app
        if self._user32 is None:
            return [self.toggle_key, self.voice_key]
        self.unregister()
        problems: list[str] = []
        plan = {
            1: (self.toggle_key, self._on_toggle),
            2: (self.voice_key, self._on_voice),
        }
        for hotkey_id, (name, callback) in plan.items():
            vk = _VK.get(name)
            if vk is None:
                problems.append(name)
                continue
            ok = self._user32.RegisterHotKey(None, hotkey_id, MOD_NOREPEAT, vk)
            if ok:
                self._ids[hotkey_id] = callback
            else:
                problems.append(name)
        if self._filter is None:
            self._filter = _Filter(self)
            qt_app.installNativeEventFilter(self._filter)
        return problems

    def rebind(self, toggle_key: str, voice_key: str) -> list[str]:
        """改键后重新注册（面板保存设置时调用）。"""
        self.toggle_key = (toggle_key or self.toggle_key).upper()
        self.voice_key = (voice_key or self.voice_key).upper()
        if self._qt_app is None:
            return []
        return self.register(self._qt_app)

    def trigger(self, hotkey_id: int) -> None:
        callback = self._ids.get(hotkey_id)
        if callback is not None:
            callback()

    def unregister(self) -> None:
        if self._user32 is not None:
            for hotkey_id in list(self._ids):
                self._user32.UnregisterHotKey(None, hotkey_id)
        self._ids.clear()

"""检测系统/游戏是否正在出声（WASAPI 默认输出设备的峰值电平）。

用途：朗读前先等游戏（或别的程序）把话说完，避免压过 Dota2 的语音播报。
不依赖第三方库：直接用 ctypes 调 COM 的 IMMDeviceEnumerator / IAudioMeterInformation。
"""

from __future__ import annotations

import ctypes
import sys
import time
from ctypes import POINTER, byref, c_float, c_uint, c_ulong, c_ushort, c_void_p, wintypes

if sys.platform == "win32":
    ole32 = ctypes.windll.ole32
else:  # pragma: no cover - 只在 Windows 用
    ole32 = None


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", c_ulong),
        ("Data2", c_ushort),
        ("Data3", c_ushort),
        ("Data4", ctypes.c_ubyte * 8),
    ]


def _guid(text: str) -> GUID:
    parts = text.strip("{}").split("-")
    value = GUID()
    value.Data1 = int(parts[0], 16)
    value.Data2 = int(parts[1], 16)
    value.Data3 = int(parts[2], 16)
    tail = bytes.fromhex("".join(parts[3:]))
    value.Data4 = (ctypes.c_ubyte * 8)(*tail)
    return value


CLSID_MMDeviceEnumerator = _guid("BCDE0395-E52F-467C-8E3D-C4579291692E")
IID_IMMDeviceEnumerator = _guid("A95664D2-9614-4F35-A746-DE8DB63617E6")
IID_IAudioMeterInformation = _guid("C02216F6-8C67-4B5B-9D00-D008E73E0064")

CLSCTX_INPROC_SERVER = 1
eRender = 0
eMultimedia = 1


def _vtable(ptr: int):
    table = ctypes.cast(ptr, POINTER(POINTER(c_void_p)))
    return table.contents


def _call(ptr: int, index: int, restype, argtypes, *args):
    fn = ctypes.WINFUNCTYPE(restype, c_void_p, *argtypes)(_vtable(ptr)[index])
    return fn(ptr, *args)


def _release(ptr: int | None) -> None:
    if not ptr:
        return
    try:
        _call(ptr, 2, ctypes.c_ulong, [])
    except Exception:  # noqa: BLE001
        pass


class GameAudioGate:
    """busy() 为 True 表示“现在有声音，先别说话”。"""

    def __init__(self, threshold: float = 0.01, music_after: float = 8.0) -> None:
        self.threshold = max(0.001, float(threshold))
        self.music_after = max(2.0, float(music_after))
        self._meter: int | None = None
        self._device: int | None = None
        self._enumerator: int | None = None
        self._peak = c_float(0.0)
        self._continuous_start: float | None = None
        self._ignored = False
        self.error = ""
        if sys.platform == "win32":
            self._init()

    # ---- COM 初始化 ----
    def _init(self) -> None:
        try:
            try:
                ole32.CoInitializeEx(None, 2)  # APARTMENTTHREADED
            except OSError:
                pass
            enumerator = c_void_p()
            hr = ole32.CoCreateInstance(
                byref(CLSID_MMDeviceEnumerator),
                None,
                CLSCTX_INPROC_SERVER,
                byref(IID_IMMDeviceEnumerator),
                byref(enumerator),
            )
            if hr != 0:
                raise OSError(f"CoCreateInstance 失败 hr=0x{hr & 0xFFFFFFFF:08X}")
            self._enumerator = enumerator.value
            device = c_void_p()
            hr = _call(
                self._enumerator,
                4,
                ctypes.c_long,
                [ctypes.c_int, ctypes.c_int, POINTER(c_void_p)],
                eRender,
                eMultimedia,
                byref(device),
            )
            if hr != 0 or not device.value:
                raise OSError(f"GetDefaultAudioEndpoint 失败 hr=0x{hr & 0xFFFFFFFF:08X}")
            self._device = device.value
            meter = c_void_p()
            hr = _call(
                self._device,
                3,
                ctypes.c_long,
                [POINTER(GUID), ctypes.c_ulong, c_void_p, POINTER(c_void_p)],
                byref(IID_IAudioMeterInformation),
                CLSCTX_INPROC_SERVER,
                None,
                byref(meter),
            )
            if hr != 0 or not meter.value:
                raise OSError(f"Activate(IAudioMeterInformation) 失败 hr=0x{hr & 0xFFFFFFFF:08X}")
            self._meter = meter.value
        except Exception as exc:  # noqa: BLE001
            self.error = str(exc)
            self.close()

    # ---- 查询 ----
    def peak(self) -> float:
        if not self._meter:
            return 0.0
        try:
            hr = _call(self._meter, 3, ctypes.c_long, [POINTER(c_float)], byref(self._peak))
            if hr != 0:
                return 0.0
            return float(self._peak.value)
        except Exception:  # noqa: BLE001
            return 0.0

    def busy(self) -> bool:
        """有持续声音（不是一闪而过的音效）就返回 True；连续播了很久视为背景音乐，不再阻塞。"""
        peak = self.peak()
        if peak < self.threshold:
            self._continuous_start = None
            self._ignored = False
            return False
        now = time.monotonic()
        if self._continuous_start is None:
            self._continuous_start = now
        if now - self._continuous_start > self.music_after:
            self._ignored = True
        return not self._ignored

    def wait_quiet(self, timeout: float = 4.0) -> float:
        """等到安静（或超时），返回实际等待秒数。"""
        started = time.monotonic()
        deadline = started + max(0.0, float(timeout))
        while time.monotonic() < deadline and self.busy():
            time.sleep(0.2)
        return time.monotonic() - started

    def close(self) -> None:
        _release(self._meter)
        _release(self._device)
        _release(self._enumerator)
        self._meter = None
        self._device = None
        self._enumerator = None

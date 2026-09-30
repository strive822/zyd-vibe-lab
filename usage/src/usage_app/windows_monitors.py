"""Physical monitor topology avoids Qt's mixed-DPI gaps becoming false edges."""
from __future__ import annotations

import ctypes
import os
from ctypes import wintypes

from .desktop_geometry import Rect


class _MonitorInfo(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT), ("rcWork", wintypes.RECT),
                ("dwFlags", wintypes.DWORD), ("szDevice", wintypes.WCHAR * 32)]


def physical_monitor_rects() -> dict[str, Rect]:
    if os.name != "nt":
        return {}
    api = ctypes.WinDLL("User32.dll", use_last_error=True)
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HANDLE, wintypes.HDC,
                                      ctypes.POINTER(wintypes.RECT), wintypes.LPARAM)
    api.EnumDisplayMonitors.argtypes = [wintypes.HDC, ctypes.POINTER(wintypes.RECT), callback_type, wintypes.LPARAM]
    api.EnumDisplayMonitors.restype = wintypes.BOOL
    api.GetMonitorInfoW.argtypes = [wintypes.HANDLE, ctypes.POINTER(_MonitorInfo)]
    api.GetMonitorInfoW.restype = wintypes.BOOL
    result = {}
    def collect(handle: int, dc: int, rect: ctypes._Pointer[wintypes.RECT], parameter: int) -> bool:
        info = _MonitorInfo()
        info.cbSize = ctypes.sizeof(info)
        if api.GetMonitorInfoW(handle, ctypes.byref(info)):
            area = info.rcMonitor
            result[info.szDevice] = Rect(area.left, area.top, area.right - area.left, area.bottom - area.top)
        return True
    if not api.EnumDisplayMonitors(None, None, callback_type(collect), 0):
        return {}
    return result

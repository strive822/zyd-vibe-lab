"""Repair a lost topmost layer without activating or showing a hidden window."""
from __future__ import annotations

import ctypes
import os
from ctypes import wintypes


class WindowVisibility:
    def __init__(self) -> None:
        self.api = ctypes.WinDLL("user32", use_last_error=True)
        self.dwm = ctypes.WinDLL("dwmapi", use_last_error=True)
        self.api.IsWindowVisible.argtypes = [wintypes.HWND]
        self.api.IsWindowVisible.restype = wintypes.BOOL
        self.api.IsIconic.argtypes = [wintypes.HWND]
        self.api.IsIconic.restype = wintypes.BOOL
        self.api.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        self.api.GetWindow.argtypes = [wintypes.HWND, wintypes.UINT]
        self.api.GetWindow.restype = wintypes.HWND
        self.api.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
        self.api.GetWindowLongW.restype = ctypes.c_long
        self.api.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
                                         ctypes.c_int, ctypes.c_int, wintypes.UINT]
        self.api.SetWindowPos.restype = wintypes.BOOL
        self.dwm.DwmGetWindowAttribute.argtypes = [wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
        self.dwm.DwmGetWindowAttribute.restype = ctypes.c_long

    def _shown(self, hwnd: int) -> bool:
        if not self.api.IsWindowVisible(hwnd) or self.api.IsIconic(hwnd):
            return False
        cloaked = wintypes.DWORD()
        result = self.dwm.DwmGetWindowAttribute(hwnd, 14, ctypes.byref(cloaked), ctypes.sizeof(cloaked))
        return result == 0 and cloaked.value == 0

    def repair(self, hwnd: int) -> bool:
        pid = wintypes.DWORD()
        self.api.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value != os.getpid() or not self._shown(hwnd):
            return False
        displaced = not self.api.GetWindowLongW(hwnd, -20) & 0x00000008  # WS_EX_TOPMOST
        above = self.api.GetWindow(hwnd, 3)  # GW_HWNDPREV: native order, not just the style flag.
        seen = {hwnd}
        # Window handles may disappear or move during enumeration. Bound the
        # walk and reject cycles rather than blocking the Qt event loop.
        for _ in range(256):
            if displaced or not above or above in seen:
                break
            seen.add(above)
            if (self._shown(above) and not self.api.GetWindowLongW(above, -20) & 0x00000008
                    and self.api.GetWindow(above, 4) != hwnd):  # Preserve our owned popup's order.
                displaced = True
                break
            above = self.api.GetWindow(above, 3)
        if not displaced:
            return False  # Other topmost tools/menus can legitimately be above us.
        # HWND_TOPMOST; NOSIZE | NOMOVE | NOACTIVATE | NOOWNERZORDER.
        # No SHOWWINDOW: explicit tray hiding is never undone here.
        return bool(self.api.SetWindowPos(hwnd, wintypes.HWND(-1), 0, 0, 0, 0, 0x0213))

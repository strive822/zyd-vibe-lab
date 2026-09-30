"""Read back CF_UNICODETEXT through the Windows clipboard API.

This returns only a match result. It never logs clipboard content.
"""

from __future__ import annotations

from _paths import SOURCE as SOURCE

import ctypes
import time


CF_UNICODETEXT = 13


def clipboard_matches(expected: str, attempts: int = 4) -> bool:
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    user32.OpenClipboard.argtypes = [ctypes.c_void_p]
    user32.OpenClipboard.restype = ctypes.c_int
    user32.GetClipboardData.argtypes = [ctypes.c_uint]
    user32.GetClipboardData.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    for _ in range(attempts):
        if user32.OpenClipboard(None):
            try:
                handle = user32.GetClipboardData(CF_UNICODETEXT)
                if not handle:
                    return False
                pointer = kernel32.GlobalLock(handle)
                if not pointer:
                    return False
                try:
                    return ctypes.wstring_at(pointer) == expected
                finally:
                    kernel32.GlobalUnlock(handle)
            finally:
                user32.CloseClipboard()
        time.sleep(0.025)
    return False


if __name__ == "__main__":
    import sys
    print("match" if clipboard_matches(sys.argv[1]) else "not-matched")

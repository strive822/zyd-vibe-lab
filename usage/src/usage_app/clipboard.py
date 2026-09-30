"""Verified CF_UNICODETEXT transfer; no clipboard history, paste or background reads."""
from __future__ import annotations

import ctypes
import os
from ctypes import wintypes
from typing import Protocol


class ClipboardError(Exception):
    pass


class ClipboardWriter(Protocol):
    def write(self, owner: int, text: str) -> None: ...


def windows_text(text: str) -> str:
    # CF_UNICODETEXT specifies CRLF. Body files remain unchanged; characters,
    # spaces, tabs and logical line breaks are preserved.
    return text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")


class WindowsClipboard:
    def __init__(self) -> None:
        if os.name != "nt":
            raise ClipboardError("此功能需要 Windows 剪贴板")
        self.user = ctypes.WinDLL("user32.dll", use_last_error=True)
        self.memory = ctypes.WinDLL("kernel32.dll", use_last_error=True)
        self.user.OpenClipboard.argtypes = [wintypes.HWND]
        self.user.OpenClipboard.restype = wintypes.BOOL
        self.user.CloseClipboard.argtypes = []
        self.user.CloseClipboard.restype = wintypes.BOOL
        self.user.EmptyClipboard.argtypes = []
        self.user.EmptyClipboard.restype = wintypes.BOOL
        self.user.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
        self.user.SetClipboardData.restype = wintypes.HANDLE
        self.user.GetClipboardData.argtypes = [wintypes.UINT]
        self.user.GetClipboardData.restype = wintypes.HANDLE
        self.memory.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
        self.memory.GlobalAlloc.restype = wintypes.HGLOBAL
        self.memory.GlobalLock.argtypes = [wintypes.HGLOBAL]
        self.memory.GlobalLock.restype = ctypes.c_void_p
        self.memory.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
        self.memory.GlobalUnlock.restype = wintypes.BOOL
        self.memory.GlobalFree.argtypes = [wintypes.HGLOBAL]
        self.memory.GlobalFree.restype = wintypes.HGLOBAL
        self.memory.GlobalSize.argtypes = [wintypes.HGLOBAL]
        self.memory.GlobalSize.restype = ctypes.c_size_t

    def write(self, owner: int, text: str) -> None:
        if not owner or not text or "\x00" in text:
            raise ClipboardError("正文为空或包含不可复制字符")
        expected = windows_text(text)
        raw = (expected + "\x00").encode("utf-16-le")
        handle = self.memory.GlobalAlloc(0x0002, len(raw))  # GMEM_MOVEABLE
        if not handle:
            raise ClipboardError("无法准备剪贴板内容，请重试")
        transferred = False
        opened = False
        try:
            pointer = self.memory.GlobalLock(handle)
            if not pointer:
                raise ClipboardError("无法准备剪贴板内容，请重试")
            ctypes.memmove(pointer, raw, len(raw))
            self.memory.GlobalUnlock(handle)
            if not self.user.OpenClipboard(owner):
                raise ClipboardError("剪贴板暂时被占用，请重试")
            opened = True
            if not self.user.EmptyClipboard() or not self.user.SetClipboardData(13, handle):
                raise ClipboardError("剪贴板写入失败，请重试")
            transferred = True  # Windows now owns this handle; never free it.
            actual = self.user.GetClipboardData(13)
            if not actual:
                raise ClipboardError("写入后无法核验，请重试")
            pointer = self.memory.GlobalLock(actual)
            if not pointer:
                raise ClipboardError("写入后无法核验，请重试")
            try:
                if self.memory.GlobalSize(actual) < len(raw) or ctypes.string_at(pointer, len(raw)) != raw:
                    raise ClipboardError("写入后无法核验，请重试")
            finally:
                self.memory.GlobalUnlock(actual)
        finally:
            if opened:
                self.user.CloseClipboard()
            if not transferred:
                self.memory.GlobalFree(handle)

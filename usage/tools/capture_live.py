"""Crop the actual desktop pixels of the running M1 window on Windows."""

from __future__ import annotations

from _paths import EVIDENCE

import ctypes
import sys
import time
from ctypes.wintypes import POINT, RECT
from pathlib import Path

from PIL import Image, ImageGrab
from PySide6.QtCore import QPointF

from main import leaf_path


user32 = ctypes.WinDLL("user32", use_last_error=True)
user32.FindWindowW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p]
user32.FindWindowW.restype = ctypes.c_void_p
user32.GetWindowRect.argtypes = [ctypes.c_void_p, ctypes.POINTER(RECT)]
user32.GetWindowRect.restype = ctypes.c_int
user32.GetDpiForWindow.argtypes = [ctypes.c_void_p]
user32.GetDpiForWindow.restype = ctypes.c_uint
user32.GetCursorPos.argtypes = [ctypes.POINTER(POINT)]
user32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]

handle = user32.FindWindowW(None, "usage · Visual Prototype")
if not handle:
    raise SystemExit("Running window not found")
rect = RECT()
if not user32.GetWindowRect(handle, ctypes.byref(rect)):
    raise SystemExit("Window rect not available")

expanded = "--expanded" in sys.argv
out = Path(EVIDENCE / "m1-rework/live-expanded-leaf.png" if expanded else "evidence/m1-rework/live-d38-ball-crop.png")
out.parent.mkdir(parents=True, exist_ok=True)
ratio = user32.GetDpiForWindow(handle) / 96
bbox = tuple(round(v * ratio) for v in (rect.left, rect.top, rect.right, rect.bottom))
original_cursor = POINT()
user32.GetCursorPos(ctypes.byref(original_cursor))
try:
    if expanded:
        # Move briefly to the visible dock ball; restore the user's pointer.
        user32.SetCursorPos(rect.right - 10, rect.top + 130)
        time.sleep(1.15)
    window_pixels = ImageGrab.grab(bbox=bbox, all_screens=True)
finally:
    if expanded:
        user32.SetCursorPos(original_cursor.x, original_cursor.y)

if expanded:
    # Keep only real leaf pixels, avoiding unrelated desktop content in the evidence.
    local_box = (round(72 * ratio), round(20 * ratio), round(292 * ratio), round(240 * ratio))
    actual = window_pixels.crop(local_box).convert("RGB")
    mask = Image.new("L", actual.size)
    data = mask.load()
    shape = leaf_path()
    for y in range(actual.height):
        for x in range(actual.width):
            if shape.contains(QPointF(72 + x / ratio, 20 + y / ratio)):
                data[x, y] = 255
    output = Image.new("RGB", actual.size, "#dfe3dc")
    output.paste(actual, (0, 0), mask)
    output.save(out)
else:
    crop = (window_pixels.width - round(42 * ratio), round(90 * ratio),
            window_pixels.width, round(170 * ratio))
    window_pixels.crop(crop).save(out)
print(f"Captured actual {'expanded leaf' if expanded else 'docked ball'} pixels at {ratio:g} scale to {out}")

"""Capture a real mouse-driven widget interaction without moving the pointer.

The Windows window region is copied for each frame. Desktop pixels behind the
transparent shape are replaced with a neutral background before saving. The
native hit region includes drawing margin, so these neutralized frames are
for pointer/geometry evidence, not final contour-color judgment.
"""

from __future__ import annotations

import argparse
import ctypes
import json
import time
from ctypes import wintypes
from pathlib import Path

# Query the target HWND and its region in physical pixels. A DPI-unaware
# inspector receives virtualized, sparsely sampled region rectangles at 150%.
user32 = ctypes.WinDLL("user32", use_last_error=True)
user32.SetProcessDpiAwarenessContext.argtypes = [ctypes.c_void_p]
user32.SetProcessDpiAwarenessContext.restype = wintypes.BOOL
if not user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)):
    raise RuntimeError("Per-monitor DPI awareness could not be enabled for capture")

from PIL import Image, ImageDraw, ImageFilter, ImageGrab
from main import DOCK_EXPOSURE


TITLE = "usage · Visual Prototype"
BACKGROUND = "#dfe3dc"


class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class RGNDATAHEADER(ctypes.Structure):
    _fields_ = [("dwSize", wintypes.DWORD), ("iType", wintypes.DWORD),
                ("nCount", wintypes.DWORD), ("nRgnSize", wintypes.DWORD),
                ("rcBound", RECT)]


gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
user32.FindWindowW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p]
user32.FindWindowW.restype = ctypes.c_void_p
user32.GetWindowRect.argtypes = [ctypes.c_void_p, ctypes.POINTER(RECT)]
user32.GetWindowRect.restype = wintypes.BOOL
user32.GetDpiForWindow.argtypes = [ctypes.c_void_p]
user32.GetDpiForWindow.restype = wintypes.UINT
user32.GetWindowRgn.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
user32.GetWindowRgn.restype = ctypes.c_int
user32.GetCursorPos.argtypes = [ctypes.POINTER(POINT)]
user32.GetCursorPos.restype = wintypes.BOOL
user32.WindowFromPoint.argtypes = [POINT]
user32.WindowFromPoint.restype = ctypes.c_void_p
user32.GetForegroundWindow.argtypes = []
user32.GetForegroundWindow.restype = ctypes.c_void_p
gdi32.CreateRectRgn.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
gdi32.CreateRectRgn.restype = ctypes.c_void_p
gdi32.GetRgnBox.argtypes = [ctypes.c_void_p, ctypes.POINTER(RECT)]
gdi32.GetRgnBox.restype = ctypes.c_int
gdi32.GetRegionData.argtypes = [ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p]
gdi32.GetRegionData.restype = wintypes.DWORD
gdi32.PtInRegion.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
gdi32.PtInRegion.restype = wintypes.BOOL
gdi32.DeleteObject.argtypes = [ctypes.c_void_p]
gdi32.DeleteObject.restype = wintypes.BOOL


def window() -> tuple[int, RECT, int]:
    hwnd = user32.FindWindowW(None, TITLE)
    if not hwnd:
        raise RuntimeError("Running Visual Prototype window not found")
    rect = RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        raise RuntimeError("GetWindowRect failed")
    dpi = int(user32.GetDpiForWindow(hwnd))
    return hwnd, rect, dpi


def region(hwnd: int) -> tuple[int, RECT, list[RECT], dict[str, bool]]:
    handle = gdi32.CreateRectRgn(0, 0, 0, 0)
    if not handle:
        raise RuntimeError("CreateRectRgn failed")
    try:
        kind = user32.GetWindowRgn(hwnd, handle)
        if kind not in (2, 3):
            raise RuntimeError(f"GetWindowRgn returned {kind}")
        box = RECT()
        gdi32.GetRgnBox(handle, ctypes.byref(box))
        size = int(gdi32.GetRegionData(handle, 0, None))
        if size < ctypes.sizeof(RGNDATAHEADER):
            raise RuntimeError("GetRegionData returned no rectangles")
        data = ctypes.create_string_buffer(size)
        if gdi32.GetRegionData(handle, size, data) != size:
            raise RuntimeError("GetRegionData failed")
        header = RGNDATAHEADER.from_buffer_copy(data)
        if header.nCount > 100_000:
            raise RuntimeError("Unexpectedly large window region")
        offset = ctypes.sizeof(RGNDATAHEADER)
        rect_array = (RECT * header.nCount).from_buffer_copy(data, offset)
        scale = user32.GetDpiForWindow(hwnd) / 96
        probes = {(x, y): bool(gdi32.PtInRegion(handle, round(x * scale), round(y * scale)))
                  for x, y in ((5, 5), (150, 130), (265, 130), (290, 130))}
        return kind, box, list(rect_array), {f"{x},{y}": hit for (x, y), hit in probes.items()}
    finally:
        gdi32.DeleteObject(handle)


def physical_bbox(rect: RECT, dpi: int, region_box: RECT) -> tuple[tuple[int, int, int, int], float]:
    """Confirm that DPI-aware Win32 and ImageGrab use physical pixels."""
    returned_width = rect.right - rect.left
    ratio = dpi / 96
    # The native region can extend beyond the right edge of the Qt window.
    if abs(returned_width - 300 * ratio) <= 3 and region_box.left < returned_width:
        return (rect.left, rect.top, rect.right, rect.bottom), 1.0
    raise RuntimeError(f"Cannot align window region {region_box.right} with window width {returned_width} at dpi {dpi}")


def visible_frame(hwnd: int, rect: RECT, dpi: int) -> tuple[Image.Image, dict]:
    kind, box, rectangles, probes = region(hwnd)
    bbox, scale = physical_bbox(rect, dpi, box)
    screen = ImageGrab.grab(bbox=bbox, all_screens=True).convert("RGB")
    mask = Image.new("L", screen.size)
    draw = ImageDraw.Draw(mask)
    for item in rectangles:
        draw.rectangle((round(item.left * scale), round(item.top * scale),
                        round(item.right * scale) - 1, round(item.bottom * scale) - 1), fill=255)
    # Qt intentionally gives the native hit mask a few DIP of drawing margin.
    # Shrink that margin for evidence. A few underlying desktop pixels can
    # still enter near curved edges and resemble dark outlines on light ground.
    mask = mask.filter(ImageFilter.MinFilter(5))
    output = Image.new("RGB", screen.size, BACKGROUND)
    output.paste(screen, (0, 0), mask)
    cursor = POINT()
    user32.GetCursorPos(ctypes.byref(cursor))
    return output, {"region_kind": kind, "region_rectangles": len(rectangles),
                    "region_box": [box.left, box.top, box.right, box.bottom],
                    "region_probes": probes, "mask_scale": scale,
                    "cursor": [cursor.x, cursor.y],
                    "pointer_on_widget": bool(user32.WindowFromPoint(cursor) == hwnd),
                    "widget_foreground": bool(user32.GetForegroundWindow() == hwnd)}


def wait_for_physical_dock_hover(hwnd: int, rect: RECT, dpi: int, timeout: float) -> None:
    scale = dpi / 96
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        cursor = POINT()
        user32.GetCursorPos(ctypes.byref(cursor))
        if (rect.right - round(DOCK_EXPOSURE * scale) <= cursor.x < rect.right
                and rect.top + round(94 * scale) <= cursor.y < rect.top + round(166 * scale)
                and user32.WindowFromPoint(cursor) == hwnd):
            return
        time.sleep(.05)
    raise TimeoutError("No physical pointer entry into the dock ball before timeout")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inspect", action="store_true")
    parser.add_argument("--seconds", type=float, default=8.0)
    parser.add_argument("--fps", type=int, default=10)
    parser.add_argument("--wait-for-hover", action="store_true")
    parser.add_argument("--wait-timeout", type=float, default=180.0)
    parser.add_argument("--out", type=Path, default=Path("evidence/m1-rework/live-mouse-uat.gif"))
    args = parser.parse_args()
    if not 1 <= args.seconds <= 30 or not 1 <= args.fps <= 20:
        parser.error("seconds must be 1–30 and fps 1–20")
    hwnd, rect, dpi = window()
    if args.inspect:
        frame, meta = visible_frame(hwnd, rect, dpi)
        print(json.dumps({"window_rect": [rect.left, rect.top, rect.right, rect.bottom],
                          "dpi": dpi, "captured_size": frame.size, **meta}, ensure_ascii=False))
        return
    if args.wait_for_hover:
        wait_for_physical_dock_hover(hwnd, rect, dpi, args.wait_timeout)
    frames: list[Image.Image] = []
    samples: list[dict] = []
    start = time.monotonic()
    count = round(args.seconds * args.fps)
    for index in range(count):
        target = start + index / args.fps
        if target > time.monotonic():
            time.sleep(target - time.monotonic())
        frame, meta = visible_frame(hwnd, rect, dpi)
        frames.append(frame)
        samples.append({"elapsed_ms": round((time.monotonic() - start) * 1000), **meta})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(args.out, save_all=True, append_images=frames[1:], duration=round(1000 / args.fps), loop=0)
    args.out.with_suffix(".json").write_text(json.dumps({"source": "ImageGrab of real Windows window",
                                                   "pointer_control": "none",
                                                   "window_rect": [rect.left, rect.top, rect.right, rect.bottom],
                                                   "dpi": dpi, "samples": samples}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Captured {len(frames)} physical desktop frames to {args.out}")


if __name__ == "__main__":
    main()

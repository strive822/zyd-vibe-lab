"""Record the running Windows widget while a person drags it between edges.

The recorder never moves the pointer. Each frame follows the current HWND
rectangle and masks pixels outside its native region. Coordinates and hit
state are saved beside the GIF so a physical path can be audited separately
from scripted Qt renders.
"""

from __future__ import annotations

from _paths import EVIDENCE

import argparse
import json
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from record_live_uat import BACKGROUND, visible_frame, wait_for_physical_dock_hover, window


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=float, default=20.0)
    parser.add_argument("--fps", type=int, default=10)
    parser.add_argument("--wait-for-hover", action="store_true")
    parser.add_argument("--wait-timeout", type=float, default=180.0)
    parser.add_argument("--out", type=Path, default=Path(EVIDENCE / "m1-r2/native-four-edge.gif"))
    args = parser.parse_args()
    if not 1 <= args.seconds <= 30 or not 1 <= args.fps <= 20:
        parser.error("seconds must be 1-30 and fps 1-20")

    first_hwnd, first_rect, first_dpi = window()
    if args.wait_for_hover:
        wait_for_physical_dock_hover(first_hwnd, first_rect, first_dpi, args.wait_timeout)

    frames: list[Image.Image] = []
    samples: list[dict] = []
    font = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 16)
    started = time.monotonic()
    for index in range(round(args.seconds * args.fps)):
        due = started + index / args.fps
        if due > time.monotonic():
            time.sleep(due - time.monotonic())
        hwnd, rect, dpi = window()
        if hwnd != first_hwnd:
            raise RuntimeError("The original widget HWND changed during recording")
        image, meta = visible_frame(hwnd, rect, dpi)
        canvas = Image.new("RGB", (500, 500), BACKGROUND)
        canvas.paste(image, ((500 - image.width) // 2, 36 + (450 - image.height) // 2))
        draw = ImageDraw.Draw(canvas)
        elapsed_ms = round((time.monotonic() - started) * 1000)
        draw.text((10, 9), f"{elapsed_ms / 1000:04.1f}s  {rect.left},{rect.top}  {image.width}x{image.height}",
                  fill="#1e2119", font=font)
        draw.text((10, 475), f"pointer {'hit' if meta['pointer_on_widget'] else 'away'}  focus {'yes' if meta['widget_foreground'] else 'no'}",
                  fill="#1e2119", font=font)
        frames.append(canvas)
        samples.append({"elapsed_ms": elapsed_ms,
                        "window_rect": [rect.left, rect.top, rect.right, rect.bottom],
                        "dpi": dpi, **meta})

    args.out.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(args.out, save_all=True, append_images=frames[1:],
                   duration=round(1000 / args.fps), loop=0, optimize=True)
    args.out.with_suffix(".json").write_text(json.dumps({
        "source": "ImageGrab of the moving Windows window, masked by its native region",
        "pointer_control": "none",
        "initial_hwnd": first_hwnd,
        "samples": samples,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Captured {len(frames)} physical frames to {args.out}")


if __name__ == "__main__":
    main()

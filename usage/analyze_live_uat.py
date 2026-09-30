"""Build an inspection sheet from a physical mouse recording and Win32 trace."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


parser = argparse.ArgumentParser()
parser.add_argument("gif", type=Path)
args = parser.parse_args()
metadata = json.loads(args.gif.with_suffix(".json").read_text(encoding="utf-8"))
samples = metadata["samples"]
clip = Image.open(args.gif)
timeline: list[tuple[int, int, Image.Image]] = []
elapsed = 0
for index in range(clip.n_frames):
    clip.seek(index)
    duration = int(clip.info.get("duration", 100))
    timeline.append((elapsed, elapsed + duration, clip.convert("RGB").copy()))
    elapsed += duration

width, height = timeline[0][2].size
targets = [min(ms, elapsed - 1) for ms in range(0, elapsed, 500)]
font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 17)
columns = 5
clean = Image.new("RGB", (width * columns, (height + 34) * math.ceil(len(targets) / columns)), "#dfe3dc")
pointer = clean.copy()
origin = metadata["window_rect"]
for index, target in enumerate(targets):
    frame = next((image for start, end, image in timeline if start <= target < end), timeline[-1][2])
    sample = min(samples, key=lambda item: abs(item["elapsed_ms"] - target))
    x0 = index % columns * width
    y0 = index // columns * (height + 34)
    for sheet in (clean, pointer):
        sheet.paste(frame, (x0, y0 + 34))
        ImageDraw.Draw(sheet).text((x0 + 8, y0 + 6),
                                   f"{target/1000:.1f}s  hit={int(sample['pointer_on_widget'])} focus={int(sample['widget_foreground'])}",
                                   font=font, fill="#1e2119")
    px = sample["cursor"][0] - origin[0]
    py = sample["cursor"][1] - origin[1]
    if 0 <= px < width and 0 <= py < height:
        draw = ImageDraw.Draw(pointer)
        cx, cy = x0 + px, y0 + 34 + py
        draw.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), outline="#b63235", width=2)

clean_path = args.gif.with_name(args.gif.stem + "-contact.png")
pointer_path = args.gif.with_name(args.gif.stem + "-pointer-contact.png")
clean.save(clean_path)
pointer.save(pointer_path)
summary = {
    "recorded_samples": len(samples),
    "encoded_frames": clip.n_frames,
    "duration_ms": samples[-1]["elapsed_ms"],
    "expanded_samples": sum(item["region_rectangles"] > 100 for item in samples),
    "pointer_widget_samples": sum(item["pointer_on_widget"] for item in samples),
    "widget_foreground_samples": sum(item["widget_foreground"] for item in samples),
    "contact": str(clean_path),
    "pointer_contact": str(pointer_path),
}
print(json.dumps(summary, ensure_ascii=False))

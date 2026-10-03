"""Capture unread reminder in all four dock orientations, including bell sway."""

from __future__ import annotations

from _paths import EVIDENCE

import argparse
import io
import json
import os
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--scale", type=float, default=1.0, help="Multiplier relative to the native display DPI")
parser.add_argument("--expected-dpr", type=float)
args = parser.parse_args()
os.environ["QT_SCALE_FACTOR"] = str(args.scale)

from PIL import Image, ImageDraw, ImageFont  # noqa: E402 - scale/DPI must be configured before graphics imports
from PySide6.QtCore import QBuffer, QIODevice  # noqa: E402 - scale/DPI must be configured before graphics imports
from PySide6.QtWidgets import QApplication  # noqa: E402 - scale/DPI must be configured before graphics imports

from main import LeafPrototype  # noqa: E402 - scale/DPI must be configured before graphics imports


app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)
widget = LeafPrototype(scenario="low")
widget.move(100, 100)
widget.show()
widget._pulse.stop()
widget._tick.stop()
widget._now = lambda: widget._base_now
widget.trigger_reminder_demo()
app.processEvents()
ratio = widget.devicePixelRatioF()
if args.expected_dpr is not None:
    assert abs(ratio - args.expected_dpr) < .01, (ratio, args.expected_dpr)
out = Path(EVIDENCE / f"m1-r3/reminder/{ratio:g}")
out.mkdir(parents=True, exist_ok=True)


def capture(edge: str, progress: float, name: str) -> Image.Image:
    widget.set_dock_edge(edge)
    widget.set_expansion_progress(progress)
    widget.update()
    app.processEvents()
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    assert widget.grab().save(buffer, "PNG")
    image = Image.open(io.BytesIO(bytes(buffer.data()))).convert("RGBA")
    image.save(out / f"{name}.png")
    return image


rows = []
for edge in ("right", "left", "top", "bottom"):
    widget._reminder_animation.setCurrentTime(0)
    dock = capture(edge, 0, f"{edge}-dock")
    expanded = capture(edge, 1, f"{edge}-expanded")
    rows.append((edge, dock, expanded))

cell_w = max(image.width for _, dock, expanded in rows for image in (dock, expanded))
cell_h = max(image.height for _, dock, expanded in rows for image in (dock, expanded))
label_h = round(28 * ratio)
sheet = Image.new("RGB", (cell_w * 2, (cell_h + label_h) * 4), "#dfe3dc")
draw = ImageDraw.Draw(sheet)
font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", round(12 * ratio))
for row, (edge, dock, expanded) in enumerate(rows):
    for col, (state, image) in enumerate((("dock", dock), ("expanded", expanded))):
        x, y = col * cell_w, row * (cell_h + label_h)
        draw.text((x + 8, y + 6), f"{edge} / {state}", fill="#1e2119", font=font)
        base = Image.new("RGBA", image.size, "#dfe3dc")
        base.alpha_composite(image)
        sheet.paste(base.convert("RGB"), (x, y + label_h))
sheet.save(out / "four-edges.png")

# A full animation cycle through Qt's property animation uses the same paint route
# as the running widget. Verify reminder-colored ink stays clear of the top edge.
top_frames = []
target = widget.theme.reminder
target_rgb = (target.red(), target.green(), target.blue())
measurements = []
for ms in (0, 80, 150, 220, 300, 400, 520, 640):
    widget._reminder_animation.setCurrentTime(ms)
    image = capture("top", 0, f"top-pulse-{ms:03d}")
    top_frames.append(image)
    candidates = []
    for y in range(min(image.height, round(20 * ratio))):
        for x in range(round(152 * ratio), min(image.width, round(169 * ratio))):
            red, green, blue, alpha = image.getpixel((x, y))
            if alpha >= 180 and sum(abs(a - b) for a, b in zip((red, green, blue), target_rgb)) < 65:
                candidates.append((x, y))
    assert candidates, (ms, target_rgb)
    minimum_y = min(y for _, y in candidates)
    assert minimum_y >= round(1.5 * ratio), (ms, minimum_y, ratio)
    measurements.append({"time_ms": ms, "ink_top_px": minimum_y,
                         "ink_bottom_px": max(y for _, y in candidates)})

gif_frames = []
for frame in top_frames:
    base = Image.new("RGBA", frame.size, "#dfe3dc")
    base.alpha_composite(frame)
    gif_frames.append(base.convert("RGB"))
gif_frames[0].save(out / "top-sway.gif", save_all=True, append_images=gif_frames[1:], duration=90, loop=0)
(out / "measurements.json").write_text(json.dumps({"dpr": ratio, "top_reminder_ink": measurements}, indent=2), encoding="utf-8")
widget.close()
print(json.dumps({"dpr": ratio, "four_edges": True, "pulse_frames": len(top_frames),
                  "minimum_top_ink_px": min(item["ink_top_px"] for item in measurements)}))

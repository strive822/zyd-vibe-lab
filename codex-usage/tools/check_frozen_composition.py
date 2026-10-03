"""Deterministic native Qt renders of the frozen core and current inherited core."""
from __future__ import annotations

from _paths import SOURCE, EVIDENCE

import hashlib
import json
import subprocess
import sys

from PIL import Image, ImageChops




def main() -> int:
    output = EVIDENCE / "m6"
    output.mkdir(parents=True, exist_ok=True)
    code = """import sys
from datetime import datetime
sys.path.insert(0,sys.argv[1])
import main
from PySide6.QtWidgets import QApplication
app=QApplication([])
w=main.LeafPrototype(expanded=True,reduced_motion=True)
w._pulse.stop()
w._tick.stop()
w._now=lambda:datetime.fromisoformat('2026-09-27T08:00:00+08:00')
w.ensurePolished()
app.processEvents()
assert w.grab().save(sys.argv[2])
w.close()
"""
    frozen = EVIDENCE / "m1-r4" / "frozen-source"
    paths = [output / "frozen-core.png", output / "current-core.png"]
    for directory, image in zip((frozen, SOURCE), paths):
        subprocess.run([sys.executable, "-B", "-c", code, str(directory), str(image)], check=True)
    with Image.open(paths[0]) as reference, Image.open(paths[1]) as current:
        identical = reference.size == current.size and ImageChops.difference(reference.convert("RGBA"), current.convert("RGBA")).getbbox() is None
        report = {"identical": identical, "size": list(current.size),
                  "frozenMainSha256": hashlib.sha256((frozen / "main.py").read_bytes()).hexdigest(),
                  "currentMainSha256": hashlib.sha256((SOURCE / "main.py").read_bytes()).hexdigest(),
                  "frozenRenderSha256": hashlib.sha256(paths[0].read_bytes()).hexdigest(),
                  "currentRenderSha256": hashlib.sha256(paths[1].read_bytes()).hexdigest(),
                  "frozenImage": paths[1].name if identical else paths[0].name,
                  "currentImage": paths[1].name,
                  "boundary": "Native Qt render, same fixed data/clock and 150% target device. Tests inherited core composition; production data/settings/interaction have separate checks."}
    if identical:
        paths[0].unlink()  # Equality and both hashes remain in the receipt; keep one image.
    (output / "frozen-regression.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))
    return 0 if identical else 1


if __name__ == "__main__":
    raise SystemExit(main())

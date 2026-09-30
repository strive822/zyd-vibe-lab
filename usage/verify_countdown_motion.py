"""Exercise real Qt countdown frame delivery on a non-displayed test surface."""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from time import monotonic

from PySide6.QtCore import QEventLoop, QTimer, Qt
from PySide6.QtWidgets import QApplication

from usage_app.models import Provider, Status
from usage_app.parsers import GLM_PERSONAL_MAPPING, parse_codex, parse_glm
from usage_app.runtime import UsageRuntime
from usage_app.widget import LiveLeaf


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("evidence/m6/countdown-motion"))
    args = parser.parse_args()
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    args.out.mkdir(parents=True, exist_ok=True)

    def pump(milliseconds):
        loop = QEventLoop()
        QTimer.singleShot(milliseconds, loop.quit)
        loop.exec()

    class ObservedLeaf(LiveLeaf):
        def __init__(self, runtime):
            self.frames = []
            self.settled_seconds = []
            self.paint_key = ""
            super().__init__(runtime, expanded=True)

        def _paint_countdown(self, painter, key, current, x, y, size):
            self.paint_key = key
            super()._paint_countdown(painter, key, current, x, y, size)

        def _draw_countdown_fields(self, painter, countdown, x, y, size, width, motion=None, fraction=1):
            if motion is not None:
                self.frames.append((self.paint_key, round(fraction, 4)))
            elif countdown.mode == "HMS" and self.paint_key == "live-glm-5h":
                values = [int(value) for value, _ in countdown.fields]
                seconds = values[0] * 3600 + values[1] * 60 + values[2]
                if not self.settled_seconds or self.settled_seconds[-1] != seconds:
                    self.settled_seconds.append(seconds)
            super()._draw_countdown_fields(painter, countdown, x, y, size, width, motion, fraction)

    with tempfile.TemporaryDirectory(prefix="usage-countdown-") as directory:
        runtime = UsageRuntime(Path(directory))
        runtime.stop()
        now = datetime(2026, 9, 30, 9, tzinfo=UTC)
        for provider, state in runtime.states.items():
            state.account = replace(state.account, enabled=True)
            if provider == Provider.CODEX:
                state.snapshot = parse_codex({"rateLimits": {"primary": {"usedPercent": 25, "windowDurationMins": 300,
                    "resetsAt": int((now + timedelta(hours=10)).timestamp())}, "secondary": {"usedPercent": 40,
                    "windowDurationMins": 10080, "resetsAt": int((now + timedelta(days=1)).timestamp())}}}, state.account, now)
            elif provider == Provider.GLM:
                state.snapshot = parse_glm({"data": {"limits": [
                    {"type": "CREDIT_LIMIT", "unit": 3, "number": 5, "percentage": 20,
                     "nextResetTime": int((now + timedelta(hours=2)).timestamp() * 1000)},
                    {"type": "CREDIT_LIMIT", "unit": 6, "number": 1, "percentage": 30,
                     "nextResetTime": int((now + timedelta(days=2)).timestamp() * 1000)}]}}, state.account, now, GLM_PERSONAL_MAPPING)
            state.status = Status.FRESH
        leaf = ObservedLeaf(runtime)
        leaf.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen)
        leaf._pulse.stop()
        leaf._tick.stop()
        leaf._now = lambda: now
        leaf.set_detail("codex")
        leaf.show()  # Qt paints this surface without displaying another desktop ball.
        pump(260)
        leaf.frames.clear()
        now += timedelta(seconds=1)
        leaf._on_tick()
        pump(240)  # No grab/render/update calls during the frame-delivery observation.
        observations = []
        def verify_delivery(key):
            values = [fraction for observed_key, fraction in leaf.frames if observed_key == key]
            result = {"key": key, "naturalFrames": len(values), "hasIntermediateFrame": any(.1 < value < .9 for value in values),
                      "transitionFinished": not leaf._countdown_motion and not leaf._countdown_frames.isActive()}
            observations.append(result)
            assert len(values) >= 3 and result["hasIntermediateFrame"] and result["transitionFinished"]

        verify_delivery("live-codex-5h")
        assert leaf._countdown_previous["live-codex-5h"].text == "9时59分59秒"
        assert leaf._countdown_previous["live-codex-周"].mode == "HMS"
        leaf.grab().save(str(args.out / "codex-boundary.png"))
        for _ in range(2):
            leaf.frames.clear()
            now += timedelta(seconds=1)
            leaf._on_tick()
            pump(240)
            verify_delivery("live-codex-5h")

        leaf.set_detail("glm")
        pump(220)
        for _ in range(2):
            leaf.frames.clear()
            now += timedelta(seconds=1)
            leaf._on_tick()
            pump(240)
            verify_delivery("live-glm-5h")
            # DHM minute readout is unchanged: no decorative second-by-second motion.
            assert not any(key == "live-glm-周" for key, _ in leaf.frames)
        leaf.grab().save(str(args.out / "glm-repeat.png"))
        leaf.set_detail("codex")
        pump(220)
        leaf.frames.clear()
        now += timedelta(seconds=1)
        leaf._on_tick()
        pump(240)
        verify_delivery("live-codex-5h")

        leaf.reduced_motion = True
        leaf.frames.clear()
        now += timedelta(seconds=1)
        leaf._on_tick()
        pump(240)
        assert not leaf.frames and not leaf._countdown_motion and not leaf._countdown_frames.isActive()
        leaf.reduced_motion = False
        leaf.set_expansion_progress(0)
        now += timedelta(hours=1)
        leaf._on_tick()
        pump(50)
        leaf.expand()
        pump(350)
        assert not leaf._countdown_motion and not leaf._countdown_frames.isActive()
        leaf.grab().save(str(args.out / "reopened.png"))

        # GLM's real source has millisecond resets. Deliberately place its
        # second boundary near the end of a 160ms transition, then let the
        # real clock and production tick run without forced renders.
        state = runtime.states[Provider.GLM]
        state.snapshot = replace(state.snapshot, windows=tuple(
            replace(window, next_recovery_at=window.next_recovery_at.replace(microsecond=761000))
            if window.duration_minutes == 300 else window for window in state.snapshot.windows))
        real_base, began = now.replace(microsecond=610000), monotonic()
        leaf._now = lambda: real_base + timedelta(seconds=monotonic() - began)
        leaf._data_changed()
        leaf.set_detail("glm")
        pump(220)
        began = monotonic()
        leaf._countdown_previous.clear()
        leaf._countdown_motion.clear()
        leaf._countdown_frames.stop()
        leaf.settled_seconds.clear()
        leaf._tick.start(1000)
        leaf._on_tick()
        pump(4200)
        settled = list(leaf.settled_seconds)
        leaf._tick.stop()
        print(json.dumps({"glmSettledSeconds": settled}))
        args.out.joinpath("live-clock-result.json").write_text(json.dumps({
            "settledSeconds": settled, "clockPhaseMicroseconds": 610000, "resetMicroseconds": 761000,
            "consecutive": len(settled) >= 4 and all(before - after == 1 for before, after in zip(settled, settled[1:])),
            "sources": {name: hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in ("main.py", "usage_app/widget.py")},
            "boundary": "Real Qt production tick and real monotonic clock; synthetic millisecond GLM reset, non-displayed surface, no forced grabs."}, indent=2), encoding="utf-8")
        assert len(settled) >= 4 and all(before - after == 1 for before, after in zip(settled, settled[1:]))
        leaf._now = lambda: now
        leaf._on_tick()
        pump(220)

        # Rendering capture is separate from the no-grab delivery assertions above.
        from PIL import Image
        leaf.set_detail("codex")
        pump(220)
        images = [leaf.grab().toImage()]
        now += timedelta(seconds=1)
        leaf._on_tick()
        for _ in range(12):
            pump(20)
            images.append(leaf.grab().toImage())
        rendered = []
        for index, image in enumerate(images):
            path = args.out / f"frame-{index:02}.png"
            image.save(str(path))
            with Image.open(path) as source:
                rendered.append(source.convert("RGB"))
        rendered[0].save(args.out / "countdown.gif", save_all=True, append_images=rendered[1:], duration=20, loop=0)
        checks = {"passed": 5, "checks": ["steady Codex and GLM ticks finish naturally after initial entry",
                   "10-to-9 digit exit and 24h unit switch finish without another UI animation",
                   "unchanged minute readout and reduced motion remain still", "collapsed/reopened view uses current time without replay",
                   "millisecond GLM reset with real clock settles each consecutive second without double jumps"],
                  "glmSettledSeconds": settled,
                  "observations": observations, "nativeDpr": leaf.devicePixelRatioF(),
                  "sources": {name: hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in ("main.py", "usage_app/widget.py")},
                  "boundary": "Real Qt event loop on WA_DontShowOnScreen surface with synthetic data. Natural frame observations contain no grab/render/update calls between tick and completion. GIF separately captures native rendered frames. No physical pointer, live keys, clipboard or second displayed leaf."}
        args.out.joinpath("result.json").write_text(json.dumps(checks, indent=2), encoding="utf-8")
        print(json.dumps(checks))
        leaf.hide()


if __name__ == "__main__":
    main()

"""Reproduce displaced native Z-order in isolated owned Qt windows."""
from __future__ import annotations

from _paths import EVIDENCE

import ctypes
import json
import tempfile
from pathlib import Path

# Enable physical-pixel capture before Qt/graphics imports.
import record_live_uat as capture
from PySide6.QtCore import QEventLoop, Qt, QTimer
from PySide6.QtWidgets import QApplication, QWidget

from usage_app.desktop import DesktopLeaf, screen_key
from usage_app.desktop_geometry import Placement
from usage_app.runtime import UsageRuntime


def pump(milliseconds):
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def main():
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    api = capture.user32
    api.GetWindowLongW.argtypes = [ctypes.c_void_p, ctypes.c_int]
    api.GetWindowLongW.restype = ctypes.c_long
    api.SetWindowPos.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
                                 ctypes.c_int, ctypes.c_int, ctypes.c_uint]
    api.SetWindowPos.restype = ctypes.c_int
    api.IsIconic.argtypes = [ctypes.c_void_p]
    api.IsIconic.restype = ctypes.c_int
    out = EVIDENCE / "m6" / "orb-visibility"
    out.mkdir(parents=True, exist_ok=True)
    checks = {}
    with tempfile.TemporaryDirectory(prefix="usage-visibility-") as directory:
        runtime = UsageRuntime(Path(directory))
        runtime.stop()  # Synthetic defaults; no real account/network/data changes.
        leaf = DesktopLeaf(runtime, reduced_motion=True)
        leaf._visible_hit = lambda x, y: False
        leaf._visibility_timer.stop()
        leaf.show()
        cover = QWidget(None, Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        cover.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        cover.setStyleSheet("background: #233c50")
        top = QWidget(None, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        top.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        top.setStyleSheet("background: #53623c")
        hwnd = int(leaf.winId())

        class StyleView:
            # Windows manages WS_EX_TOPMOST itself; SetWindowLong cannot
            # recreate the incident's inconsistent flag. Model that one
            # stale read while keeping Z-order, timer, hit test and repair native.
            stale_flag = False

            def GetWindowLongW(self, handle, index):
                value = api.GetWindowLongW(handle, index)
                return value | 8 if self.stale_flag and handle == hwnd and index == -20 else value

            def __getattr__(self, name):
                return getattr(api, name)

        style = StyleView()
        leaf._window_visibility.api = style

        def rect():
            native = capture.RECT()
            assert api.GetWindowRect(hwnd, ctypes.byref(native))
            return native

        def point():
            native = rect()
            local = leaf._dock_dial_center("codex")
            ratio = api.GetDpiForWindow(hwnd) / 96
            return capture.POINT(round(native.left + local.x() * ratio), round(native.top + local.y() * ratio))

        def displace(stale_flag=True):
            cover.setGeometry(leaf.geometry())
            cover.show()
            assert api.SetWindowPos(hwnd, ctypes.c_void_p(1), 0, 0, 0, 0, 0x213)  # HWND_BOTTOM
            style.stale_flag = stale_flag
            pump(90)
            assert api.WindowFromPoint(point()) != hwnd
            assert bool(style.GetWindowLongW(hwnd, -20) & 8) == stale_flag

        try:
            checks["production check interval is two seconds"] = leaf._visibility_timer.interval() == 2000
            for edge in ("right", "left", "top", "bottom"):
                leaf.apply_placement(Placement(screen_key(app.primaryScreen()), edge, .5))
                displace()
                before = rect()
                foreground = api.GetForegroundWindow()
                if edge == "right":
                    frame, _ = capture.visible_frame(hwnd, before, api.GetDpiForWindow(hwnd))
                    frame.save(str(out / "regression-covered.png"))
                    leaf._visibility_timer.start()  # Actual production interval, not direct recovery.
                    pump(2150)
                    leaf._visibility_timer.stop()
                else:
                    leaf._reconcile_visibility()
                    pump(90)
                after = rect()
                checks[f"{edge}: stale topmost style and covered native region recover"] = api.WindowFromPoint(point()) == hwnd
                checks[f"{edge}: repair preserves foreground, rectangle and collapsed form"] = (
                    foreground == api.GetForegroundWindow()
                    and (before.left, before.top, before.right, before.bottom) == (after.left, after.top, after.right, after.bottom)
                    and leaf._progress == 0)
                if edge == "right":
                    frame, _ = capture.visible_frame(hwnd, after, api.GetDpiForWindow(hwnd))
                    frame.save(str(out / "regression-recovered.png"))
            events = Path(directory) / "logs" / "events.jsonl"
            count = sum(json.loads(line)["event"] == "window_layer_restored" for line in events.read_text().splitlines())
            for _ in range(20):
                leaf._reconcile_visibility()
            checks["healthy checks never raise again or write repeated recovery events"] = count == 4 and count == len(events.read_text().splitlines())
            displace(stale_flag=False)
            leaf._reconcile_visibility()
            pump(80)
            checks["lost native topmost flag also recovers"] = bool(api.GetWindowLongW(hwnd, -20) & 8) and api.WindowFromPoint(point()) == hwnd

            for attr in ("_menu_open", "_auxiliary_open", "_drag_pending"):
                displace()
                setattr(leaf, attr, True)
                leaf._reconcile_visibility()
                checks[f"{attr} blocks recovery until the interaction ends"] = api.WindowFromPoint(point()) != hwnd
                setattr(leaf, attr, False)
                leaf._reconcile_visibility()
                pump(80)
                checks[f"{attr} release permits recovery"] = api.WindowFromPoint(point()) == hwnd

            leaf.hide_to_tray()
            leaf._visibility_timer.start()
            pump(2150)
            leaf._visibility_timer.stop()
            checks["explicit tray hide survives the real timer and remains hidden"] = not leaf.isVisible()
            leaf.restore_from_tray()
            pump(80)
            checks["explicit tray restore still works"] = leaf.isVisible() and api.WindowFromPoint(point()) == hwnd
            leaf.showMinimized()
            pump(80)
            leaf._reconcile_visibility()
            checks["native minimized window is never unminimized by recovery"] = bool(api.IsIconic(hwnd))
            leaf.showNormal()
            leaf.raise_()
            cover.hide()
            top.setGeometry(leaf.geometry())
            top.show()
            top.raise_()
            pump(100)
            foreground = api.GetForegroundWindow()
            checks["another legitimate topmost tool is not fought or activated"] = (
                api.WindowFromPoint(point()) == int(top.winId())
                and not leaf._window_visibility.repair(hwnd) and api.GetForegroundWindow() == foreground)
            top.hide()
            # A fully expanded leaf follows the same layer policy without collapsing.
            leaf.set_expansion_progress(1)
            cover.setGeometry(leaf.geometry())
            cover.show()
            api.SetWindowPos(hwnd, ctypes.c_void_p(1), 0, 0, 0, 0, 0x213)
            style.stale_flag = True
            pump(40)
            leaf._last_inside = True
            leaf._close_timer.stop()
            leaf._pulse.stop()
            leaf._reconcile_visibility()
            pump(60)
            checks["expanded form is preserved during repair"] = leaf._progress == 1 and leaf.isVisible() and not leaf.isMinimized()
        finally:
            cover.close()
            top.close()
            leaf.quit_app()
        checks["quit stops the visibility timer"] = not leaf._visibility_timer.isActive()
    report = {"passed": sum(checks.values()), "checks": checks,
              "nativeDpr": app.primaryScreen().devicePixelRatio(),
              "boundary": "Owned temporary-data Qt windows; native Z-order displaced, incident's stale WS_EX_TOPMOST read modeled because Windows manages that bit, real two-second timer and native capture/hit/focus checks. No physical input or real account changes. Does not identify the external trigger of the original displacement or prove indefinite idle stability."}
    (out / "regression.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())

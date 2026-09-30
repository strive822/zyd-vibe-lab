"""Read-only counters for the existing leaf; never creates or controls a window."""
from __future__ import annotations

from _paths import ROOT, SOURCE, EVIDENCE

import argparse
import ctypes
import hashlib
import json
import os
import platform
import time
from ctypes import wintypes
from pathlib import Path

from measure_idle import WindowsMeter
from verify_portable import ProcessEntry




class ExistingLeaf:
    def __init__(self, pid: int):
        self.pid = pid
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self.user = ctypes.WinDLL("user32", use_last_error=True)
        self.gdi = ctypes.WinDLL("gdi32", use_last_error=True)
        self.kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
        self.kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
        self.kernel.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
        self.kernel.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
        self.kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self.kernel.OpenProcess.restype = wintypes.HANDLE
        self.kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
        self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        self.user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        self.user.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        self.user.IsWindowVisible.argtypes = [wintypes.HWND]
        self.user.IsIconic.argtypes = [wintypes.HWND]
        self.user.GetDpiForWindow.argtypes = [wintypes.HWND]
        self.user.GetWindowRgn.argtypes = [wintypes.HWND, wintypes.HANDLE]
        self.gdi.CreateRectRgn.argtypes = [ctypes.c_int] * 4
        self.gdi.CreateRectRgn.restype = wintypes.HANDLE
        self.gdi.GetRgnBox.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.RECT)]
        self.gdi.DeleteObject.argtypes = [wintypes.HANDLE]
        self.callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        self.user.EnumWindows.argtypes = [self.callback_type, wintypes.LPARAM]
        handle = self.kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            raise ValueError("Existing owned app process is unavailable")
        try:
            buffer, size = ctypes.create_unicode_buffer(32768), wintypes.DWORD(32768)
            assert self.kernel.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size))
            self.image = Path(buffer.value).resolve()
        finally:
            self.kernel.CloseHandle(handle)
        expected = (ROOT / ".venv-win/Scripts/python.exe").resolve()
        bundled = self.image.is_relative_to(ROOT / "dist") and self.image.name.casefold() in ("python.exe", "pythonw.exe") and self.image.parent.name == "runtime"
        if self.image != expected and not bundled:
            raise ValueError("PID does not belong to this project's known runtime")

    def owned_processes(self):
        snapshot = self.kernel.CreateToolhelp32Snapshot(2, 0)
        assert snapshot and snapshot != ctypes.c_void_p(-1).value
        entries = []
        try:
            entry = ProcessEntry()
            entry.size = ctypes.sizeof(entry)
            more = self.kernel.Process32FirstW(snapshot, ctypes.byref(entry))
            while more:
                entries.append((entry.pid, entry.parent, entry.exe.casefold()))
                more = self.kernel.Process32NextW(snapshot, ctypes.byref(entry))
        finally:
            self.kernel.CloseHandle(snapshot)
        descendants = {self.pid}
        while True:
            expanded = descendants | {pid for pid, parent, exe in entries if parent in descendants}
            if expanded == descendants:
                break
            descendants = expanded
        # A Windows venv launcher can redirect into a child Python runtime.
        # Include that verified ancestry rather than measuring the idle shim.
        return {pid: exe for pid, parent, exe in entries if pid in descendants
                and (pid == self.pid or exe in ("python.exe", "pythonw.exe", "codex.exe"))}

    def idle_condition(self):
        windows = []
        owned = self.owned_processes()
        @self.callback_type
        def collect(window, _):
            owner = wintypes.DWORD()
            self.user.GetWindowThreadProcessId(window, ctypes.byref(owner))
            if owner.value not in owned or not self.user.IsWindowVisible(window) or self.user.IsIconic(window):
                return True
            title = ctypes.create_unicode_buffer(256)
            self.user.GetWindowTextW(window, title, 256)
            # Read metadata only after filtering to this exact owned process.
            if title.value == "usage" or title.value.startswith("usage ·"):
                windows.append((window, title.value))
            return True
        self.user.EnumWindows(collect, 0)
        main = [window for window, title in windows if title == "usage"]
        if len(main) != 1:
            return False, "leaf_not_visible", None
        if len(windows) != 1:
            return False, "settings_or_auxiliary_open", None
        window = main[0]
        ratio = self.user.GetDpiForWindow(window) / 96
        region = self.gdi.CreateRectRgn(0, 0, 0, 0)
        try:
            kind = self.user.GetWindowRgn(window, region)
            bounds = wintypes.RECT()
            if kind <= 1 or not self.gdi.GetRgnBox(region, ctypes.byref(bounds)):
                return False, "leaf_has_no_collapsed_mask", ratio
            width, height = bounds.right - bounds.left, bounds.bottom - bounds.top
            collapsed = width <= 76 * ratio + 2 and height <= 76 * ratio + 2
            return collapsed, "collapsed" if collapsed else "leaf_expanded_or_animating", ratio
        finally:
            self.gdi.DeleteObject(region)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--seconds", type=float, default=200)
    parser.add_argument("--out", type=Path, default=EVIDENCE / "m6/live-idle-performance.json")
    args = parser.parse_args()
    target = ExistingLeaf(args.pid)
    valid, condition, ratio = target.idle_condition()
    if not valid:
        print(json.dumps({"status": "not_started", "condition": condition}))
        return 2
    meter = WindowsMeter()
    starts, latest, owned, samples, violations = {}, {}, set(), [], set()
    start = time.monotonic()
    try:
        while True:
            owned.update(target.owned_processes())
            values = {}
            for identity in {args.pid, *owned}:
                value = meter.sample(identity)
                if value is not None:
                    values[identity] = value
                    latest[identity] = value
                    if not samples:
                        starts[identity] = value[0]
            if args.pid not in values:
                violations.add("target_process_unavailable")
            valid, condition, ratio = target.idle_condition()
            if not valid:
                violations.add(condition)
            samples.append((sum(value[1] for value in values.values()), sum(value[2] for value in values.values())))
            elapsed = time.monotonic() - start
            if elapsed >= args.seconds:
                break
            time.sleep(.05)
    finally:
        meter.close()
    cpu = sum(value[0] - starts.get(identity, 0) for identity, value in latest.items()) / elapsed * 100
    resident = max(sample[0] for sample in samples) / 1024 ** 2
    source = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in (SOURCE / "main.py", SOURCE / "usage_app/desktop.py", SOURCE / "usage_app/widget.py")}
    report = {"status": "inconclusive" if violations else "passed" if cpu < 1 and resident < 200 else "failed",
              "seconds": round(elapsed, 2), "samples": len(samples), "source": source,
              "cpuOneCorePercent": round(cpu, 3), "cpuMachinePercent": round(cpu / (os.cpu_count() or 1), 3),
              "peakResidentMBIncludingOwnedChildren": round(resident, 2),
              "peakPrivateMBIncludingOwnedChildren": round(max(sample[1] for sample in samples) / 1024 ** 2, 2),
              "ownedApplicationProcessesObserved": len(owned), "idleConditionViolations": sorted(violations),
              "platform": platform.platform(), "logicalProcessors": os.cpu_count(), "dpr": ratio,
              "boundary": "Read-only observation of the already running app. No new widget, GUI input or user data access. Only this app and its descendant codex.exe CPU/memory are counted. Any expanded/auxiliary window invalidates the idle gate. Not a long-duration leak or clean-Windows test."}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Reference-device measurement including only the Codex process this widget owns."""
from __future__ import annotations

from _paths import EVIDENCE

import argparse
import ctypes
import json
import os
import platform
import tempfile
import time
from ctypes import wintypes
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from usage_app.adapters import CodexAdapter
from usage_app.desktop import DesktopLeaf, screen_key
from usage_app.desktop_geometry import Placement
from usage_app.models import Provider
from usage_app.runtime import UsageRuntime


class Counters(ctypes.Structure):
    _fields_ = [("cb", wintypes.DWORD), ("faults", wintypes.DWORD)] + [
        (name, ctypes.c_size_t) for name in ("peak_rss", "rss", "peak_paged", "paged", "peak_nonpaged", "nonpaged", "pagefile", "peak_pagefile", "private")]


class WindowsMeter:
    def __init__(self):
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self.psapi = ctypes.WinDLL("psapi", use_last_error=True)
        self.kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self.kernel.OpenProcess.restype = wintypes.HANDLE
        self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
        self.psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        self.handles = {}

    def sample(self, identity):
        if identity not in self.handles:
            handle = self.kernel.OpenProcess(0x0410, False, identity)
            if not handle:
                return None
            self.handles[identity] = handle
        handle = self.handles[identity]
        creation, exit_time, kernel, user = (wintypes.FILETIME() for _ in range(4))
        if not self.kernel.GetProcessTimes(handle, ctypes.byref(creation), ctypes.byref(exit_time), ctypes.byref(kernel), ctypes.byref(user)):
            return None
        seconds = ((kernel.dwHighDateTime << 32) + kernel.dwLowDateTime + (user.dwHighDateTime << 32) + user.dwLowDateTime) / 10_000_000
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        memory_ok = self.psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb)
        return seconds, counters.rss if memory_ok else 0, counters.private if memory_ok else 0

    def close(self):
        for handle in self.handles.values():
            self.kernel.CloseHandle(handle)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=int, default=200)
    parser.add_argument("--with-refresh", action="store_true")
    parser.add_argument("--out", type=Path, default=Path(EVIDENCE / "m6/idle-performance.json"))
    args = parser.parse_args()
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    meter = WindowsMeter()
    report = None
    with tempfile.TemporaryDirectory(prefix="duizhaoye-performance-") as directory:
        runtime = UsageRuntime(Path(directory))
        leaf = DesktopLeaf(runtime)
        leaf.apply_placement(Placement(screen_key(app.primaryScreen()), "left", .5, free_orientation="left"))
        leaf.set_expansion_progress(0)
        leaf.show()
        leaf._hover_timer.stop()
        # Keep normal polling/painting active. No input is driven by this probe.
        samples, starts, latest = [], {}, {}
        cold_peak = 0
        phase = {"start": None, "cold": time.monotonic()}
        owned = set()
        def collect():
            nonlocal report, cold_peak
            adapter = runtime.adapters[Provider.CODEX]
            assert isinstance(adapter, CodexAdapter)
            if adapter._process is not None and adapter._process.processId():
                owned.add(int(adapter._process.processId()))
            values = {}
            for identity in {os.getpid(), *owned}:
                value = meter.sample(identity)
                if value is not None:
                    values[identity] = value
                    latest[identity] = value
            if phase["start"] is None:
                cold_peak = max(cold_peak, sum(value[1] for value in values.values()))
                if time.monotonic() - phase["cold"] < 7:
                    return
                phase["start"] = time.monotonic()
                starts.update({identity: value[0] for identity, value in values.items()})
                if args.with_refresh:
                    runtime.refresh_now()
            elapsed = time.monotonic() - phase["start"]
            samples.append({"at": elapsed, "rss": sum(value[1] for value in values.values()), "private": sum(value[2] for value in values.values()), "processes": len(values)})
            if elapsed < args.seconds:
                return
            cpu = sum(value[0] - starts.get(identity, 0) for identity, value in latest.items()) / elapsed * 100
            widget_cpu = latest[os.getpid()][0] - starts[os.getpid()]
            child_cpu = sum(value[0] - starts.get(identity, 0) for identity, value in latest.items() if identity != os.getpid())
            peak = max(item["rss"] for item in samples) / 1024 ** 2
            report = {"seconds": round(elapsed, 2), "samples": len(samples), "cpuOneCorePercent": round(cpu, 3),
                      "cpuMachinePercent": round(cpu / (os.cpu_count() or 1), 3), "peakResidentMBIncludingOwnedChildren": round(peak, 2),
                      "peakPrivateMBIncludingOwnedChildren": round(max(item["private"] for item in samples) / 1024 ** 2, 2),
                      "ownedCodexProcessesObserved": len(owned), "cpuBelowOnePercent": cpu < 1, "residentBelow200MB": peak < 200,
                      "widgetCpuSeconds": round(widget_cpu, 5), "ownedCodexCpuSeconds": round(child_cpu, 5),
                      "startupPeakResidentMBIncludingOwnedChildren": round(cold_peak / 1024 ** 2, 2), "deliberateRefresh": args.with_refresh,
                      "platform": platform.platform(), "logicalProcessors": os.cpu_count(), "dpr": app.primaryScreen().devicePixelRatio(),
                      "codexStatus": runtime.states[Provider.CODEX].status.value,
                      "boundary": "Reference device, normal collapsed animation/polling. Includes cumulative CPU and concurrent resident memory of only app-owned Codex processes. Seven-second startup CPU excluded, startup memory separately reported. Deliberate refresh only when specified; default 200 seconds includes a normal 180-second polling cycle. Not a long-duration leak or clean-Windows test."}
            poll.stop()
            leaf.quit_app()
        poll = QTimer()
        poll.timeout.connect(collect)
        poll.start(50)
        app.exec()
    meter.close()
    assert report is not None
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))
    return 0 if report["cpuBelowOnePercent"] and report["residentBelow200MB"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

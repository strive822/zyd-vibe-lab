"""Exercise the actual isolated bundle, launcher and visible startup failure.

Uses temporary app data and only the official read-only quota operation.
No physical mouse/keyboard is driven and no user snippets or keys are copied.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from ctypes import wintypes
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def runtime_probe(bundle: Path, data: Path) -> dict:
    from zoneinfo import ZoneInfo

    import PySide6
    import run_app
    from PySide6.QtCore import QEventLoop, QLibraryInfo, QLocale, QTimer, QTranslator, QUrl, qVersion
    from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QSslSocket
    from PySide6.QtSvg import QSvgRenderer
    from PySide6.QtWidgets import QApplication

    from usage_app.desktop_geometry import Placement
    from usage_app.desktop_settings import DesktopSettings, DesktopSettingsStore
    from usage_app.runtime import UsageRuntime

    assert sys.flags.isolated and sys.flags.ignore_environment
    assert all(Path(path).resolve().is_relative_to(bundle) for path in sys.path)
    assert Path(PySide6.__file__).resolve().is_relative_to(bundle)
    assert Path(run_app.__file__).resolve().is_relative_to(bundle / "app")
    app = QApplication([])
    assert QSvgRenderer(str(bundle / "app" / "usage_app" / "assets" / "check.svg")).isValid()
    translator = QTranslator()
    assert translator.load(QLocale("zh_CN"), "qtbase", "_", QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath))
    assert ZoneInfo("Asia/Shanghai").key == "Asia/Shanghai"
    assert QSslSocket.supportsSsl() and QSslSocket.activeBackend() == "schannel"

    # A real HTTPS request with NO Authorization header; only classify the status.
    # Never retain or print the response body.
    manager = QNetworkAccessManager()
    request = QNetworkRequest(QUrl("https://api.deepseek.com/user/balance"))
    request.setTransferTimeout(10_000)
    request.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute,
                         QNetworkRequest.RedirectPolicy.ManualRedirectPolicy)
    reply = manager.get(request)
    ssl_errors = []
    reply.sslErrors.connect(lambda errors: ssl_errors.extend(errors))
    loop = QEventLoop()
    reply.finished.connect(loop.quit)
    QTimer.singleShot(11_000, loop.quit)
    loop.exec()
    status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
    assert reply.isFinished() and not ssl_errors and status == 401
    reply.deleteLater()

    runtime = UsageRuntime(data)
    runtime.stop()  # No source query from this setup; the real entry tests it below.
    DesktopSettingsStore(data).save(DesktopSettings(Placement(app.primaryScreen().name(), "left", .35, pinned=True), True))
    return {"isolated": True, "ignoreEnvironment": True, "qt": qVersion(), "python": sys.version.split()[0],
            "paths": [str(Path(path).resolve().relative_to(bundle)) for path in sys.path],
            "svg": True, "chineseTranslation": True, "timezone": True,
            "tlsBackend": QSslSocket.activeBackend(), "unauthorizedHttpsStatus": status}


def startup_probe(bundle: Path, data: Path, capture: Path) -> dict:
    import run_app
    from PySide6.QtCore import QTimer

    before = (data / "config.json").read_bytes()
    original = run_app.startup_error
    observed = []

    def show(error, directory):
        message = original(error, directory)
        assert message.windowTitle() == "usage · 无法启动"
        assert "保留" in message.informativeText()
        assert "退出" in [button.text() for button in message.buttons()]
        def inspect():
            assert message.isVisible()
            assert message.grab().save(str(capture))
            observed.append(message.text())
            message.reject()  # Programmatic closure of our own test dialog.
        QTimer.singleShot(180, inspect)
        return message

    run_app.startup_error = show
    sys.argv = [str(bundle / "app" / "run_app.py"), "--data-dir", str(data)]
    assert run_app.main() == 1
    assert (data / "config.json").read_bytes() == before and len(observed) == 1
    return {"visibleChineseFailure": True, "configurationPreserved": True}


class ProcessEntry(ctypes.Structure):
    _fields_ = [("size", wintypes.DWORD), ("usage", wintypes.DWORD), ("pid", wintypes.DWORD),
                ("heap", ctypes.c_size_t), ("module", wintypes.DWORD), ("threads", wintypes.DWORD),
                ("parent", wintypes.DWORD), ("priority", wintypes.LONG), ("flags", wintypes.DWORD),
                ("exe", wintypes.WCHAR * 260)]


def owned_launcher_child(parent: int, executable: Path):
    """Track only the child with our launcher PID AND exact bundle image path."""
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
    kernel.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
    snapshot = kernel.CreateToolhelp32Snapshot(2, 0)
    assert snapshot and snapshot != ctypes.c_void_p(-1).value
    try:
        entry = ProcessEntry()
        entry.size = ctypes.sizeof(entry)
        more = kernel.Process32FirstW(snapshot, ctypes.byref(entry))
        while more:
            if entry.parent == parent and entry.exe.casefold() == "pythonw.exe":
                handle = kernel.OpenProcess(0x00100000 | 0x1000 | 0x0001, False, entry.pid)
                buffer, size = ctypes.create_unicode_buffer(32768), wintypes.DWORD(32768)
                if handle and kernel.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
                    if Path(buffer.value).resolve() == executable.resolve():
                        return kernel, handle
                if handle:
                    kernel.CloseHandle(handle)
            more = kernel.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        kernel.CloseHandle(snapshot)
    raise AssertionError("Our launcher did not create the expected bundled process")


def wait_file(path: Path, seconds: float) -> None:
    until = time.monotonic() + seconds
    while time.monotonic() < until:
        if path.exists() and path.stat().st_size:
            return
        time.sleep(.08)
    raise AssertionError(f"Expected own test artifact missing: {path.name}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--mode", choices=("runtime", "startup"))
    parser.add_argument("--data", type=Path)
    parser.add_argument("--capture", type=Path)
    args = parser.parse_args()
    bundle = (args.bundle or Path(json.loads((ROOT / "evidence/m6/portable-build.json").read_text(encoding="utf-8"))["directory"])).resolve()
    if args.mode:
        result = runtime_probe(bundle, args.data) if args.mode == "runtime" else startup_probe(bundle, args.data, args.capture)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    assert os.name == "nt"
    out = ROOT / "evidence" / "m6"
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((bundle / "build-manifest.json").read_text(encoding="utf-8"))
    sums = json.loads((bundle / "SHA256SUMS.json").read_text(encoding="utf-8"))
    for name, digest in sums.items():
        assert hashlib.sha256((bundle / name).read_bytes()).hexdigest() == digest, name
    assert hashlib.sha256(json.dumps(manifest["buildInputs"], sort_keys=True).encode()).hexdigest() == manifest["candidateHash"]
    for name, digest in manifest["sources"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    assert not any(Path(name).name in ("config.json", "snapshots.json", "reminder-ledger.json") or "snippets" in Path(name).parts for name in sums)
    assert not any(Path(name).suffix in (".pyc", ".tmp") for name in sums)
    checks = ["all shipped checksums and current sources match; no app data, bodies or temporary bytecode shipped"]
    python = bundle / "runtime" / "python.exe"
    environment = dict(os.environ)
    environment["PATH"] = str(Path(os.environ["WINDIR"]) / "System32") + os.pathsep + os.environ["WINDIR"]
    with tempfile.TemporaryDirectory(prefix="usage 验收 package space ") as directory:
        root = Path(directory)
        environment["PYTHONHOME"] = str(root / "missing-python")
        environment["PYTHONPATH"] = str(root / "poison-python-path")
        entry_data = root / "normal"
        command = [str(python), "-B", "-X", "utf8", str(Path(__file__).resolve()), "--bundle", str(bundle)]
        result = subprocess.run([*command, "--mode", "runtime", "--data", str(entry_data)], env=environment,
                                capture_output=True, text=True, encoding="utf-8", timeout=20, check=True)
        isolated = json.loads(result.stdout)
        checks.append("embedded Python ignores foreign Python environment; Qt, SVG, Chinese, tzdata and native Schannel HTTPS work")

        screenshot = out / "portable-entry.png"
        screenshot.unlink(missing_ok=True)
        launch = subprocess.Popen([str(bundle / "usage.exe"), "--data-dir", str(entry_data), "--detail", "codex", "--capture", str(screenshot)],
                                  env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        assert launch.wait(timeout=5) == 0
        kernel, handle = owned_launcher_child(launch.pid, bundle / "runtime" / "pythonw.exe")
        try:
            wait_file(entry_data / "logs" / "events.jsonl", 5)
            second = subprocess.run([str(python), "-B", "-X", "utf8", str(bundle / "app/run_app.py"), "--data-dir", str(entry_data)],
                                    env=environment, capture_output=True, text=True, timeout=5)
            assert second.returncode == 0, "Second launch failed to receive restore acknowledgement"
            wait_file(screenshot, 16)
            assert kernel.WaitForSingleObject(handle, 5000) == 0
        finally:
            if kernel.WaitForSingleObject(handle, 0) != 0:
                kernel.TerminateProcess(handle, 255)  # Only the strictly identified owned test child.
                kernel.WaitForSingleObject(handle, 3000)
            kernel.CloseHandle(handle)
        events = [json.loads(line) for line in (entry_data / "logs/events.jsonl").read_text(encoding="utf-8").splitlines()]
        (out / f"portable-events-{manifest['candidateHash'][:12]}-{datetime.now(UTC):%Y%m%dT%H%M%S%f}.json").write_text(
            json.dumps({"candidateHash": manifest["candidateHash"], "events": [
                {key: value for key, value in item.items() if key in ("at", "event", "provider", "code", "errorType", "location", "line")}
                for item in events]}, indent=2), encoding="utf-8")
        assert sum(item["event"] == "start" for item in events) == 1
        assert any(item["event"] == "quit" for item in events)
        assert not any(item["event"] in ("storage_failed", "unexpected_error") for item in events)
        codex_read = any(item["event"] == "refresh_ok" and item.get("provider") == "codex" for item in events)
        assert codex_read, "Official read-only Codex quota was not successful in this bundle run"
        checks.append("actual windowed launcher handles Chinese/spaced paths, production Qt capture, official Codex read and second-instance restore")

        bad_data = root / "damaged"
        bad_data.mkdir()
        (bad_data / "config.json").write_bytes(b'{invalid json')
        result = subprocess.run([*command, "--mode", "startup", "--data", str(bad_data), "--capture", str(out / "portable-startup-error.png")],
                                env=environment, capture_output=True, text=True, encoding="utf-8", timeout=10, check=True)
        failure = json.loads(result.stdout)
        checks.append("real production startup shows a Chinese error and preserves invalid configuration; own dialog closed programmatically")
    report = {"passed": len(checks), "checks": checks, "candidateHash": manifest["candidateHash"],
              "runtime": isolated, "startupFailure": failure, "codexReadOnly": codex_read,
              "boundary": "Actual bundled binaries on this reference Windows, poisoned Python environment/minimal PATH, temporary app data. Not a clean Windows, physical mouse, real GLM/DeepSeek, multi-monitor or signed-release test."}
    (out / "portable-native-result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

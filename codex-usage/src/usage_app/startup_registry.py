"""Access the login-visible Run entry through the existing Explorer desktop.

MSIX descendants can read/write a private HKCU overlay. A new Shell.Application
or a normal subprocess inherits that environment; the desktop's Application
object runs in the existing Explorer process. No elevation or scheduler is used.
"""
from __future__ import annotations

import base64
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Literal

from .storage import StorageError


_WORKER = r"""
$ErrorActionPreference = 'Stop'
$result = @{ ok = $false; value = $null }
try {
    $request = Get-Content -LiteralPath REQUEST -Raw -Encoding UTF8 | ConvertFrom-Json
    if ([DateTimeOffset]::UtcNow.ToUnixTimeSeconds() -gt $request.deadline) { throw 'Expired' }
    $path = 'Software\Microsoft\Windows\CurrentVersion\Run'
    $name = 'Duizhaoye'
    if ($request.action -eq 'write') {
        if ($null -ne $request.value -and ($request.value -isnot [string] -or $request.value.Length -gt 260)) { throw 'Invalid command' }
        $key = [Microsoft.Win32.Registry]::CurrentUser.CreateSubKey($path)
        try {
            if ($null -eq $request.value) { $key.DeleteValue($name, $false) }
            else { $key.SetValue($name, $request.value, [Microsoft.Win32.RegistryValueKind]::String) }
        } finally { $key.Dispose() }
    } elseif ($request.action -ne 'read') { throw 'Invalid action' }
    $key = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey($path)
    try {
        if ($null -ne $key -and $key.GetValueNames() -contains $name) {
            if ($key.GetValueKind($name) -ne [Microsoft.Win32.RegistryValueKind]::String) { throw 'Invalid registry type' }
            $result.value = $key.GetValue($name)
        }
    } finally { if ($null -ne $key) { $key.Dispose() } }
    if ($request.action -eq 'write' -and $result.value -cne $request.value) { throw 'Readback mismatch' }
    $result.ok = $true
} catch { $result.ok = $false }
$response = RESPONSE
[IO.File]::WriteAllText($response + '.tmp', ($result | ConvertTo-Json -Compress), (New-Object Text.UTF8Encoding($false)))
[IO.File]::Move($response + '.tmp', $response)
"""

_BROKER = r"""
$ErrorActionPreference = 'Stop'
$shell = New-Object -ComObject Shell.Application
$hwnd = 0
$desktop = $shell.Windows().FindWindowSW(0, 0, 8, [ref]$hwnd, 1)
if ($null -eq $desktop) { throw 'Explorer desktop unavailable' }
$desktop.Document.Application.ShellExecute(POWERSHELL, ARGUMENTS, '', 'open', 0)
"""


def _quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _encoded(script: str) -> str:
    return base64.b64encode(script.encode("utf-16-le")).decode("ascii")


def registry_request(action: Literal["read", "write"], value: str | None = None) -> str | None:
    """Only the application's own Run value is addressable; never log commands."""
    powershell = Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    try:
        # USERPROFILE is outside AppData virtualization. Inherited profile ACLs
        # keep these short-lived messages in the current user's directory.
        with tempfile.TemporaryDirectory(prefix=".usage-startup-", dir=Path.home()) as temporary:
            root = Path(temporary)
            request, response = root / "request.json", root / "response.json"
            request.write_text(json.dumps({"action": action, "value": value, "deadline": int(time.time()) + 10}), encoding="utf-8")
            worker = _WORKER.replace("REQUEST", _quote(str(request))).replace("RESPONSE", _quote(str(response)))
            arguments = "-NoProfile -NonInteractive -WindowStyle Hidden -EncodedCommand " + _encoded(worker)
            broker = _BROKER.replace("POWERSHELL", _quote(str(powershell))).replace("ARGUMENTS", _quote(arguments))
            started = time.monotonic()
            completed = subprocess.run(
                [str(powershell), "-NoProfile", "-NonInteractive", "-EncodedCommand", _encoded(broker)],
                capture_output=True, timeout=10, creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if completed.returncode:
                raise StorageError("无法访问 Windows 登录启动项，请在桌面会话中重新保存")
            while not response.exists():
                if time.monotonic() - started > 10:
                    raise StorageError("Windows 登录启动项核验超时，请重新保存")
                time.sleep(0.02)
            result = json.loads(response.read_text(encoding="utf-8"))
            if not isinstance(result, dict) or result.get("ok") is not True:
                raise StorageError("Windows 登录启动项未能核验，请检查本用户的权限")
            actual = result.get("value")
            if actual is not None and not isinstance(actual, str):
                raise StorageError("开机启动项格式不兼容，原项已保留")
            return actual
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        raise StorageError("Windows 登录启动项未能核验，请重新保存") from error

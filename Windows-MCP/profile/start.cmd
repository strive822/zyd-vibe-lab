@echo off
setlocal
set "ANONYMIZED_TELEMETRY=false"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "WINDOWS_MCP_WATCHDOG=false"
"%~dp0source\.venv\Scripts\python.exe" -m windows_mcp serve --transport stdio
exit /b %errorlevel%

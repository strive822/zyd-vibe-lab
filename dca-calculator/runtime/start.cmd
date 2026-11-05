@echo off
setlocal
cd /d "%~dp0backend"
if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv
  if errorlevel 1 goto failed
)
if not exist ".venv\.runtime-ready" (
  .venv\Scripts\python.exe -m pip install -r requirements-runtime.txt
  if errorlevel 1 goto failed
  type nul > ".venv\.runtime-ready"
)
echo Open http://127.0.0.1:8000 after the server reports ready. Ctrl+C stops it.
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
exit /b %errorlevel%
:failed
echo Setup failed. Python 3.11 or newer and internet access are required.
pause
exit /b 1

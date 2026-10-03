@echo off
setlocal
rem Start backend (FastAPI) on port 8000
cd /d "%~dp0..\backend"
if errorlevel 1 exit /b 1
if not exist ".venv\Scripts\python.exe" (
  echo [First run] Creating venv and installing dependencies...
  python -m venv .venv
  if errorlevel 1 goto :failed
)
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto :failed
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
exit /b %errorlevel%

:failed
echo Backend setup failed. Check Python and network access, then retry.
pause
exit /b 1

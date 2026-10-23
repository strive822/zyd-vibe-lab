@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
  echo Please install the Python dependencies in .venv first.
  pause
  exit /b 1
)
start "" /D "%~dp0" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0app\enhanced.py" --settings

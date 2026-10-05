@echo off
setlocal
cd /d "%~dp0"
if exist "dist\usage-0.1.0-candidate-47eb35634991\usage.exe" (
  start "" "dist\usage-0.1.0-candidate-47eb35634991\usage.exe" %*
  exit /b 0
)
if exist ".venv-win\Scripts\pythonw.exe" (
  start "" ".venv-win\Scripts\pythonw.exe" -B "src\run_app.py" %*
  exit /b 0
)
echo Extract the portable package into dist, or create the development environment.
pause
exit /b 1

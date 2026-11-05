@echo off
cd /d "%~dp0"
python restore.py --destination "%~dp0app" --cache "%~dp0.downloads"
if errorlevel 1 (pause & exit /b 1)
echo Prepared app. Run app\install.cmd next. Host registration is a separate step.
pause

@echo off
cd /d "%~dp0"
python restore.py --destination "%~dp0app" --cache "%~dp0.downloads"
if errorlevel 1 (pause & exit /b 1)
echo Prepared verified npm package in app. Read INSTALL.md; setup is not automatic.
pause

@echo off
setlocal
cd /d "%~dp0"
where node >nul 2>nul
if errorlevel 1 (
  echo Node.js 22 or newer is required. See INSTALL.md.
  pause
  exit /b 1
)
node start.mjs
if errorlevel 1 pause

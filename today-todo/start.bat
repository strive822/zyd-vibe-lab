@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Today Todo - Local Server

where node >nul 2>nul
if errorlevel 1 (
  echo.
  echo Node.js not found. Please install Node.js 18 or newer first.
  echo https://nodejs.org/
  echo.
  pause
  exit /b 1
)

set OPEN_BROWSER=1
node server.js

echo.
echo Server stopped. Press any key to close this window.
pause >nul

@echo off
set "PATH=%~dp0runtime;%PATH%"
set "NEXT_TELEMETRY_DISABLED=1"
cd /d "%~dp0source"
"%~dp0runtime\node.exe" "node_modules\typescript\bin\tsc" --noEmit
if errorlevel 1 exit /b %errorlevel%
"%~dp0runtime\node.exe" "node_modules\eslint\bin\eslint.js" src
if errorlevel 1 exit /b %errorlevel%
"%~dp0runtime\node.exe" "node_modules\vitest\vitest.mjs" run
if errorlevel 1 exit /b %errorlevel%
"%~dp0runtime\node.exe" "node_modules\next\dist\bin\next" build
exit /b %errorlevel%

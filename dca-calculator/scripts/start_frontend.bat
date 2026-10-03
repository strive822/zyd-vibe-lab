@echo off
setlocal
rem Start frontend (Next.js) on port 3000
cd /d "%~dp0..\frontend"
if errorlevel 1 exit /b 1
echo Installing locked frontend dependencies...
call npm ci --no-fund --no-audit
if errorlevel 1 goto :failed
call npm run dev
exit /b %errorlevel%

:failed
echo Frontend setup failed. Check Node.js 22.6+ and network access, then retry.
pause
exit /b 1

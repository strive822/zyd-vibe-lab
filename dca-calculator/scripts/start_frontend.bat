@echo off
rem Start frontend (Next.js) on port 3000
cd /d "%~dp0..\frontend"
if not exist node_modules (
  echo [First run] Installing frontend dependencies...
  call npm install --registry=https://registry.npmmirror.com/
)
call npm run dev

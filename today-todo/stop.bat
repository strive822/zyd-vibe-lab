@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 停止今日待办

set KILLED=0
for /l %%R in (1,1,2) do (
  for %%P in (3000 3001 3002 3003 3004 3005) do (
    for /f "tokens=5" %%A in ('netstat -ano ^| findstr /r /c:":%%P .*LISTENING"') do (
      echo 正在停止端口 %%P 上的进程 %%A
      taskkill /PID %%A /F >nul 2>&1
      set KILLED=1
    )
  )
  if %%R==1 "%SystemRoot%\System32\ping.exe" -n 2 127.0.0.1 >nul
)

if "%KILLED%"=="1" (
  echo.
  echo 服务已停止，端口已释放。
) else (
  echo 没有发现正在运行的服务。
)

echo.
echo 按任意键关闭窗口。
pause >nul

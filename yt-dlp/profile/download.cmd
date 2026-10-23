@echo off
setlocal
"%~dp0yt-dlp.exe" --config-locations "%~dp0yt-dlp.conf" %*
exit /b %errorlevel%

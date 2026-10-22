@echo off
setlocal
set "UV_TOOL_DIR=%~dp0tools"
set "UV_TOOL_BIN_DIR=%~dp0bin"
set "UV_CACHE_DIR=%~dp0cache"
set "UV_PYTHON_INSTALL_DIR=%~dp0python"
uv tool install --managed-python --python 3.14.7 --no-config windows-mcp==0.8.7
exit /b %errorlevel%

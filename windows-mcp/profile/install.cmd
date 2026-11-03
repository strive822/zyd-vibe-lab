@echo off
setlocal
set "UV_CACHE_DIR=%~dp0cache"
set "UV_PYTHON_INSTALL_DIR=%~dp0python"
uv sync --project "%~dp0source" --frozen --no-dev --managed-python --python 3.14.7
exit /b %errorlevel%

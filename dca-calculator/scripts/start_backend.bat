@echo off
rem Start backend (FastAPI) on port 8000
cd /d "%~dp0..\backend"
if not exist .venv (
  echo [First run] Creating venv and installing dependencies...
  python -m venv .venv
  .venv\Scripts\python.exe -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
)
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 给 Agent：下载并运行计算器

用户提示词：

```text
下载并运行 https://github.com/strive822/zyd-vibe-lab 里的 dca-calculator。请读取这个项目的 INSTALL.md，自动准备环境、启动前后端并验证页面，保留已有文件。
```

## 获取与环境

克隆仓库，或安全解压 `https://github.com/strive822/zyd-vibe-lab/archive/refs/heads/main.zip`，完整保留其中 `dca-calculator/`。下载前先读 [README.md](README.md)，实际检查 Python 3.11+、Node.js 22.6+ 和 npm。Windows 是原始交付环境；Linux / macOS 可以运行 Python 与 Next.js 源码，Windows bat 和 exe 不能跨系统执行。

没有 Python 或 Node 时，Agent 使用宿主允许的官方安装方式准备；缺少安装权限则说明具体限制。不要把依赖装入系统 Python，也不要覆盖已有项目或占用的服务端口。

## 启动（Windows PowerShell，当前目录为项目根目录）

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
```

在两个长期运行的终端或宿主进程工具中分别执行，先检查端口 8000 / 3000 是否可用：

```powershell
# 后端终端，在项目根目录执行
backend/.venv/Scripts/python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

```powershell
# 前端终端
Set-Location frontend
npm ci
npm run dev -- --hostname 127.0.0.1
```

Windows 也可使用 `scripts/start_backend.bat`、`scripts/start_frontend.bat`。如果端口被占用，先识别是否已有本项目服务；复用正确的已有服务，或报告冲突，不杀掉未知进程。

## 启动（WSL / Linux / macOS，当前目录为项目根目录）

```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
backend/.venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

另开一个终端：

```bash
cd frontend
npm ci
npm run dev -- --hostname 127.0.0.1
```

## 验证与使用

1. 请求 `http://127.0.0.1:8000/api/health`，预期 `{"status":"ok"}`。
2. 打开 `http://127.0.0.1:3000`，确认页面加载并显示两个模型或明确的数据源错误。
3. 请求一次 `/api/calculation`。真实行情成功时才核验三资产和两个模型权重和为 1；免费数据源不可达时报告 502 和具体原因，不代填行情。
4. 输入 1000 元，确认每个模型三项金额合计 1000.00；修改金额不应再请求行情。仅接受正数及最多两位小数。

此项目没有账号或 API Key，读取公开行情，不执行交易。安装无需重新打包 exe；可选打包先按 README 完成静态导出。测试需要 `backend/requirements-dev.txt`，前端检查使用 `npm run typecheck`、`npm test`、`npm run build`。

# -*- coding: utf-8 -*-
"""PyInstaller 单文件打包入口。

启动 FastAPI 应用（uvicorn），由 app.main 同源 serve 前端静态资源与 /api。
直接 import app.main 以便 PyInstaller 静态收集整个 app 包（含 models/services/data）。
"""
from app.main import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

# -*- coding: utf-8 -*-
"""FastAPI 入口。

运行（Windows，backend 目录下）：
    python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

接口：
    GET /api/health        健康检查
    GET /api/calculation   一次性完成 取行情→SMA800→两模型→权重
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import sys
from pathlib import Path

from app.data.market_data import MarketDataError
from app.schemas.calculation import CalculationResponse
from app.services.calculator import run_calculation

app = FastAPI(
    title="三资产定投权重计算器",
    version="1.0.0",
    description="纯计算工具：SMA800 + C哥模型/严谨模型 双模型权重（无交易功能）",
)

# 仅允许本机前端跨域访问（前后端同源代理时不会触发）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/calculation", response_model=CalculationResponse)
def get_calculation() -> CalculationResponse:
    """打开/刷新页面时调用一次。任何资产数据不可靠时明确报错，绝不返回错误权重。"""
    try:
        return run_calculation()
    except MarketDataError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:  # noqa: BLE001 兜底：未知异常同样不输出权重
        raise HTTPException(
            status_code=500,
            detail=f"当前无法完成计算：服务内部错误（{type(exc).__name__}）。",
        )


# ---------------------------------------------------------------------------
# 前端静态资源托管（方案 A：单 exe 一体运行，免 Node 运行时）
# 开发态：../frontend/out；PyInstaller 打包态：sys._MEIPASS/out
# 必须在 /api 路由之后挂载，/api/* 精确路由优先命中，不会落到此处。
# ---------------------------------------------------------------------------
_APP_DIR = Path(__file__).resolve().parent            # backend/app
_PROJECT_ROOT = _APP_DIR.parent.parent               # Project_DCA_Calculator
_DEV_OUT = _PROJECT_ROOT / "frontend" / "out"
_PKG_OUT = Path(getattr(sys, "_MEIPASS", "")) / "out"
_FRONTEND_OUT = _PKG_OUT if _PKG_OUT.exists() else _DEV_OUT

if _FRONTEND_OUT.exists():
    app.mount("/", StaticFiles(directory=str(_FRONTEND_OUT), html=True), name="frontend")

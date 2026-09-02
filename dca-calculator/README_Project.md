# README_Project — 项目管理说明

## 项目目标

为个人定投决策提供纯计算工具：基于 SMA800 估值比率，用两套独立模型（C哥模型/严谨模型）
输出纳斯达克100、中证500、黄金三个资产大类的定投权重与金额分配。**不做交易、不做回测。**

## 技术栈

- 后端：Python 3.13 + FastAPI + Pydantic + requests（无数据库）
- 前端：Next.js 15（App Router）+ React 19 + TypeScript + Tailwind CSS v4
- 数据：东方财富（主）+ 新浪财经/腾讯（按资产回退），全部免费无密钥
- 测试：pytest（45 个用例）

## 当前状态

v1.0.0 已交付：数据源验证 → 后端（数据层/两模型/测试/API）→ 前端 → 端到端实测全部通过。

## 文件结构

```
backend/app/         后端源码（data/models/services/schemas/tests）
backend/tools/       数据源验证脚本
frontend/app/        前端页面（page.tsx 主界面，lib/money.ts 金额分摊）
docs/                数据源验证报告
tests/screenshots/   端到端验收截图
logs/                运行日志（backend_uvicorn.log 等）
scripts/             Windows 一键启动脚本
```

## 使用入口

- 启动：`scripts\start_backend.bat` + `scripts\start_frontend.bat`，浏览器开 http://localhost:3000
- 详细说明：见 `README.md`

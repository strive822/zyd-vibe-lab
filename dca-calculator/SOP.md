# SOP — 项目操作流程

## 日常启动

1. 双击 `scripts\start_backend.bat`（等待控制台出现 `Uvicorn running on http://127.0.0.1:8000`）
2. 双击 `scripts\start_frontend.bat`（等待 `Ready`）
3. 浏览器打开 http://localhost:3000

## 日常使用

- 输入本次定投总金额 → 两模型卡片实时显示各资产权重与金额
- 刷新页面 = 重新获取行情并计算（60 秒内重复刷新会复用上一次真实数据）
- 出现"当前无法完成计算…"时点重试；持续失败说明免费数据源整体不可用，稍后再试

## 数据源复验

```
backend\.venv\Scripts\python.exe backend\tools\verify_data_sources.py
```

全部 PASS 说明数据源健康；FAIL 时对照 `docs/数据源验证报告.md` 排查。

## 运行测试

```
cd backend
.venv\Scripts\python.exe -m pytest
```

## 修改注意事项

- 模型公式/γ/口径改动必须同步更新单元测试（严格单调性是红线）
- `config.py` 改 secid/端点前先用验证脚本实测
- 前端 `lib/money.ts` 与后端口径（权重和=1）相关，改动需两端核对
- 提交前确认 `.gitignore` 生效：venv/node_modules/.next/日志不入库

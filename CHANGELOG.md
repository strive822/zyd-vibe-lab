# CHANGELOG

## v1.0.0（2026-09-02）

首个可用版本。

### 新增
- 后端：FastAPI（/api/calculation、/api/health），数据层（东财主源 + 新浪/腾讯按资产回退、
  60 秒真实数据缓存、整流重试）、C哥模型与严谨模型纯函数、45 个单元测试。
- 前端：Next.js 15 + Tailwind v4 桌面端页面，双模型左右并排大数字卡片、总金额输入
  （最大余额法分摊、合计严格等于输入）、三资产行情时间行、Loading/错误态。
- 工具：`backend/tools/verify_data_sources.py` 数据源验证脚本。
- 文档：README、数据源验证报告、8 项工作区标准管理文件。
- scripts：Windows 一键启动脚本（backend/frontend）。

### 补充（2026-09-02 18:20）

- 新增 `docs/验收报告.md`：对照需求 §19 十四项逐条留证（含两轮实测数据、金额分摊两例、截图清单）
- 新增桌面启动器：`Start-DCA-Backend.bat` / `Start-DCA-Frontend.bat`（COM 创建 .lnk 被安全策略拦截，
  改用含绝对路径的 .bat 包装器，双击即用）
- 复验：晚间时段（18:17）pytest 45/45 通过；非整数金额 1234.56 分摊合计严格等于输入

### 验证
- pytest 45/45 通过；端到端真实行情实测（权重和=1.0、金额合计=输入、
  改金额零网络请求、数据时间展示正确）；截图存 `tests/screenshots/`。

### 补充（2026-09-02 20:35）单文件 exe 打包

- 新增 `backend/build_exe.spec` + `backend/build_exe_entry.py`：PyInstaller 单文件打包，
  产出 `backend/dist/DCA-Calculator.exe`（约 16MB），双击即启前后端一体，免装 Python/Node。
- 前端 `next.config.ts` 用 `DCA_EXPORT` 环境变量区分：导出态去 rewrites + `output:'export'`；
  开发态保留 rewrites，原有双 .bat + localhost:3000 方式不变。
- 后端 `app/main.py` 增加 `StaticFiles` 同源 serve `frontend/out`（开发态 / 打包态双路径）。
- 实测：exe 启动后 `GET /` 返回静态首页、`GET /api/calculation` 真实计算，两模型权重和均 = 1.0。
- `.gitignore` 补充忽略 `backend/build/`、`backend/dist/`、`frontend/out/`（可重现产物不入库）。

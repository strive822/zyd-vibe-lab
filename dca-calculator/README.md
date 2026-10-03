# 三资产定投权重计算器

> Windows 本地运行的纯计算工具：纳斯达克100 + 中证500 + 黄金，基于 SMA800 的双模型定投权重计算。
> **不是交易系统**——无回测、无持仓、无账户、无自动交易、无定时任务。

让 Agent 自动下载和启动，先读 [INSTALL.md](INSTALL.md)。源码运行需要 Python 3.11+ 和 Node.js 22.6+；日常运行不需要 API Key。

## 功能

打开网站后自动完成：

1. 获取三个资产最新可用行情与最近 800 个完整交易日收盘价；
2. 计算各自 SMA800（恰好 800 根已完成交易日的收盘均价）；
3. 计算估值比率 `R = 当前点位 ÷ SMA800`；
4. 分别运行两套完全独立的模型（C哥模型 / 严谨模型）输出权重；
5. 输入本次定投总金额后，实时显示每个模型的应投入金额（2 位小数，合计严格等于输入金额）。

页面为桌面端左右并排布局，显示三资产实际参与计算的行情时间。修改金额不会重新请求行情。

## 快速启动（Windows）

### 1. 启动后端（FastAPI，端口 8000）

方式 A —— 双击 `scripts\start_backend.bat`（首次自动建 venv 装依赖）。

方式 B —— 手动：

```bat
cd backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 2. 启动前端（Next.js，端口 3000）

方式 A —— 双击 `scripts\start_frontend.bat`（按锁文件安装依赖，失败则停止）。

方式 B —— 手动：

```bat
cd frontend
npm ci
npm run dev
```

### 3. 打开浏览器

访问 `http://localhost:3000`。刷新页面即重新获取行情并计算。

运行要求：Python 3.11+（含 pip）+ Node.js 22.6+（含 npm）。Windows 可用 bat 入口；WSL / Linux / macOS 的源码命令见 INSTALL.md。

## 数据源（免费、无需任何 API Key）

| 资产 | 基准 | 主源（东方财富） | 回退源 |
|------|------|------------------|--------|
| 纳斯达克100 | NDX 指数 | secid `100.NDX100` | 新浪财经 `.NDX`（US_MinKService） |
| 中证500 | 000905 指数 | secid `1.000905` | 腾讯 `sh000905`（ifzq.gtimg.cn） |
| 黄金 | XAU/USD 现货伦敦金 | secid `122.XAU` | 新浪财经 `hf_XAU` |

说明：

- 所有源均免费、无需密钥，因此**没有 .env / .env.example**。
- 2026-09-02 开发时已实测验证（脚本 `backend/tools/verify_data_sources.py` 可复验）：当时历史深度分别为 1861 根（NDX，2019 起）、2000+ 根（000905）、8918 根（XAU，1992 起）；这些是历史结果，当前接口可用性需重新查询。
- 选择单源东财 + 每资产一个回退源的原因：开发当天实测东财 WAF 存在秒级瞬断与指纹拦截，单源不可靠；回退链在实测中真实接管过全部三个资产。
- 为防免费源频控，同一资产 60 秒内的重复请求复用上一次**真实抓取**的数据（不做任何修改），60 秒后自动重新抓取。

## 两套模型的数学公式

记 `R_i = CurrentPrice_i / SMA800_i`（i ∈ {NDX, 中证500, 黄金}）。

**C哥模型**（无参数）：

```
Score_i  = 1 / R_i
Weight_i = Score_i / Σ Score
```

**严谨模型**（γ = 1.5 固定，不提供设置）：

```
V_i      = -ln(R_i)
Score_i  = exp( sign(V_i) × |V_i|^1.5 )
Weight_i = Score_i / Σ Score
```

两者共同性质（单元测试已验证）：

- `R_A < R_B ⇒ Weight_A > Weight_B`（严格单调，哪怕 R 差 0.001）；
- 三个 R 相同 ⇒ 各 33.33%；
- 权重之和恒为 1，全部 R > 1 时资金仍 100% 分配。

上述是数学公式的性质；计算机使用有限精度浮点数。极端比率下很小的权重可能饱和为 0，此时不能保证显示值或机器数仍严格区分所有资产。

**金额**：`Amount_i = 总金额 × Weight_i`，按“最大余额法”分摊到分，
三项显示金额之和**严格等于**输入总金额。
输入金额最多两位小数，并限制在整数分可精确表示的范围内；超出范围不计算。

## SMA800 数据口径

- 每个资产独立取最近 800 个**已完成**交易日收盘价，不要求三个市场日期对齐；
- 当日未收盘时：盘中最新价只作为 CurrentPrice，当日K线**不进入** SMA800
  （纳指 16:00 ET 前不算完、中证500 15:00 CST 前不算完、现货黄金当日K线一律不计入）；
- 已收盘后当日K线计入 SMA800 并作为 CurrentPrice；
- 现货黄金无交易所收盘概念，其口径为“截至上一自然日（北京时间）的日线”，当日形成中的K线不参与。

## 测试与验证

```bat
cd backend
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest
```

57 个后端单元测试通过（2026-10-03），覆盖：需求文档 §8 的 4 个指定用例 + 2000 组随机 R 的严格单调性 +
SMA800 口径（恰好 800 根、盘中价排除）+ 金额分摊尾差 + API 错误语义（数据失败返回
502 与中文报错，响应中不含任何权重字段）。
新增畸形 JSON 的数据源回退与浮点极端输入回归。数学公式保持不变；计算时先缩放分数，避免溢出或除零。

前端在 `frontend` 目录执行：

```text
npm ci
npm run typecheck
npm test
npm run build
```

前端 8 项回归验证错误原因保留、响应结构校验、金额输入边界与分摊总额；没有单独配置 ESLint。依赖安全检查使用 `npm audit --registry=https://registry.npmjs.org`，部分镜像不提供安全审计接口。

端到端实测（2026-09-02）：真实行情下权重和精确 = 1.0；输入 1000 元两模型金额合计均为
1000.00；修改金额时后端访问日志零新增请求；截图见 `tests/screenshots/`。

## 项目结构

```
backend/
  app/
    main.py               # FastAPI 入口（/api/calculation, /api/health）
    config.py             # 资产/数据源/口径配置
    data/market_data.py   # 行情获取、清洗、多源回退、完整交易日判定
    models/c_model.py     # C哥模型（纯函数）
    models/rigorous_model.py  # 严谨模型（纯函数，γ=1.5）
    services/calculator.py    # 编排：行情→SMA800→R→两模型→权重
    schemas/calculation.py    # Pydantic 响应模型
    tests/                # 后端单元测试
  requirements.txt        # 运行依赖
  requirements-dev.txt    # 测试依赖
  tools/verify_data_sources.py  # 数据源验证脚本（可随时复验）
frontend/
  app/page.tsx            # 桌面端页面（双模型并排大数字卡片）
  lib/money.ts            # 金额分摊（最大余额法）与格式化
  lib/calculation.ts      # API 成功/失败响应与数据结构校验
  tests/                  # 前端逻辑回归
docs/数据源验证报告.md
scripts/start_backend.bat / start_frontend.bat
```

## 已知限制

- 东财/腾讯/新浪均为免费非官方接口，极端情况下可能整体不可用；此时页面明确显示
  “当前无法完成计算：XXX…”并附重试按钮，**不会输出错误权重**。
- 美股早收盘日（13:00 ET 收盘）当日K线在 16:00 ET 前暂不计入 SMA800，影响极小。
- 仅支持桌面端浏览器，未做移动端适配（需求明确排除）。

## 安全说明

数据源全部免个人密钥；东财的 UT_TOKEN 为网页端公共标识。`.gitignore` 排除虚拟环境、node_modules 与日志，提交前仍应检查凭据和私人文件；静态扫描不能保证不存在所有敏感内容。

## 打包为单文件 exe（可选）

已提供 `backend/build_exe.spec`（PyInstaller 单文件规格），可把前后端打成一个
`DCA-Calculator.exe`，双击即启、免装 Python/Node：

```bat
cd backend
.venv\Scripts\python.exe -m pip install pyinstaller
.venv\Scripts\python.exe -m PyInstaller build_exe.spec --clean --noconfirm
```

打包前必须先生成前端静态文件。Windows PowerShell，在项目根目录执行：

```powershell
Set-Location frontend
npm ci
$env:DCA_EXPORT = "1"
try { npm run build } finally { Remove-Item Env:DCA_EXPORT -ErrorAction SilentlyContinue }
Set-Location ../backend
.venv/Scripts/python.exe -m pip install pyinstaller
.venv/Scripts/python.exe -m PyInstaller build_exe.spec --clean --noconfirm
```

产物：`backend/dist/DCA-Calculator.exe`。仓库不包含预编译计算器 exe；本轮验证了静态导出与同源托管，Windows exe 重新构建仍需 Windows 环境验证。

实现要点（方案 A · 单 exe）：

- 前端 `next build` 静态导出：`DCA_EXPORT=1` 时 `output: 'export'`（移除 rewrites）；
  非导出态保留 rewrites，原有「双 .bat + localhost:3000」方式不受影响。
- 后端 `app/main.py` 用 `StaticFiles` 同源 serve `frontend/out/` 与 `/api`，
  开发态从 `../frontend/out`、打包态从 `sys._MEIPASS/out` 加载。
- `build_exe.spec` 用 `collect_all` 收集 uvicorn / certifi / requests 的隐式导入与 CA 证书，
  并把 `frontend/out` 作为 datas 打进 exe。

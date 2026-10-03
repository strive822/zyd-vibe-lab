# Repository Cleanup Report

2026-10-03。基线提交 `9898618`，初始工作区干净。本轮针对 GitHub 仓库进行文件检查、最小修复、安装入口整理与提交前验证。

## Scope

初始 242 个 Git 跟踪文件逐个执行类型、语法/结构、文档链接、敏感内容模式、重复内容及包完整性检查；新增文件一起复核，最终清单见 [FILE_AUDIT.md](FILE_AUDIT.md)。重点复核入口、安装、配置/凭据、数据回退、计算、API 和打包链路。

这份清单说明静态检查覆盖，不能证明每行代码或每种业务输入没有缺陷。公开源码与本机运行包、私有验收资料分别处理。私有账号、用户配置和个人正文不在本轮公开报告中。

## Deleted

仅清除本轮运行产生的 Python 字节码和 pytest/mypy/ruff 缓存；它们可重新生成，不属于正式工程文件。本轮清除 72 个文件、12 个缓存目录，合计 20,499,883 字节（约 19.55 MiB）。

没有删除正式源码、现用便携目录、下载 ZIP、许可证、测试、历史验收或冻结视觉夹具。原有空 __init__.py 用于包结构，不能按重复空文件删除。

## Archived

没有新增归档目录。继续保留当前 docs/history、设计参考、合成截图和有独立用途的冻结源码。本机私有证据维持忽略规则，保留在原目录。

两份字节相同的论文 Codex / Claude Code ZIP 是不同客户端的明确下载入口；相同内容具有分发用途，保留。额度浮窗的解压运行目录与下载 ZIP 有不同用途，保留。

## Merged

dca-calculator/README_Project.md 中重复的项目状态、目录和技术栈统一到 README.md；原文件保留为跳转说明，旧链接继续有效。PROJECT_KNOWLEDGE、DEVLOG、DECISIONS、GOTCHAS、SOP 各自保留有价值的信息。

## Git Ignore

根目录 .gitattributes 固定额度源码的 LF，并禁止技能原稿/上游文件的换行转换，以保留 ZIP 与源码的字节一致性。根目录增加通用 `.venv/`、`.venv-*/`、`node_modules/`、`coverage/` 和 `core` 忽略项。原有 .env、日志和各项目私有资料规则继续生效。

## Structure Changes

- 新增根目录 AGENTS.md、scripts/check_repository.py 和持续检查配置。
- 根 INSTALL.md 按三个项目分流；计算器、额度浮窗新增独立 INSTALL.md，论文沿用其现有安装入口。
- 后端 requirements-dev.txt 承担测试依赖，requirements.txt 仅保留运行依赖。
- 前端增加 API 响应解析模块与两份行为回归测试。
- 本轮未迁移现有项目目录、生产数据或包内路径。

## Documentation Updates

README 首页提供三段可直接复制给 Agent 的提示词、项目入口和下载链接。安装说明明确完整文件、平台差异、依赖准备、现有目录保护与真实验证标准。

计算器补齐静态导出后才能打包 exe 的步骤，改用 npm ci 和锁文件；运行/测试说明同步，历史行情报告标明日期。论文发布说明去掉本机绝对路径；额度开发文档补上 tools 的 Lint。

## Fixes

| 问题 | 修复与证据 |
| --- | --- |
| 根安装入口把所有项目指向论文技能 | 按点名项目分流，保留“安装论文工作流”的既有用法 |
| 计算器丢失 502 中文原因 | 同时解析成功/失败 JSON；HTML 错误保留状态码，页面失败不展示权重 |
| 前端直接信任缺少/异常的权重和资产信息 | 校验三资产、有限非负权重与归一化结果；不补 0 制造有效结果 |
| 分以下金额、科学记数法及超出精确范围的输入 | 拒绝非法金额，整数分转换保留精度余量；分摊前归一化微小误差 |
| 上游畸形 JSON/字段中断整条回退链 | 按源捕获解析错误继续回退；所有源失败保留中文数据错误与实际尝试的源 |
| 极端正数令倒数或指数溢出/除零 | 以相同因子缩放分数，公式不变；极端饱和仍有浮点精度限制 |
| bat 只判断目录存在，失败后仍运行 | 检查真实 Python 入口，按声明/锁文件准备依赖，失败停止 |
| WSL 测试误把 powershell.exe 当原生 Windows 环境 | 论文原生安装测试只在 Windows Python 中运行；Linux 正确标记跳过 |
| 额度 Windows 模拟测试隐式依赖本机路径/环境 | 路径用临时目录；明确注入被模拟的 Windows 进程上下文；mypy 指定 win32 目标 |
| Windows 真实 CI 暴露中文 stdout 编码与上游文件换行哈希问题 | CLI 明确 UTF-8 输出并增加 cp1252 回归；Git 保留技能源原始字节，重建论文分发包 |
| npm 安全审计发现 3 个受影响依赖节点 | 更新 PostCSS / sharp overrides 与锁文件，保留 Next.js 15；官方 npm 审计重测为 0 |

依赖依据：[PostCSS 上游公告](https://github.com/postcss/postcss/security/advisories/GHSA-fxqj-rqcc-2cmp)、[sharp 上游公告](https://github.com/lovell/sharp/security/advisories/GHSA-rgj7-g3m4-5g8c)。本轮安装结果为 PostCSS 8.5.28、sharp 0.35.5；构建与原生图片缩放检查通过。镜像的安全审计接口曾返回 404，改用官方接口，不把失败当作零漏洞。

## Validation

本轮本地环境为 WSL / Ubuntu、Python 3.12.14、Node.js 22.22.1。依赖安装与构建在临时隔离目录进行，不依赖本机旧虚拟环境。

| 检查 | 结果 |
| --- | --- |
| Environment / Install | 额度 requirements-dev.txt、计算器运行/测试依赖均可安装，pip check 通过；前端 npm ci 通过 |
| Type Check | 额度 mypy 41 个源码文件通过（Windows 目标）；前端 tsc --noEmit 通过 |
| Lint | 额度 src/tests/tools Ruff 通过；新仓库检查器与计算器后端基础 Ruff 检查通过；前端未单独配置 ESLint |
| Tests | 额度 122 通过；计算器后端 57 通过；前端 8 通过；论文 27 通过、6 项 Windows 安装测试在 WSL 跳过；Windows 云端结果见下文 |
| Build | Next.js 普通生产构建和 DCA_EXPORT=1 静态导出通过；本轮没有重新构建 Windows exe |
| Runtime | 真实 Uvicorn 进程健康检查、FastAPI 同源托管静态页面通过；Qt 离屏应用创建和渲染通过 |
| Critical Path | Chromium 页面加载；1000/1234.56 元各模型分摊总额正确；改金额无额外行情请求；分以下输入拒绝；中文 502 保留且无权重；重试恢复，均通过 |
| Workflow | 中文空格路径初始化成功；空论文项目的 audit 正确拒绝交付；上游 Humanizer 内容哈希保持 |
| Download Packages | 四个 ZIP CRC/路径检查通过；ZIP SHA-256 符合公开校验值；额度 771 个随包文件校验与当前源码一致；三份论文 ZIP 与技能源逐字节一致 |
| Visual Baseline | 当前/冻结核心在同一 Linux 离屏环境 300×260 逐像素一致；这是渲染回归，不是 Windows 150% 物理设备验收 |
| Images | 10 个跟踪图片/GIF 解码检查与可见内容审查，无新增私有账号资料 |
| Repository | 当前可见文件检查、Markdown 本地链接、Python/JSON/TOML/SVG 结构和 git diff --check 通过 |

计算器浏览器链路使用明确的合成行情夹具，没有查询真实市场。额度测试模拟 Windows API 或使用离屏 Qt，不修改日常实例、账号、剪贴板或自启动。WSL 缺少的 Chromium 共享库仅解包到测试临时目录，没有安装系统组件。

代码与可达历史中的敏感模式检查未发现实际凭据。432 个历史文本 blob 中的 5 个候选，经核对为 2 处合成测试字符串和 3 处官方令牌端点常量；未回显值。东财 UT_TOKEN 是公开网页标识。此结果不是完整安全审计，不能保证所有种类的个人数据都能由模式检测发现。

后端当前依赖产生 1 条 TestClient/httpx 弃用警告，测试仍通过；后续升级测试客户端时应按框架官方行为复验。

## Manual Review

- codex-usage 原创源码尚未单独声明许可证。选择 MIT 等源码许可需要所有者决定；本轮没有替所有者授权。第三方许可证已保留。
- 真实行情、三端原生技能发现、完整论文交付、干净 Windows、重启登录、多屏/休眠及计算器 Windows exe 未在本轮重测。
- 本机 docs/evidence 中的私有/历史资料继续保留，未提出未经判断的删除项。若要单独清理这些资料，应先逐项确认用途和保留需求。

## Submission

用户已要求提交。本轮仅提交本仓库实际改动；提交前查看暂存差异与工作区状态，不修改远程地址、不重写已有 Git 历史、不创建 GitHub Release。新增 GitHub Actions 会在推送后检查三个项目，云端实际执行状态以 Actions 页面为准。

首次云端运行六个检查通过，论文 Windows 检查发现两处真实问题，已修复后再提交；不能用首次本地成功代替跨平台验证。

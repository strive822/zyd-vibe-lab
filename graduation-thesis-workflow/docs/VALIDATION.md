# 0.4.0 验证记录（2026-11-03）

35 项 unittest 中 29 项流程测试全部通过；6 项 PowerShell 安装/环境测试在本机被执行策略阻止（UnauthorizedAccess，且安全模块无法加载，连 Get-ExecutionPolicy 都不可用）。测试文件与 bootstrap-windows.ps1 本次未改动，失败类型与 2026-10-24 GOTCHAS 记录一致，属环境限制，不计为通过。

- 流程测试覆盖：tool=humanizer-zh 新项目写入与 audit 接受、旧值 humanizer 兼容（改值后重新快照后通过）、未知 tool 拒绝、vendor/humanizer-zh 的 UPSTREAM.json 哈希与全部四个平台包内字节一致、四包自包含与 WorkBuddy 元数据、既有证据/快照/路径回归全部保持。
- 补偿验证（进程级 -ExecutionPolicy Bypass，未改机器策略）：install.ps1 -Plan 四客户端目标正确（codex ~/.agents/skills、claude-code ~/.claude/skills、pi ~/.pi/agent/skills、workbuddy 显式 SkillsDir）；临时目录实际安装 pi 返回 files_installed，重复安装返回 already_installed，篡改 SKILL.md 后安装被拒并保留原文件；workbuddy 安装注入 version: 0.4.0。
- packages 重建为四个 ZIP：codex/claude-code/pi 三者字节相同，workbuddy 差异仅为元数据；全部四个包内 vendor SKILL.md/LICENSE 与上游 op7418/Humanizer-zh 提交 f4518a8 的 git blob（非 CRLF 工作区文件）逐字节一致。
- delivery 重建：45 个文件（新增 pi ZIP），ZIP 内文件清单与 FILES.json 一致，SHA256SUMS 匹配。
- 上游拉取自 GitHub 固定提交 f4518a8，与本地 ~/.agents/skills/Humanizer-zh 副本逐字节对照一致。

尚未验证：Pi 真实宿主注册 settings 后的原生发现、四端实际宿主中的真实论文端到端交付；这些边界与 0.3.0 记录相同，没有伪造宿主行为或检测分数。

---

# 0.3.0 验证记录（2026-09-10）

32 项 unittest 全部通过，0 项跳过；skill-creator quick_validate 使用 Python UTF-8 模式通过。

- 三端 ZIP 与实际安装文件逐文件相同，包括 WorkBuddy 元数据；中文空格路径下初始化成功，空项目 audit 正确拒绝交付。
- 验证重复安装、保护已有技能、环境创建与复用，以及禁止下载时诚实失败。
- 验证稿件修改并刷新 artifact 哈希后仍不能复用旧审查；验证缺快照、路径越界、证据变化及摘要不能支持全文细节。
- 验证润色 token 比较能提示数字、引用和部分公式变化，同时用否定句反例确认它不能代替语义审查。
- Humanizer 原版及许可哈希保持一致。

测试发现并修复 Windows CRLF 导致 WorkBuddy ZIP 漏加元数据的问题；增加了安装与 ZIP 字节一致性检查防止复发。沙箱账户执行策略阻止 PowerShell 测试后，在正常用户权限下重跑通过，没有修改机器执行策略。

尚未在三个实际宿主中分别完成真实论文端到端验收，也没有验证干净机器从零下载所有依赖。没有伪造论文或检测报告；下列为历史记录，不代表本次重测所有联网功能。

---

# 验证记录

## v0.2.0 · 2026-09-10

26 项 unittest 已全部通过，源 SKILL 格式验证通过。新增测试在正常 Windows 用户权限下将三个客户端技能安装到临时目录，核验重复安装与已有文件保护；实际创建并复用隔离 Python 环境；模拟未发现 Python 时检查安装计划和禁止下载的失败结果；验证 Humanizer 未执行时不能通过交付检查，并核对分发包中的上游内容哈希。

Python 3.13.15 AMD64 官方安装器地址已通过真实 HTTP HEAD 返回 200。未在无 Python 的干净机器实际执行安装器，也未执行文档库全量下载，因此不能将上述测试描述为零依赖整机端到端验证。三个客户端的原生技能发现与权限交互仍需实际客户端验证。

Humanizer 已从上游固定提交取得并阅读，许可证与文件哈希保留。测试不能证明 AI 检测或查重指标改善，没有生成或声称任何检测分数。

日期：2026-09-10。环境：Windows，Python 3.12.10。

## 已执行

- 初始 14 项离线 unittest 通过，覆盖空项目拒绝、无覆盖初始化、结构完整样例、证据变化、阅读范围不足、引用缺失、路径越界、缺交付物、阻塞、未独立核实材料的披露、坏 JSON、重复 id、URL 编码和三种包结构。
- 真实执行 Crossref 查询 `retrieval augmented generation`，limit=2，成功取得 2 条候选元数据，保存实际响应及 SHA256，输出明确 fulltext_verified=false。这只验证元数据接口，不证明候选适合引用或已读全文。
- skill-creator `quick_validate.py` 使用 `python -X utf8` 通过。默认 Windows GBK 运行曾解码失败，未改上游验证器，改用明确 UTF-8 模式。

最终 18 项回归全部通过（包括检索失败不产生替代结果、不会升级阅读范围、已有文件保护及内部链接检查）。三种分发 ZIP 已生成，内含入口、全部阶段资料、脚本与许可证，SHA256 见 dist/checksums.json。此验证不包含宿主客户端的实际安装。

## 尚未验证

- 未在 Codex、Claude Code、WorkBuddy 的原生客户端逐一安装并完成端到端论文。当前是官方文档对照、技能静态格式、脚本和打包测试。
- 未拿真实学校模板生成最终 Word/PDF/PPT；是否能生成及渲染取决于执行环境，流程要求实际检查，不伪造完成。
- 未验证所有专业的研究充分性，也未认证数据真实性。合成测试样例只测试机械约束，不是有效毕业论文。
- 未创建 GitHub 远程仓库或发布 Release。

## 客户端验收建议

分别安装完整包，在独立测试目录提出“尚未提供学校模板和问卷数据，要求立即交最终论文”的请求。预期应先问必要问题、标记缺失材料，不能生成调查结果或宣布正式完成。

然后用自己合法取得的实际学校要求和资料测试小范围写作，检查引用位置、输出格式和断点续做。记录平台版本、时间、实际结果及偏差，不能只凭模型自述认定通过。

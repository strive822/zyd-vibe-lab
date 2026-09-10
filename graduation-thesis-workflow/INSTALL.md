# 给 AI 助手的安装入口

用户说“安装 https://github.com/strive822/zyd-vibe-lab 里的论文工作流”时，请执行安装，不只复述教程。本仓库含多个项目，目标只限 `graduation-thesis-workflow`，不要安装其他项目。

## 1. 获取文件，不要求用户安装 Git

优先使用宿主已有的技能安装工具，来源子路径为 `graduation-thesis-workflow/skills/graduation-thesis`。没有安装工具时，使用自身下载/文件能力取得完整工作流目录。

- 仓库 ZIP：`https://github.com/strive822/zyd-vibe-lab/archive/refs/heads/main.zip`
- 获取后定位其中 `graduation-thesis-workflow/INSTALL.md` 与 `skills/graduation-thesis/SKILL.md`，先阅读再执行脚本。
- 也可从 README 的 packages 下载对应客户端 ZIP，按客户端能力导入/解压；这条路径不需要 Python、Git 或 Node。
- Windows 可使用系统 PowerShell 的 Invoke-WebRequest 与 Expand-Archive；macOS/Linux 使用宿主文件工具或实际存在的下载/解压工具。不要假设电脑安装了 curl、Git、Python；缺少能力时先检查宿主可用工具，不把命令交给小白。

只从用户指定仓库获取安装材料。ZIP 解压到本次专用缓存目录；拒绝绝对路径、`..` 越界路径或符号链接逃逸，不覆盖用户已有工作目录。失败最多重试两次，不换未知镜像、不假称安装成功。

## 2. 识别当前客户端，完整安装

根据当前宿主身份选择，不要求用户理解隐藏文件夹。

| 客户端 | 安装目标 |
| --- | --- |
| Codex | 优先宿主技能安装器实际使用的目录；手工文件安装可用当前官方个人目录 `~/.agents/skills/graduation-thesis/`，项目安装可用 `.agents/skills/` |
| Claude Code | `~/.claude/skills/graduation-thesis/` 或用户要求的项目 `.claude/skills/` |
| WorkBuddy | 优先宿主内置导入能力；否则检查当前客户端实际的 skills 目录。本机已有 `~/.workbuddy/skills/` 时可使用，但不得把它硬当成所有版本通用路径 |

Windows 已下载完整目录后，由助手调用 `scripts/install.ps1 -Client codex|claude-code|workbuddy`；`-SkillsDir` 可指定已经核实的真实技能根目录。参数里的竖线只是候选说明，调用时必须选择一个值。此脚本不需要 Python，保留同名不同内容技能，不自动覆盖。macOS/Linux 用宿主文件工具完成同样的目录复制与核验，不运行 PowerShell 脚本。

若通过原生导入 ZIP 安装，不再重复复制一次。更新已有技能时先检查现状、备份原文件，在用户更新授权范围内替换，不删除无关技能。

## 3. 核验并马上进入工作流

检查 SKILL.md、references/00-setup.md、scripts/project.py 和 bootstrap-windows.ps1 实际存在且与来源一致。尝试宿主原生技能发现；不能仅凭文件存在就声称已原生启用。热加载未生效时在当前会话直接读取已安装入口继续，必要时请用户重新打开会话；不需要他重新安装软件。

读取已安装的 SKILL.md 和 references/00-setup.md。告诉用户“安装文件完成，开始准备环境并了解论文要求”，而不是要求他学习命令。安装工作流的请求包含配置运行该工作流所必需免费依赖的意图；说明必要下载，然后使用宿主正常权限流程执行。不要自动安装尚不需要的大型工具或付费软件。

Windows 用 bootstrap-windows.ps1 自动探测 Python、按需获取官方安装器和创建隔离环境。先 core，需求确定后才 documents。用 runtime.json 中真实解释器路径运行；不要求用户配置 PATH 或激活 venv。学校格式需要的渲染工具按 00-setup 实际配置并核验。

## 4. 面向用户只问论文问题

安装完只询问专业、学校要求、题目/方向、截止时间及已有材料等必要信息。文件夹可以提出默认位置，交给用户选择。用户不需要填写 JSON、修改脚本、运行终端或阅读开发文档。

底线：网络不可达、无文件/执行权限、管理员确认和缺少真实研究数据都不能由一句提示词消除。遇到这些情况说明具体原因和最少必要操作，继续其他可做工作。不得承诺“所有客户端版本、所有操作系统、任何网络下零交互必定成功”。

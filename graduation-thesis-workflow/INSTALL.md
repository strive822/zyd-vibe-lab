# 给 AI 助手的安装入口

## 给人：自己动手的步骤

1. 打开[固定 Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/graduation-thesis-workflow-v0.5.0-r1)，按客户端选择同名技能 ZIP 和 `SHA256SUMS.txt`。
2. 在下载目录打开命令提示符，核对哈希（应与 `SHA256SUMS.txt` 中所选 ZIP 文件名对应行一致）：

   ```bat
   certutil -hashfile graduation-thesis-codex.zip SHA256
   ```

   上例使用 Codex 包；其他客户端替换为实际下载的 ZIP 文件名，并比对校验文件中的同名行。

3. 在 WorkBuddy 中打开“添加技能 → 上传技能”，上传校验过的 ZIP 并启用。其他客户端解压后，将整个 `graduation-thesis` 文件夹复制到对应的技能目录。[WorkBuddy 官方导入说明](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market#上传技能)

   | 客户端 | 技能目录 |
   | --- | --- |
   | Claude Code | `~/.claude/skills/` |
   | Codex | `~/.agents/skills/` |
   | Pi | `%USERPROFILE%\.pi\agent\skills\`（首次使用需把该目录注册进 `~/.pi/agent/settings.json` 的 `skills` 数组，详见 [docs/INSTALL.md](docs/INSTALL.md)） |

4. 打开新会话，确认客户端能找到 graduation-thesis 技能。输入“用 graduation-thesis 开始我的毕业论文”。已有项目输入“用 graduation-thesis 继续我的论文”，并指向原来的论文目录。

## 给 Agent：交给 AI 执行

用户说“安装 https://github.com/strive822/zyd-vibe-lab 里的论文工作流”时，请执行安装，不只复述教程。本仓库含多个项目，目标只限 `graduation-thesis-workflow`，不要安装其他项目。本文其余小节（获取文件、识别客户端、核验与进入工作流、面向用户只问论文问题）是 Agent 执行时的完整约束。

## 1. 获取文件，不要求用户安装 Git

按上面的固定 Release 下载当前客户端的技能 ZIP 和 `SHA256SUMS.txt`。核对所选 ZIP 文件名及 SHA-256 后才导入或解压。用宿主已有的下载、哈希和解压能力即可，Windows 可使用系统 PowerShell 或 certutil。先读包内 `graduation-thesis/SKILL.md` 再执行其中的脚本。

只从用户指定仓库获取安装材料。ZIP 解压到本次专用缓存目录；拒绝绝对路径、`..` 越界路径或符号链接逃逸，不覆盖用户已有工作目录。失败最多重试两次，不换未知镜像、不假称安装成功。

## 2. 识别当前客户端，完整安装

根据当前宿主身份选择，不要求用户理解隐藏文件夹。

| 客户端 | 安装目标 |
| --- | --- |
| Codex | 优先宿主技能安装器实际使用的目录；手工文件安装可用当前官方个人目录 `~/.agents/skills/graduation-thesis/`，项目安装可用 `.agents/skills/` |
| Claude Code | `~/.claude/skills/graduation-thesis/` 或用户要求的项目 `.claude/skills/` |
| Pi | `%USERPROFILE%\.pi\agent\skills\graduation-thesis\`（与 Codex 目录分离）。安装器只复制文件；Pi 需先把 `~/.pi/agent/skills` 注册进 `~/.pi/agent/settings.json` 的 `skills` 数组才发现技能，注册由助手在用户授权下完成（先备份、幂等、解析失败即停），见 [docs/INSTALL.md](docs/INSTALL.md) |
| WorkBuddy | 优先宿主内置导入能力；否则检查当前客户端实际的 skills 目录。本机已有 `~/.workbuddy/skills/` 时可使用，但不得把它硬当成所有版本通用路径 |

使用宿主导入工具时传入校验过的 ZIP。需要文件方式安装时，将 ZIP 中完整的 `graduation-thesis` 目录复制到已核实的技能根目录。同名目录已存在时先核对内容并保护原文件。源码维护者可用仓库内的 `scripts/install.ps1` 做独立安装测试。

若通过原生导入 ZIP 安装，不再重复复制一次。更新已有技能时先检查现状、备份原文件，在用户更新授权范围内替换，不删除无关技能。

## 3. 核验并马上进入工作流

检查 `SKILL.md`、`references/00-setup.md`、`scripts/project.py`、`scripts/check_literature.py` 和 `scripts/bootstrap-windows.ps1` 与已校验的包一致。尝试宿主原生技能发现。热加载未生效时可在当前会话直接读取入口继续，必要时请用户重新打开会话。

读取已安装的 SKILL.md 和 references/00-setup.md。告诉用户“安装文件完成，开始准备环境并了解论文要求”，而不是要求他学习命令。安装工作流的请求包含配置运行该工作流所必需免费依赖的意图；说明必要下载，然后使用宿主正常权限流程执行。不要自动安装尚不需要的大型工具或付费软件。

Windows 用 bootstrap-windows.ps1 自动探测 Python、按需获取官方安装器和创建隔离环境。先 core，需求确定后才 documents。用 runtime.json 中真实解释器路径运行；不要求用户配置 PATH 或激活 venv。学校格式需要的渲染工具按 00-setup 实际配置并核验。

## 4. 面向用户只问论文问题

安装完只询问专业、学校要求、题目/方向、截止时间及已有材料等必要信息。文件夹可以提出默认位置，交给用户选择。用户不需要填写 JSON、修改脚本、运行终端或阅读开发文档。

底线：网络不可达、无文件/执行权限、管理员确认和缺少真实研究数据都不能由一句提示词消除。遇到这些情况说明具体原因和最少必要操作，继续其他可做工作。不得承诺“所有客户端版本、所有操作系统、任何网络下零交互必定成功”。

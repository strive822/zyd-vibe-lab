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

用户说“用 https://github.com/strive822/zyd-vibe-lab 里的论文工作流”时，按宿主实际能力开始。目标项目是 `graduation-thesis-workflow`，只处理用户指定的论文目录。

## 1. 获取文件，不要求用户安装 Git

按上面的固定 Release 下载当前客户端的技能 ZIP 和 `SHA256SUMS.txt`。没有专用包时选择 `graduation-thesis-codex.zip`，其内容与 Claude Code 包、Pi 包一致。核对所选 ZIP 文件名及 SHA-256 后才导入或解压。用宿主已有的下载、哈希和解压能力即可。先读包内 `graduation-thesis/SKILL.md` 再执行其中的脚本。

只从用户指定仓库获取安装材料。ZIP 解压到本次专用缓存目录；拒绝绝对路径、`..` 越界路径或符号链接逃逸，不覆盖用户已有工作目录。失败最多重试两次，不换未知镜像、不假称安装成功。

## 2. 识别当前客户端，完整安装

根据当前宿主身份选择，不要求用户理解隐藏文件夹。

| 客户端 | 安装目标 |
| --- | --- |
| Codex | 优先宿主技能安装器实际使用的目录；手工文件安装可用当前官方个人目录 `~/.agents/skills/graduation-thesis/`，项目安装可用 `.agents/skills/` |
| Claude Code | `~/.claude/skills/graduation-thesis/` 或用户要求的项目 `.claude/skills/` |
| Pi | `%USERPROFILE%\.pi\agent\skills\graduation-thesis\`（与 Codex 目录分离）。安装器只复制文件；Pi 需先把 `~/.pi/agent/skills` 注册进 `~/.pi/agent/settings.json` 的 `skills` 数组才发现技能，注册由助手在用户授权下完成（先备份、幂等、解析失败即停），见 [docs/INSTALL.md](docs/INSTALL.md) |
| WorkBuddy | 优先宿主内置导入能力；否则检查当前客户端实际的 skills 目录。本机已有 `~/.workbuddy/skills/` 时可使用，但不得把它硬当成所有版本通用路径 |
| 其他 Agent | 有 Agent Skills 加载能力时按客户端说明导入完整文件夹。支持文件读取时也可直接使用下方的通用入口。 |

使用宿主导入工具时传入校验过的 ZIP。需要文件方式安装时，将 ZIP 中完整的 `graduation-thesis` 目录复制到已核实的技能根目录。同名目录已存在时先核对内容并保护原文件。源码维护者可用仓库内的 `scripts/install.ps1` 做独立安装测试。

更新已有技能时先核对现状并备份用户文件，按用户授权替换。

### 通用入口

把核验后解压得到的 `graduation-thesis/` 放在 Agent 能访问的位置。让 Agent 直接读取该目录下的 `SKILL.md`，按其中相对路径读取 `references/` 和运行 `scripts/`。此路径无需登记技能或修改客户端配置。论文保存在独立目录，更换 Agent 时直接提供同一个论文目录，读取原来的项目状态和证据。

如果当前 Agent 只能对话或联网检索，可用公开材料做选题、检索与审阅。需要创建项目文件、运行检查或生成文件格式时，转到有对应权限的设备。仅能读取附件时，可提供获准共享的必要文件，真实论文、问卷或账户资料沿用原有授权。

## 3. 核验并马上进入工作流

检查 `SKILL.md`、`references/00-setup.md`、`scripts/project.py`、`scripts/check_literature.py` 和 `scripts/bootstrap-windows.ps1` 与已校验的包一致。选择安装时验证宿主能否发现技能，热加载未生效可用通用入口。选择通用入口时，核验入口与所需文件实际可读。

读取 `SKILL.md` 和 `references/00-setup.md` 后说明实际完成的步骤。有原项目时先读取 `requirements.json`、`state.json`、`NEXT.md`、`DECISIONS.md` 及最近审查记录，从已有进度继续。需要免费依赖时说明用途，按宿主权限流程执行。

Windows 先检测可用 Python，再按需使用 bootstrap-windows.ps1 准备隔离环境。先 core，需求确定后才 documents。用 runtime.json 中的实际解释器运行。学校格式需要的渲染工具按 00-setup 实际配置并核验。

## 4. 面向用户只问论文问题

开始新项目时只询问专业、学校要求、题目或方向、截止时间及已有材料等必要信息。续做时只补待确认内容。用户不需要填写 JSON、修改脚本、运行终端或阅读开发文档。

底线：网络不可达、无文件/执行权限、管理员确认和缺少真实研究数据都不能由一句提示词消除。遇到这些情况说明具体原因和最少必要操作，继续其他可做工作。不得承诺“所有客户端版本、所有操作系统、任何网络下零交互必定成功”。

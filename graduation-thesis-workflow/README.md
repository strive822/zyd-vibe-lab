# 毕业论文工作流 · Graduation Thesis Workflow

面向各专业本科论文的可移植 Agent Skill。通过 grilling 式访谈确认学校要求和必要条件，再自动推进文献、研究、写作、审查与交付。目标是满足毕业论文要求，不承诺毕业、录用或检测分数。

**不编造文献、数据、实验、引文、审批或导师反馈。材料不足时完成能做的部分并列出缺口，补齐后续做。** 规则和脚本降低出错风险，不能数学保证模型永不犯错，也不能代替作者、导师对学术内容负责。

## 零基础使用：只对助手说一句话

打开 **Codex、Claude Code 或 WorkBuddy**，发送：

```text
安装 https://github.com/strive822/zyd-vibe-lab 里的论文工作流。
```

电脑上只有 WorkBuddy 也可以从这一步开始，**不需要先学 Git、Python，不需要自己敲终端命令**。助手会读取本仓库的 [安装入口](INSTALL.md)，下载工作流、识别当前工具并安装，再检查运行环境。

### 接下来会发生什么？

1. **助手安装技能。** 你不用自己寻找隐藏文件夹或解压到特定路径。
2. **助手准备环境。** Windows 缺 Python 时自动从官网取得安装器并配置隔离环境；写文档所需免费依赖按实际需求补齐。系统或助手弹出权限确认时，由你点击确认。
3. **助手了解论文要求。** 你回答专业、学校要求、截止时间、题目方向和已有材料等问题。没有题目也可以先讨论。
4. **确认后继续完成工作。** 获取真实文献、研究和写作，最后自动执行 Humanizer 润色，再检查引用、数字、结论和排版。

如果安装后助手暂时停在完成提示，直接说：

```text
开始我的毕业论文，先了解必要需求，其余准备工作请你自动完成。
```

你只需准备学校模板/要求和实际拥有的材料，不需要手填配置文件。学校要求不同，生成的论文格式、开题、中期、答辩附件也会不同。缺真实数据时，助手会先做其他部分，再告诉你需要补什么，不会编造问卷或实验。

中断后说“继续我的论文”，并让助手打开原来的论文文件夹即可。

### 自动安装的条件

助手需要能联网、读写文件、执行必要工具；Windows 10/11 提供本包的自动环境脚本，不要求预装 Git/Python。macOS/Linux 由助手使用对应平台工具准备，尚未实测其零依赖启动。企业限制、网络故障或系统权限不能由提示词跳过。文件复制成功、客户端识别成功和环境准备成功会分别核验。

**Humanizer 用于改善语言表达，不保证降低 AI 检测分数或文字重复率。** 润色保留来源、研究事实和学校要求的披露。工作流不保证毕业，也不会伪造检测报告。

### 如果助手没有找到安装入口

发送这句补充：

```text
请读取该仓库根目录 INSTALL.md，然后执行 graduation-thesis-workflow/INSTALL.md。
不要只给我手动安装教程，请在权限允许范围内完成安装并检查环境。
```

也保留直接导入包作为备用，不需要运行打包命令：

| 工具 | 安装包 |
| --- | --- |
| WorkBuddy | [下载 WorkBuddy ZIP](https://github.com/strive822/zyd-vibe-lab/raw/refs/heads/main/graduation-thesis-workflow/packages/graduation-thesis-workbuddy.zip) |
| Codex | [下载 Codex ZIP](https://github.com/strive822/zyd-vibe-lab/raw/refs/heads/main/graduation-thesis-workflow/packages/graduation-thesis-codex.zip) |
| Claude Code | [下载 Claude Code ZIP](https://github.com/strive822/zyd-vibe-lab/raw/refs/heads/main/graduation-thesis-workflow/packages/graduation-thesis-claude-code.zip) |

以下内容面向希望了解实现或维护仓库的人，普通使用者无需操作。

## 当前包含什么

- 一个自包含技能入口，按需读取环境准备及八个阶段模块：访谈、设计、检索、研究执行、写作、审查、Humanizer、排版交付。
- 五类研究方法分支：文献研究、定量、定性、工程系统和实验；支持组合。各专业的具体规范需要项目内补充。
- 真实 Crossref 元数据检索脚本，以及 arXiv、PubMed/PMC、ERIC、中文数据库等合法来源的检索指引。没有声称实现所有数据库 API。
- 无 Git/Python 的 Windows 技能安装脚本、按需环境准备、项目初始化、文件哈希、交付检查和断点续做。
- Codex / Claude Code / WorkBuddy 分发 ZIP 生成器。

不是独立后台应用。自动程度取决于宿主权限、联网、运行能力、额度和材料是否可得。用户关闭应用后不会因此保持运行。机械检查 PASS 只表示登记与文件一致，不证明研究结论真实。

## 仓库结构

```text
skills/graduation-thesis/  唯一技能源，包含 SKILL.md、阶段模块、脚本
scripts/package.py        生成三种自包含 ZIP
packages/                 可直接下载的三端 ZIP 和 SHA256 清单
tests/                    隔离的合成测试，不是论文数据
docs/                     安装、验证和发布说明
README.md                 产品范围和使用入口
DEVLOG.md                 开发记录
DECISIONS.md              设计取舍
GOTCHAS.md                已知问题与边界
SOP.md                    维护和发布流程
```

真实论文、个人信息、学校材料和数据默认不进入公开仓库。新建论文项目的 `.gitignore` 默认忽略项目内容，后续是否进行私有版本管理由使用者决定。

## 本地验证与打包

在仓库根目录运行：

```text
python -m unittest discover -s tests -v
python scripts/package.py --out packages
```

可下载的 ZIP 位于 `packages/`，附 SHA256 清单；维护时使用上面的命令同步重建。发布到 GitHub 的步骤见 [发布指南](docs/RELEASE.md)。当前验证范围见 [验证记录](docs/VALIDATION.md)，不能把打包成功等同于三端真实论文端到端验证。

## 来源与许可

本仓库原创流程与脚本采用 [MIT License](LICENSE)。访谈流程为原创实现；Humanizer 3.0.0 已按 MIT 许可内置，保留上游版权、固定提交和文件哈希，见 [第三方说明](THIRD_PARTY_NOTICES.md)。未复制图片中来源不明的技能。可复用宿主已有文档技能，但不分发其受独立许可约束的内容。

官方格式与接口依据：[Codex Skills](https://learn.chatgpt.com/docs/build-skills)、[Claude Code Skills](https://code.claude.com/docs/en/skills)、[WorkBuddy 技能结构](https://open.workbuddy.cn/docs/skill)、[Crossref REST API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/)。

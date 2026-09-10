# 毕业论文工作流 · Graduation Thesis Workflow

面向各专业本科论文的可移植 Agent Skill。通过 grilling 式访谈确认学校要求和必要条件，再自动推进文献、研究、写作、审查与交付。目标是满足毕业论文要求，不承诺毕业、录用或检测分数。

**不编造文献、数据、实验、引文、审批或导师反馈。材料不足时完成能做的部分并列出缺口，补齐后续做。** 规则和脚本降低出错风险，不能数学保证模型永不犯错，也不能代替作者、导师对学术内容负责。

## 先看这里：怎么用？

你需要已有的 **Codex、Claude Code 或 WorkBuddy**。这不是一个点击后独立运行的网站，也不包含大模型账号。下载技能包不收费，运行助手可能使用你已有的订阅或额度。

### 第一步：下载与你的工具对应的包

| 你使用的工具 | 下载 | 安装位置或方式 |
| --- | --- | --- |
| Codex | [下载 Codex ZIP](https://github.com/strive822/zyd-vibe-lab/raw/refs/heads/main/graduation-thesis-workflow/packages/graduation-thesis-codex.zip) | 解压后把完整 `graduation-thesis` 文件夹放到论文项目的 `.agents/skills/` |
| Claude Code | [下载 Claude Code ZIP](https://github.com/strive822/zyd-vibe-lab/raw/refs/heads/main/graduation-thesis-workflow/packages/graduation-thesis-claude-code.zip) | 解压后放到论文项目的 `.claude/skills/`，或个人 `~/.claude/skills/` |
| WorkBuddy | [下载 WorkBuddy ZIP](https://github.com/strive822/zyd-vibe-lab/raw/refs/heads/main/graduation-thesis-workflow/packages/graduation-thesis-workbuddy.zip) | 技能界面 → 添加技能 → 上传技能，导入 ZIP 并启用 |

ZIP 内包含一个 `graduation-thesis` 文件夹。不要多套一层同名文件夹，也不要只复制 SKILL.md。完整安装说明和兼容性边界见 [安装指南](docs/INSTALL.md)。

### 第二步：新建一个私有论文目录，发送这段话

```text
使用 graduation-thesis，在我指定的私有论文目录启动本科毕业论文工作流。
先用 grilling 式访谈确认我的专业、学校要求、选题、材料和交付物。
确认需求后自动推进；不得编造文献、引用、数据、实验或结论。
缺少必要材料时先完成其他可做工作，再集中告诉我需要补什么。
```

Codex 可用 `$graduation-thesis`，Claude Code 可用 `/graduation-thesis`；WorkBuddy 在对话中选择或要求使用该技能。安装后按工具需要重新打开会话。

**技能可以安装在论文工作目录内，但初始化的资料子目录必须是新的或空的。** 例如工作目录中已有 `.agents/skills/`，就让助手把资料初始化到其下的 `thesis-project/`，不要在非空工作目录根部初始化。

### 第三步：回答问题，提供真实材料

可以先不知道题目，由访谈协助确定。学校要求/模板、截止时间、已有文献和数据按实际情况提供，不需要自己填 JSON。论文格式、是否需要开题/中期/PPT 等由你确认；助手负责维护项目文件。

没有问卷、访谈或实验结果时，流程不会替你制造数据。它会完成有依据的部分，列出缺口，材料补齐后继续。

### 中断后如何继续？

```text
使用 graduation-thesis 继续这个论文目录，先读 requirements.json、state.json 和 NEXT.md。
```

**预期产出**：你确认需要的论文稿件与附件、文献和证据记录、审查记录。是否真正满足学校要求仍需作者与导师核对，不能保证毕业或检测分数。

辅助脚本需要 Python 3.10+，没有第三方 Python 依赖；联网检索需要网络，Word/PDF/PPT 生成与排版检查需要助手环境具备相应工具。首次启动会检查能力并报告缺项。

不安装也能尝试：下载完整仓库，在能读文件的助手中要求读取 `graduation-thesis-workflow/skills/graduation-thesis/SKILL.md` 并执行，提供实际本地路径。

## 第一版包含什么

- 一个自包含技能入口，按需读取七个阶段模块：访谈、设计、检索、研究执行、写作、审查、排版交付。
- 五类研究方法分支：文献研究、定量、定性、工程系统和实验；支持组合。各专业的具体规范需要项目内补充。
- 真实 Crossref 元数据检索脚本，以及 arXiv、PubMed/PMC、ERIC、中文数据库等合法来源的检索指引。没有声称实现所有数据库 API。
- 项目初始化、文件哈希、交付结构检查和断点续做协议。
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

本仓库原创流程与脚本采用 [MIT License](LICENSE)。未复制第三方 grilling、humanizer 或图片中来源不明的技能；访谈能力内置，humanizer 为可选外部工具，不是启动依赖。可复用宿主已有文档技能，但不分发其受独立许可约束的内容。

官方格式与接口依据：[Codex Skills](https://learn.chatgpt.com/docs/build-skills)、[Claude Code Skills](https://code.claude.com/docs/en/skills)、[WorkBuddy 技能结构](https://open.workbuddy.cn/docs/skill)、[Crossref REST API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/)。

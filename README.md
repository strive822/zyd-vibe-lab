# zyd-vibe-lab

zhongyudi 的个人项目仓库：各项目独立下载、安装、运行和维护；原工具箱已拆为五个独立目录。

> 原 github-toolbox 已拆为五个独立项目；全部 8 个项目都有自己的 Agent 入口、独立下载包和 SHA-256。

## 直接让 Agent 帮你使用

把下面任意一句发给具备联网、文件读写和运行能力的 Agent。它应先读本仓库 [INSTALL.md](INSTALL.md)，按项目名选择入口，再完成下载、核验与启动。系统权限、学校材料和账号登录仍需本人处理。

**毕业论文工作流（Codex / Claude Code / WorkBuddy）：**

```text
安装并使用 https://github.com/strive822/zyd-vibe-lab 里的 graduation-thesis-workflow。请先读取仓库 INSTALL.md，完整安装技能并检查环境，然后开始了解我的论文要求。
```

**三资产定投计算器：**

```text
下载并运行 https://github.com/strive822/zyd-vibe-lab 里的 dca-calculator。请先读取仓库 INSTALL.md，自动准备隔离环境与依赖，启动前后端并验证页面；不要覆盖已有项目。
```

**Windows 额度浮窗：**

```text
下载并运行 https://github.com/strive822/zyd-vibe-lab 里的 codex-usage。请先读取仓库 INSTALL.md，优先使用 Windows x64 便携包，核对 SHA-256 后完整解压并启动；保留已有配置，不代填密钥或开启自启动。
```

**LibreTV：**

```text
下载并运行 https://github.com/strive822/zyd-vibe-lab 里的 LibreTV。请先读取该项目 INSTALL.md，取得完整独立目录，核对校验值，在新目录恢复固定版本、个人启动入口与预置源，准备项目内运行时和依赖，启动并验证页面；不要覆盖现有服务。
```

**yt-dlp：**

```text
下载并准备使用 https://github.com/strive822/zyd-vibe-lab 里的 yt-dlp。请先读取该项目 INSTALL.md，取得完整独立目录并核验，在新目录准备 yt-dlp、FFmpeg、Deno 和下载入口，验证版本；不要全局安装，不自动下载视频。
```

**Windows-MCP：**

```text
下载并准备使用 https://github.com/strive822/zyd-vibe-lab 里的 Windows-MCP。请先读取该项目 INSTALL.md，在新目录恢复固定源码与入口，使用项目内环境安装必要依赖并验证；保留已有配置，注册 MCP 接入前先说明具体改动。
```

**rea：**

```text
下载 https://github.com/strive822/zyd-vibe-lab 里的 rea。请先读取该项目 INSTALL.md，取得完整独立目录，下载并核验固定的 rea-agents 包，保留许可和使用说明；不全局安装、不自动运行 setup 或安装分析引擎。
```

**Winhance：**

```text
下载 https://github.com/strive822/zyd-vibe-lab 里的 Winhance。请先读取该项目 INSTALL.md，取得完整独立目录，下载官方固定版本安装包并核对 SHA-256，保留使用说明和许可；只下载，不运行安装器或修改系统设置。
```

**今日待办（电脑与手机局域网共用清单）：**

```text
下载并运行 https://github.com/strive822/zyd-vibe-lab 里的 today-todo。请先读取该项目 INSTALL.md，把文件放进新目录并核验，再用 Node.js 启动本地服务、打开 http://localhost:3000 验证页面；不要覆盖已有的数据文件。
```

**白龙桌宠（多平台额度与 Token）：**

```text
下载并运行 https://github.com/strive822/zyd-vibe-lab 里的 codex-bailong-desktop-pet。请先读取该项目 INSTALL.md，下载完整文件并核验，在新目录准备项目内 Python 环境和已验证的官方播放素材，然后启动并检查；保留已有文件与账号，不全局安装、不代填密钥、不自动开启自启动。
```

简短说“安装这个仓库里的论文工作流”也可使用论文入口。未指定项目时，Agent 应先确认项目。

## 项目与下载

| 项目 | 用途 | Agent 入口 | 下载方式 |
| --- | --- | --- | --- |
| [graduation-thesis-workflow](graduation-thesis-workflow/README.md) | 本科论文需求访谈、真实文献与证据、写作审查；包含 Humanizer | [安装技能](graduation-thesis-workflow/INSTALL.md) | [独立 ZIP](https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/graduation-thesis-workflow/delivery/graduation-thesis-workflow.zip) · [SHA-256](https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/graduation-thesis-workflow/delivery/SHA256SUMS.txt) |
| [dca-calculator](dca-calculator/README.md) | 三资产 SMA800 定投权重与金额计算，FastAPI + Next.js | [下载与启动](dca-calculator/INSTALL.md) | [独立 ZIP](https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/dca-calculator/delivery/dca-calculator.zip) · [SHA-256](https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/dca-calculator/delivery/SHA256SUMS.txt) |
| [codex-usage](codex-usage/README.md) | Windows 三平台额度、六位快捷复制和每日提醒，Python + PySide6 | [便携包与源码](codex-usage/INSTALL.md) | [独立 ZIP](https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/codex-usage/delivery/codex-usage.zip) · [SHA-256](https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/codex-usage/delivery/SHA256SUMS.txt) |
| [LibreTV](LibreTV/README.md) | 独立的个人使用配置与固定下载版本 | [Agent 入口](LibreTV/INSTALL.md) | [独立 ZIP](https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/LibreTV/delivery/LibreTV.zip) · [SHA-256](https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/LibreTV/delivery/SHA256SUMS.txt) |
| [yt-dlp](yt-dlp/README.md) | 独立的个人使用配置与固定下载版本 | [Agent 入口](yt-dlp/INSTALL.md) | [独立 ZIP](https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/yt-dlp/delivery/yt-dlp.zip) · [SHA-256](https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/yt-dlp/delivery/SHA256SUMS.txt) |
| [Windows-MCP](Windows-MCP/README.md) | 独立的个人使用配置与固定下载版本 | [Agent 入口](Windows-MCP/INSTALL.md) | [独立 ZIP](https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/Windows-MCP/delivery/Windows-MCP.zip) · [SHA-256](https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/Windows-MCP/delivery/SHA256SUMS.txt) |
| [rea](rea/README.md) | 独立的个人使用配置与固定下载版本 | [Agent 入口](rea/INSTALL.md) | [独立 ZIP](https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/rea/delivery/rea.zip) · [SHA-256](https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/rea/delivery/SHA256SUMS.txt) |
| [Winhance](Winhance/README.md) | 独立的个人使用配置与固定下载版本 | [Agent 入口](Winhance/INSTALL.md) | [独立 ZIP](https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/Winhance/delivery/Winhance.zip) · [SHA-256](https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/Winhance/delivery/SHA256SUMS.txt) |
| [today-todo](today-todo/README.md) | 电脑与手机局域网共用的今日清单，零依赖 Node 服务 + 原生前端 | [下载与启动](today-todo/INSTALL.md) | [独立 ZIP](https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/today-todo/delivery/today-todo.zip) · [SHA-256](https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/today-todo/delivery/SHA256SUMS.txt) |
| [codex-bailong-desktop-pet](codex-bailong-desktop-pet/README.md) | 白龙桌宠，多平台额度、Token 与悬浮胶囊 | [安装与使用](codex-bailong-desktop-pet/INSTALL.md) | [独立 ZIP](https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/codex-bailong-desktop-pet/delivery/codex-bailong-desktop-pet.zip) · [SHA-256](https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/codex-bailong-desktop-pet/delivery/SHA256SUMS.txt) |

论文工作流不保证毕业或检测分数；计算器只计算，不执行交易；浮窗为未签名的个人使用候选，设备验收边界见项目说明。

## 维护

从仓库根目录运行 `python scripts/check_repository.py`，检查受 Git 管理的文件、文档链接、Python 语法、下载包校验和及源码一致性。各项目的测试命令见对应 README；持续检查配置在 [.github/workflows/checks.yml](.github/workflows/checks.yml)。

本轮检查范围、修复与尚未验证的项目见 [Repository Cleanup Report](docs/REPOSITORY_CLEANUP_REPORT.md)。

## 许可证

[计算器](dca-calculator/LICENSE)与[论文工作流](graduation-thesis-workflow/LICENSE)的原创内容使用各自目录的 MIT 许可证；论文工作流中的 Humanizer 保留上游许可。codex-usage 的第三方许可见 [THIRD_PARTY.md](codex-usage/docs/guides/THIRD_PARTY.md)，其原创源码尚未单独声明许可证。


## 新增项目交付规范

以后每个新增、上传的项目都必须在自己的 README.md 中提供“直接让 Agent 帮你使用”、
包含仓库地址与项目名的可复制提示词，以及真实可执行的 INSTALL.md。
根 README 同步增加提示词和项目入口，校验和与交付包保持一致。
规范和模板见 [Agent 交付规范](docs/AGENT_DELIVERY_STANDARD.md)。

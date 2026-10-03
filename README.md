# zyd-vibe-lab

zhongyudi 的个人项目仓库：三个项目独立安装、运行和维护。

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

简短说“安装这个仓库里的论文工作流”也可使用论文入口。未指定项目时，Agent 应先确认项目。

## 项目与下载

| 项目 | 用途 | Agent 入口 | 下载方式 |
| --- | --- | --- | --- |
| [graduation-thesis-workflow](graduation-thesis-workflow/README.md) | 本科论文需求访谈、真实文献与证据、写作审查；包含 Humanizer | [安装技能](graduation-thesis-workflow/INSTALL.md) | [Codex](graduation-thesis-workflow/packages/graduation-thesis-codex.zip) · [Claude Code](graduation-thesis-workflow/packages/graduation-thesis-claude-code.zip) · [WorkBuddy](graduation-thesis-workflow/packages/graduation-thesis-workbuddy.zip) |
| [dca-calculator](dca-calculator/README.md) | 三资产 SMA800 定投权重与金额计算，FastAPI + Next.js | [下载与启动](dca-calculator/INSTALL.md) | [完整仓库 ZIP](https://github.com/strive822/zyd-vibe-lab/archive/refs/heads/main.zip)，取其中 dca-calculator |
| [codex-usage](codex-usage/README.md) | Windows 三平台额度、六位快捷复制和每日提醒，Python + PySide6 | [便携包与源码](codex-usage/INSTALL.md) | [Windows x64 ZIP](codex-usage/packages/usage-0.1.0-windows-x64.zip) · [校验值](codex-usage/packages/SHA256SUMS.txt) |

论文工作流不保证毕业或检测分数；计算器只计算，不执行交易；浮窗为未签名的个人使用候选，设备验收边界见项目说明。

## 维护

从仓库根目录运行 `python scripts/check_repository.py`，检查受 Git 管理的文件、文档链接、Python 语法、下载包校验和及源码一致性。各项目的测试命令见对应 README；持续检查配置在 [.github/workflows/checks.yml](.github/workflows/checks.yml)。

本轮检查范围、修复与尚未验证的项目见 [Repository Cleanup Report](docs/REPOSITORY_CLEANUP_REPORT.md)。

## 许可证

[计算器](dca-calculator/LICENSE)与[论文工作流](graduation-thesis-workflow/LICENSE)的原创内容使用各自目录的 MIT 许可证；论文工作流中的 Humanizer 保留上游许可。codex-usage 的第三方许可见 [THIRD_PARTY.md](codex-usage/docs/guides/THIRD_PARTY.md)，其原创源码尚未单独声明许可证。


# 安装论文工作流（供 Codex / Claude Code / WorkBuddy 读取）

当用户说“安装这个仓库里的工作流”，目标是 graduation-thesis-workflow，不是其他项目。

请读取并执行 [论文工作流安装入口](graduation-thesis-workflow/INSTALL.md)。

- 技能源路径：`graduation-thesis-workflow/skills/graduation-thesis`。
- 不要求用户手动安装 Git、Python 或敲终端命令。优先使用宿主技能安装工具；否则下载完整工作流并使用平台文件能力安装。
- Windows 可执行 `graduation-thesis-workflow/scripts/install.ps1`，按实际宿主选择 Client；然后由已安装技能的 bootstrap-windows.ps1 按需准备环境。
- 自动执行必要且已授权的免费依赖准备。权限提示由用户确认，不能绕过组织策略。
- 安装后读取 SKILL.md 开始论文需求访谈。Humanizer 已包含在包内，交付前自动润色并重新核验，不保证检测分数。
- 不要只返回安装教程；完成文件核验、客户端发现检查及环境检查，分别报告真实状态。

用户教程见 [项目首页](graduation-thesis-workflow/README.md)。

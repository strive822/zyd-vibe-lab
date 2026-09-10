# zyd-vibe-lab

> zhongyudi 的 vibe-coding 实验仓库。这里收纳我从零搭建、用于学习与展示的个人小项目。

## 一句话安装论文工作流

在 **Codex、Claude Code 或 WorkBuddy** 中发送：

```text
安装 https://github.com/strive822/zyd-vibe-lab 里的论文工作流。
```

不用先学 Git 或 Python。助手按 [安装入口](INSTALL.md) 获取技能、按需配置免费依赖，再了解学校要求；最后自动使用 Humanizer 改善表达并复核证据。系统权限提示仍需本人确认，不承诺毕业或检测分数。

**给 AI 助手：** 请执行 [INSTALL.md](INSTALL.md)，目标技能源是 `graduation-thesis-workflow/skills/graduation-thesis`。不要只向小白返回手动安装教程。

完整说明：[论文工作流使用指南](graduation-thesis-workflow/README.md)。

## 项目列表

| 项目 | 说明 | 技术栈 |
| --- | --- | --- |
| [dca-calculator](./dca-calculator/) | 三资产（纳斯达克100 / 中证500 / 黄金）定投权重计算器，含 C哥模型与严谨模型双权重方案，支持单文件 exe 打包 | FastAPI + Next.js + Tailwind CSS |
| [graduation-thesis-workflow](./graduation-thesis-workflow/) | 本科毕业论文工作流：需求访谈、真实文献与证据、写作审查；含三端下载和使用教程 | Codex / Claude Code / WorkBuddy · Python |

## 许可证

各子项目许可证见对应目录（如 [dca-calculator/LICENSE](./dca-calculator/LICENSE)）。

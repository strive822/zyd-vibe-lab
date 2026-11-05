# 安装与使用入口

## 给人：自己动手的步骤

在下面选择项目，打开它的 INSTALL.md；从固定 Release 下载程序、启动包或技能包及 `SHA256SUMS.txt`，核验后按该项目说明使用。无需先学 Git，也无需下载整个开发仓库。

| 项目 | 交付形式 | 说明 | 下载 |
| --- | --- | --- | --- |
| [岛仔 Daozai](daozai/README.md) | Windows 安装器 | [安装与验证](daozai/INSTALL.md) | [Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/daozai-v0.6.50-r4) |
| [三资产定投计算器](dca-calculator/README.md) | 网页启动包（前端已构建） | [安装与验证](dca-calculator/INSTALL.md) | [Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/dca-calculator-v1.0.0-r1) |
| [飞鼠格式](flyingmouse-format/README.md) | 官方安装器联网安装入口 | [安装与验证](flyingmouse-format/INSTALL.md) | [Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/flyingmouse-format-v0.8.3-r1) |
| [毕业论文工作流](graduation-thesis-workflow/README.md) | Codex / Claude Code / Pi / WorkBuddy 技能包 | [安装与验证](graduation-thesis-workflow/INSTALL.md) | [Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/graduation-thesis-workflow-v0.4.0-r1) |
| [LibreTV](libretv/README.md) | 网页生产运行包 | [安装与验证](libretv/INSTALL.md) | [Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/libretv-v2.21.1-r2) |
| [Pi 任务通知](pi-task-notify/README.md) | Pi 宿主扩展包 | [安装与验证](pi-task-notify/INSTALL.md) | [Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/pi-task-notify-v0.2.0-r1) |
| [REA](rea/README.md) | 固定版本 CLI 联网准备包 | [安装与验证](rea/INSTALL.md) | [Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/rea-v6.8.0-r2) |
| [今日待办](today-todo/README.md) | 零依赖 Node 网页启动包 | [安装与验证](today-todo/INSTALL.md) | [Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/today-todo-v1.0.0-r1) |
| [Windows-MCP](windows-mcp/README.md) | MCP 服务联网准备包 | [安装与验证](windows-mcp/INSTALL.md) | [Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/windows-mcp-v0.8.8-r2) |
| [yt-dlp](yt-dlp/README.md) | CLI 工具链联网准备包 | [安装与验证](yt-dlp/INSTALL.md) | [Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/yt-dlp-v2026.10.26-r2) |

Windows 在下载目录运行 `Get-FileHash -Algorithm SHA256 .\下载的文件名`，与同一 Release 的 `SHA256SUMS.txt` 比对；macOS/Linux 可用 `shasum -a 256`。ZIP 解压到新目录，已有数据留在原处。

## 给 Agent：交给 AI 执行

```text
安装并使用 https://github.com/strive822/zyd-vibe-lab 里的 <项目名>。先读取对应 INSTALL.md，从固定 Release 下载成品并核验大小与 SHA-256，再按该项目类型安装或启动，完成对应验证。保留已有账号、数据和配置；只下载时不安装、不启动。不安装无关项目。
```

本文和所选项目 INSTALL.md 是 Agent 执行时的完整约束。先确定项目、平台、已有安装和本次请求范围；信息已明确时直接执行，不重复索要确认。

## Agent 的执行顺序

1. 读取项目 INSTALL.md 与 [releases.json](releases.json)，使用固定 tag 与附件，不猜最新版本、不把源码 ZIP 当程序。
2. 下载到仓库外的新目录，核对大小和 SHA-256；已有同名不同内容文件不覆盖。仅下载不会安装或启动。
3. 执行该项目的安装/启动入口。联网准备包会按其 assets.json 下载固定官方运行时或工具，并再次校验；不是离线全量包。
4. 分别验证文件、进程/页面和宿主接入；不能凭文件存在声称已安装、凭单元测试声称真实账号或手机已接通。
5. 保留用户数据。MCP 注册、REA setup、扩展持久接入按用户本次授权执行，不覆盖其他服务或配置。不安装用户未选择的其他项目。

## 开发源码

只有阅读、修改、测试和重新发布才需要 Git 源码。各目录 AGENTS.md 给出开发验证命令；构建与下载目录放在 `~/.codex/.tmp/<任务名>/`，不要把 node_modules、target、虚拟环境或成品提交到仓库。

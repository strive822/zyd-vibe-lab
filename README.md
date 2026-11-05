# zyd-vibe-lab

zhongyudi 的 10 个独立项目。仓库保存源码、测试、配置模板、锁文件与许可证；用户安装或运行的成品放各项目 GitHub Release。Git 提交与标签保留；每个项目的 Release 仅保留最新一版。

## 项目与下载

| 项目 | 用途 | 源码 | 成品形式 | 给人 / 给 Agent | 下载 |
| --- | --- | --- | --- | --- | --- |
| [岛仔 Daozai](daozai/README.md) | Windows 顶部信息岛 | [Rust 应用源码](daozai/src/) | Windows 安装器 | [安装与验证](daozai/INSTALL.md) | [Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/daozai-v0.6.50-r4) |
| [三资产定投计算器](dca-calculator/README.md) | 三资产定投权重计算 | [前后端源码](dca-calculator/) | 网页启动包（前端已构建） | [安装与验证](dca-calculator/INSTALL.md) | [Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/dca-calculator-v1.0.0-r1) |
| [飞鼠格式](flyingmouse-format/README.md) | 离线文件格式转换 | [应用源码](flyingmouse-format/) | 官方安装器联网安装入口 | [安装与验证](flyingmouse-format/INSTALL.md) | [Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/flyingmouse-format-v0.8.3-r1) |
| [毕业论文工作流](graduation-thesis-workflow/README.md) | 论文研究、写作与交付工作流 | [技能与脚本](graduation-thesis-workflow/) | Codex / Claude Code / Pi / WorkBuddy 技能包 | [安装与验证](graduation-thesis-workflow/INSTALL.md) | [Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/graduation-thesis-workflow-v0.4.0-r1) |
| [LibreTV](libretv/README.md) | 视频聚合搜索与播放 | [应用源码](libretv/source/) | 网页生产运行包 | [安装与验证](libretv/INSTALL.md) | [Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/libretv-v2.21.1-r2) |
| [Pi 任务通知](pi-task-notify/README.md) | Pi 完成、出错与等待通知 | [扩展源码](pi-task-notify/extensions/) | Pi 宿主扩展包 | [安装与验证](pi-task-notify/INSTALL.md) | [Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/pi-task-notify-v0.2.0-r1) |
| [REA](rea/README.md) | Agent 逆向分析工具入口 | [准备脚本与上游锁](rea/) | 固定版本 CLI 联网准备包 | [安装与验证](rea/INSTALL.md) | [Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/rea-v6.8.0-r2) |
| [今日待办](today-todo/README.md) | 电脑与手机共用待办清单 | [应用源码](today-todo/) | 零依赖 Node 网页启动包 | [安装与验证](today-todo/INSTALL.md) | [Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/today-todo-v1.0.0-r1) |
| [Windows-MCP](windows-mcp/README.md) | Agent 的 Windows 桌面与文件操作 | [准备脚本与上游锁](windows-mcp/) | MCP 服务联网准备包 | [安装与验证](windows-mcp/INSTALL.md) | [Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/windows-mcp-v0.8.8-r2) |
| [yt-dlp](yt-dlp/README.md) | 视频与音频下载 | [准备脚本与上游锁](yt-dlp/) | CLI 工具链联网准备包 | [安装与验证](yt-dlp/INSTALL.md) | [Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/yt-dlp-v2026.10.26-r3) |

yt-dlp、Windows-MCP、REA 的本地准备代码与固定上游来源保存在对应目录；完整上游项目按锁定来源取得。其他项目在仓库内保存应用、技能或扩展源码。各项目的 INSTALL.md 都含“给人”和“给 Agent”两部分。

## 直接让 Agent 帮你使用

先选项目，再把下面对应提示词交给有联网、文件和运行能力的 Agent。完整入口见 [INSTALL.md](INSTALL.md)。

**岛仔 Daozai**

```text
安装并使用 https://github.com/strive822/zyd-vibe-lab 里的 daozai。先读取该项目 INSTALL.md，从固定 Release 下载对应成品并校验，按项目类型安装或启动；保留已有数据与配置。日常使用不克隆开发仓库、不重新构建前端；只下载时不安装或启动。
```

**三资产定投计算器**

```text
安装并使用 https://github.com/strive822/zyd-vibe-lab 里的 dca-calculator。先读取该项目 INSTALL.md，从固定 Release 下载对应成品并校验，按项目类型安装或启动；保留已有数据与配置。日常使用不克隆开发仓库、不重新构建前端；只下载时不安装或启动。
```

**飞鼠格式**

```text
安装并使用 https://github.com/strive822/zyd-vibe-lab 里的 flyingmouse-format。先读取该项目 INSTALL.md，从固定 Release 下载对应成品并校验，按项目类型安装或启动；保留已有数据与配置。日常使用不克隆开发仓库、不重新构建前端；只下载时不安装或启动。
```

**毕业论文工作流**

```text
安装并使用 https://github.com/strive822/zyd-vibe-lab 里的 graduation-thesis-workflow。先读取该项目 INSTALL.md，从固定 Release 下载对应成品并校验，按项目类型安装或启动；保留已有数据与配置。日常使用不克隆开发仓库、不重新构建前端；只下载时不安装或启动。
```

**LibreTV**

```text
安装并使用 https://github.com/strive822/zyd-vibe-lab 里的 libretv。先读取该项目 INSTALL.md，从固定 Release 下载对应成品并校验，按项目类型安装或启动；保留已有数据与配置。日常使用不克隆开发仓库、不重新构建前端；只下载时不安装或启动。
```

**Pi 任务通知**

```text
安装并使用 https://github.com/strive822/zyd-vibe-lab 里的 pi-task-notify。先读取该项目 INSTALL.md，从固定 Release 下载对应成品并校验，按项目类型安装或启动；保留已有数据与配置。日常使用不克隆开发仓库、不重新构建前端；只下载时不安装或启动。
```

**REA**

```text
安装并使用 https://github.com/strive822/zyd-vibe-lab 里的 rea。先读取该项目 INSTALL.md，从固定 Release 下载对应成品并校验，按项目类型安装或启动；保留已有数据与配置。日常使用不克隆开发仓库、不重新构建前端；只下载时不安装或启动。
```

**今日待办**

```text
安装并使用 https://github.com/strive822/zyd-vibe-lab 里的 today-todo。先读取该项目 INSTALL.md，从固定 Release 下载对应成品并校验，按项目类型安装或启动；保留已有数据与配置。日常使用不克隆开发仓库、不重新构建前端；只下载时不安装或启动。
```

**Windows-MCP**

```text
安装并使用 https://github.com/strive822/zyd-vibe-lab 里的 windows-mcp。先读取该项目 INSTALL.md，从固定 Release 下载对应成品并校验，按项目类型安装或启动；保留已有数据与配置。日常使用不克隆开发仓库、不重新构建前端；只下载时不安装或启动。
```

**yt-dlp**

```text
安装并使用 https://github.com/strive822/zyd-vibe-lab 里的 yt-dlp。先读取该项目 INSTALL.md，从固定 Release 下载对应成品并校验，按项目类型安装或启动；保留已有数据与配置。日常使用不克隆开发仓库、不重新构建前端；只下载时不安装或启动。
```

## 开发与维护

开发才需要取得源码。机器可读的固定版本、附件大小和 SHA-256 见 [releases.json](releases.json)。有仓库副本的 Agent 可运行 `python scripts/get_release.py --project <项目名> --destination <仓库外的新下载目录>`；输出 JSON，下载并核验，不安装或启动。

`python scripts/agent_entry_policy.py`、`python -m unittest discover -s scripts/tests -v`、`python scripts/check_repository.py` 是根检查。打包命令与发布顺序见 [交付规范](docs/AGENT_DELIVERY_STANDARD.md)。构建缓存和下载的程序不进 Git。

计算器只做计算，不执行交易。论文工作流不保证毕业或检测分数。第三方内容保持原许可证与署名，具体来源见各项目 THIRD_PARTY / LICENSE。

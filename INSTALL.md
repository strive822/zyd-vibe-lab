# 安装与使用入口

## 给人：自己动手的步骤

在下面选择项目，打开它的 INSTALL.md。下载固定 Release 的程序或技能包，核验后按项目说明启动。CodeGraph 使用上游的 `SHA256SUMS`，其他项目使用本仓库 Release 的 `SHA256SUMS.txt`。成品可直接使用，无需克隆仓库。

| 项目 | 交付形式 | 说明 | 下载 |
| --- | --- | --- | --- |
| [agent-desktop](agent-desktop/README.md) | Windows x64 CLI 和 MCP 便携包 | [安装与验证](agent-desktop/INSTALL.md) | [Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/agent-desktop-v1.3.1-r1) |
| [CodeGraph](codegraph/README.md) | 官方 Windows CLI 和 MCP 便携包 | [安装与验证](codegraph/INSTALL.md) | [上游 Release](https://github.com/colbymchenry/codegraph/releases/tag/v1.6.3) |
| [岛仔 Daozai](daozai/README.md) | Windows 安装器 | [安装与验证](daozai/INSTALL.md) | [Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/daozai-v0.6.66-r4) |
| [三资产定投计算器](dca-calculator/README.md) | 网页启动包（前端已构建） | [安装与验证](dca-calculator/INSTALL.md) | [Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/dca-calculator-v1.0.0-r2) |
| [飞鼠格式](flyingmouse-format/README.md) | 官方安装器联网安装入口 | [安装与验证](flyingmouse-format/INSTALL.md) | [Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/flyingmouse-format-v0.8.3-r1) |
| [毕业论文工作流](graduation-thesis-workflow/README.md) | Codex / Claude Code / Pi / WorkBuddy 技能包 | [安装与验证](graduation-thesis-workflow/INSTALL.md) | [Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/graduation-thesis-workflow-v0.5.0-r1) |
| [LibreTV](libretv/README.md) | 网页生产运行包 | [安装与验证](libretv/INSTALL.md) | [Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/libretv-v2.24.0-r2) |
| [Pi 任务通知](pi-task-notify/README.md) | Pi 宿主扩展包 | [安装与验证](pi-task-notify/INSTALL.md) | [Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/pi-task-notify-v0.2.0-r1) |
| [REA](rea/README.md) | 固定版本 CLI 联网准备包 | [安装与验证](rea/INSTALL.md) | [Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/rea-v6.10.1-r1) |
| [今日待办](today-todo/README.md) | 零依赖 Node 网页启动包 | [安装与验证](today-todo/INSTALL.md) | [Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/today-todo-v1.0.0-r1) |
| [Windows-MCP](windows-mcp/README.md) | MCP 服务联网准备包 | [安装与验证](windows-mcp/INSTALL.md) | [Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/windows-mcp-v0.9.0-r1) |
| [yt-dlp](yt-dlp/README.md) | CLI 工具链联网准备包 | [安装与验证](yt-dlp/INSTALL.md) | [Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/yt-dlp-v2026.11.23-r1) |

Windows 在下载目录运行 `Get-FileHash -Algorithm SHA256 .\下载的文件名`，与同一 Release 的校验清单比对。macOS/Linux 可用 `shasum -a 256`。ZIP 解压到新目录，已有数据留在原处。

## 给 Agent：交给 AI 执行

```text
请用 https://github.com/strive822/zyd-vibe-lab 的 <项目名> 完成 <我的任务>。先读仓库根 INSTALL.md 和该项目的 INSTALL.md，按你能访问的设备和工具选择下面的入口。优先检查与复用已有安装。需要下载时，从固定 Release 获取成品并校验。按我要求完成下载、试用、安装或实际任务，保留原数据与配置，分别报告实际验证结果。遇到设备或权限限制时，告诉我最少需要在本机完成哪一步。
```

先确定项目、运行设备、已有安装与本次请求范围。能用文件、命令或现有浏览器直接完成的步骤优先走现有入口。需要配置宿主或安装运行环境时，按授权和项目说明执行。

## 按 Agent 能力选择入口

| Agent 能使用的能力 | 怎么开始 |
| --- | --- |
| 本机终端 | 用现有 CLI、启动器或脚本。配置工具时用实际的绝对路径。已有仓库副本可用根下载器处理本仓库 Release，命令见下方。 |
| 本机 MCP | 在该客户端有本地 stdio 能力且已获授权时，使用项目的命令与参数。实际调用一次只读工具来验证。 |
| 本机浏览器或桌面 | 在程序所在设备上打开实际监听地址或应用。能调用 HTTP 时用已公开的只读接口核对服务。 |
| 可读文件，支持或不支持技能导入 | 能原生加载时使用完整技能文件夹。否则直接让 Agent 读取解压后的 `SKILL.md` 和它引用的文件，按该流程开展任务。 |
| 云端或纯对话 | 先核对云端能否到达实际设备或服务。无法访问本机时，可以核对公开资料、给出本机步骤并解读用户提供的非敏感输出。本机接入由有权限的设备完成。 |

### 12 个项目的入口与首次验证

| 项目 | 使用入口 | 首次验证 |
| --- | --- | --- |
| [agent-desktop](agent-desktop/INSTALL.md) | Windows CLI 用 `agent-desktop.exe`。支持本机 stdio 的宿主可用同一可执行文件，参数为 `mcp`。 | `--version` 与只读 `list-windows`。宿主接入后可用 `desktop_list_windows`。 |
| [CodeGraph](codegraph/INSTALL.md) | CLI 查询已建索引项目，或按安装说明用 `serve --mcp` 作为本机 stdio 服务。 | `codegraph --version`，再在已建索引项目实际查询一次。建索引按授权执行。 |
| [岛仔](daozai/INSTALL.md) | 在 Windows 上从开始菜单或快捷方式启动。通过有桌面权限的 Agent 或由用户在界面操作。 | 对照个人版 EXE 校验值与安装路径，确认单一实例和顶部信息岛。 |
| [三资产定投计算器](dca-calculator/INSTALL.md) | 在运行设备用 `start.cmd`，从浏览器访问 `http://127.0.0.1:8000`。 | 首页可访问且 `GET /api/health` 返回 `status: ok`。使用计算功能时另核对实际行情结果。 |
| [飞鼠格式](flyingmouse-format/INSTALL.md) | 用 Windows 应用界面或直接用安装版 `FlyingMouse Format.exe --cli`。有技能入口时也可在应用内选择“接入 Agent”。 | 用安装路径运行 `--cli capabilities --json`，或在隔离目录转换合成文件。 |
| [毕业论文工作流](graduation-thesis-workflow/INSTALL.md) | 有专用包就按宿主方式导入。其他可读文件的 Agent 可使用链接中的通用读取方式，从 `graduation-thesis/SKILL.md` 进入。 | 开始或续用独立论文目录，核对已有状态。缺学校资料或证据时保留草稿与待补事项。 |
| [LibreTV](libretv/INSTALL.md) | 在运行设备用 `start.cmd`，再打开 `http://127.0.0.1:8080`。 | `GET /api/status` 核对版本与访问要求。实际播放用用户授权的视频来源另验。 |
| [Pi 任务通知](pi-task-notify/INSTALL.md) | 交给任一可用 Agent 准备包，通知扩展在 Pi 中用 `pi -e` 临时试用。 | 在 Pi 中运行 `/notify-test` 并查看系统通知。其他客户端可以协助安装和诊断。 |
| [REA](rea/INSTALL.md) | `prepare.cmd` 核验、准备固定的 npm 包。具备终端的 Agent 按项目说明用 CLI。 | 固定版本的 `--help` 正常。分析引擎、`setup` 和宿主接入各自验证。 |
| [今日待办](today-todo/INSTALL.md) | `start.bat` 后用终端显示的地址打开页面。实际读取待办会触发应用正常的过期清理。 | 只检查服务是否可用时调用 `GET /api/health`。页面、写入及重启验证用隔离数据，手机接通单独实测。 |
| [Windows-MCP](windows-mcp/INSTALL.md) | 在 Windows 上完成 `prepare.cmd` 和 `app/install.cmd`，把 `app/start.cmd` 作为本机 stdio 入口。 | 目标宿主发现服务后，在获授权的会话实际调用 `Screenshot` 或 `Snapshot`。仅有网页能力时由 Windows 端接入。 |
| [yt-dlp](yt-dlp/INSTALL.md) | `prepare.cmd` 后从 `app/` 运行 `yt-dlp.exe`，终端型 Agent 可用同样的命令。 | 先查 `--version`，按需针对有权处理的链接列格式。实际下载由用户要求决定。 |

## Agent 的执行顺序

1. 读取项目 INSTALL.md。使用 [releases.json](releases.json) 中的固定 tag 和附件。CodeGraph 使用 [项目上游锁](codegraph/upstream.json) 中的官方成品。对已在运行或安装的项目先核对版本和真实路径。
2. 下载到仓库外的新目录，核对大小和 SHA-256；已有同名不同内容文件不覆盖。仅下载不会安装或启动。
3. 执行该项目的安装/启动入口。联网准备包会按其 assets.json 下载固定官方运行时或工具，并再次校验；不是离线全量包。
4. 分别验证文件、进程/页面和宿主接入；不能凭文件存在声称已安装、凭单元测试声称真实账号或手机已接通。
5. 保留用户数据。MCP 注册、REA setup 和扩展持久接入按本次授权执行。验证用独立目录、合成数据或只读调用，完成后报告运行位置、实际结果和仍需用户操作的步骤。

已有仓库副本且能运行 Python 时，可执行 `python scripts/get_release.py --project <项目目录名> --destination <仓库外的新目录>`。该工具下载并验证本仓库固定 Release，输出 JSON。CodeGraph 的官方包按其上游锁下载。

## 开发源码

只有阅读、修改、测试和重新发布才需要 Git 源码。各目录 AGENTS.md 给出开发验证命令；构建与下载目录放在 `~/.codex/.tmp/<任务名>/`，不要把 node_modules、target、虚拟环境或成品提交到仓库。

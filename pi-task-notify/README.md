# pi-task-notify

当 Pi 编码代理停下来需要你时，发送 Windows / macOS / Linux 系统通知：任务完成、任务出错、等待确认、长任务心跳。三档通知模式随你选：总是通知、失焦才打扰（默认）、完全关闭，用 `/notify` 一键切换。

## 直接让 Agent 帮你使用

把下面这段话复制给具备联网、文件读写和运行能力的 Agent。先阅读本项目 [INSTALL.md](INSTALL.md)，再安装与验证。

```text
安装并使用 https://github.com/strive822/zyd-vibe-lab 里的 pi-task-notify。先读取该项目 INSTALL.md，从固定 Release 下载对应成品并校验，按项目类型安装或启动；保留已有数据与配置。日常使用不克隆开发仓库、不重新构建前端；只下载时不安装或启动。
```

安装与验证的完整步骤见 [INSTALL.md](INSTALL.md)。

## 成品下载

[固定 Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/pi-task-notify-v0.2.0-r1)：Pi 宿主扩展包，附 SHA256SUMS.txt。完整步骤见 [INSTALL.md](INSTALL.md)。仓库内保留源码，不保存构建包或依赖缓存。

## 功能

| 场景 | 通知 | 声音 |
| --- | --- | --- |
| 任务正常完成 | `✅ 任务完成`（含运行时长） | 默认音 |
| 任务出错结束 | `❌ 任务出错`（含错误摘要，≤100 字符） | 提醒音（更急促） |
| Pi 弹确认框/提问等你操作 | `❓ 等你确认` | 默认音 |
| 长任务心跳（默认每 10 分钟） | `⏳ 还在跑`（含已运行时长） | 默认音 |

刻意**不通知**的情况：

- Esc 中止任务——按 Esc 时你一定在屏幕前
- 你自己打开的对话框（如 `/notify` 的选择菜单）——敲命令时你一定在屏幕前
- 单个工具执行失败、API 自动重试——Pi 会自愈，每次都弹是骚扰
- pi-subagents 子代理会话——只让父会话报告，否则并行子代理会连环刷屏

## 通知模式

在 Pi 里运行 `/notify`，三档任选，选择写入配置文件、立即生效；也可以直接编辑 `~/.pi/agent/pi-task-notify.json` 的 `mode` 字段。

| 模式 | 行为 |
| --- | --- |
| `always` 总是通知 | 不管 Pi 终端在不在前台，都弹通知 |
| `focus` 失焦才通知（默认） | 只有 Pi 所在终端**不在前台**时才通知 |
| `off` 关闭 | 完全静默，任何通知都不发，`/notify-test` 会提示已关闭 |

失焦检测尽力而为：Windows 比对前台窗口 PID 与进程祖先链，macOS 比对前台应用。检测失败时回退为通知，宁可多发不错过。Linux 无可靠检测方案，`focus` 档在其上等同于 `always`。

旧版配置字段仍然识别：`focusAware: false` 等价于 `mode: "always"`，`enabled: false` 等价于 `mode: "off"`；显式 `mode` 优先于 `focusAware`。

同一项目的新通知会替换旧通知，不会叠满屏幕；不同项目的 Pi 互不覆盖。

## 跨平台能力矩阵

| 能力 | Windows | macOS | Linux |
| --- | --- | --- | --- |
| 通知渠道 | 系统 Toast（PowerShell WinRT） | 通知中心（osascript） | notify-send |
| 分级音效 | ✅（默认音 / Reminder 提醒音） | ✅（默认音 / Sosumi） | 依桌面环境 |
| 三档通知模式 | ✅ | ✅ | ✅（`focus` 档等同于 `always`） |

> Windows 为主要开发与实测平台。macOS / Linux 路径未经实机验证，如遇问题请提 issue。

## 安装

从 GitHub Release 下载（推荐）：

1. 打开 <https://github.com/strive822/zyd-vibe-lab/releases/tag/pi-task-notify-v0.2.0>，下载 `pi-task-notify.zip` 与 `SHA256SUMS.txt`
2. 校验：`certutil -hashfile pi-task-notify.zip SHA256`（Windows）或 `shasum -a 256 pi-task-notify.zip`（macOS/Linux），与 `SHA256SUMS.txt` 中的值比对
3. 解压得到 `pi-task-notify/` 目录

试用（只在本次运行加载，不写配置）：

```bash
pi -e ./pi-task-notify
```

确认可用后持久安装（任选其一）：

```bash
pi install ./pi-task-notify
```

或把解压目录的绝对路径加进 `~/.pi/agent/settings.json` 的 `packages` 数组。

也可以克隆仓库直接取源码：

```bash
git clone https://github.com/strive822/zyd-vibe-lab
pi -e ./zyd-vibe-lab/pi-task-notify
```

安装后重启 Pi 即生效。用 `/notify` 切换通知模式，用 `/notify-test` 验证：一键发送 4 条样例通知（不受失焦检测影响），确认 Toast 渲染、音效、通知权限都正常。

## 配置（可选）

配置文件 `~/.pi/agent/pi-task-notify.json`，每次发通知时重新读取，修改后无需 reload。文件缺失或损坏时使用默认值。

```json
{
  "enabled": true,
  "mode": "focus",
  "heartbeatMinutes": 10,
  "errorSummaryLength": 100,
  "notifyOn": {
    "complete": true,
    "error": true,
    "waiting": true,
    "heartbeat": true
  }
}
```

| 字段 | 默认 | 说明 |
| --- | --- | --- |
| `mode` | `"focus"` | 通知模式：`"always"` / `"focus"` / `"off"`，与 `/notify` 等效 |
| `enabled` | `true` | 总开关；`false` 时等同 `mode: "off"`（旧字段，保留兼容） |
| `heartbeatMinutes` | `10` | 心跳间隔（分钟），`0` 关闭心跳 |
| `errorSummaryLength` | `100` | 错误摘要最大长度（字符） |
| `notifyOn.*` | 全 `true` | 按场景开关通知 |

## 工作原理

扩展挂接 Pi 会话事件：`agent_start` 记录起点，`tool_result` 顺带记录最近的报错文本，`turn_end` / `agent_before_settle` 跟踪本次运行结果，`agent_settled`（Pi 完全停止、不再自动重试/压缩/续跑时）发送完成或出错通知，`ui_prompt_start` 在 Pi 等你操作时发送提醒。心跳用会话级定时器实现，`session_shutdown` 时清理。`/notify` 把选择写进同一份配置文件并立即生效。

## License

MIT

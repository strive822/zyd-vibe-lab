# pi-task-notify

当 Pi 编码代理停下来需要你时，发送 Windows / macOS / Linux 系统通知：任务完成、任务出错、等待确认、长任务心跳。人在盯着屏幕时不打扰，切走了才喊你。

## 直接让 Agent 帮你使用

把下面这段话复制给具备联网、文件读写和运行能力的 Agent。先阅读本项目 [INSTALL.md](INSTALL.md)，再安装与验证。

```text
下载并安装 https://github.com/strive822/zyd-vibe-lab 里的 pi-task-notify。请先读取该项目 INSTALL.md，按说明用 pi install npm:pi-task-notify 安装（或下载源码用 pi -e 试用），重启 Pi 后运行 /notify-test 验证 4 条样例通知，并向我报告每一步的真实结果；不要改动我已有的 Pi 配置。
```

安装与验证的完整步骤见 [INSTALL.md](INSTALL.md)。

## 功能

| 场景 | 通知 | 声音 |
| --- | --- | --- |
| 任务正常完成 | `✅ 任务完成`（含运行时长） | 默认音 |
| 任务出错结束 | `❌ 任务出错`（含错误摘要，≤100 字符） | 提醒音（更急促） |
| Pi 弹确认框/提问等你操作 | `❓ 等你确认` | 默认音 |
| 长任务心跳（默认每 10 分钟） | `⏳ 还在跑`（含已运行时长） | 默认音 |

刻意**不通知**的情况：

- Esc 中止任务——按 Esc 时你一定在屏幕前
- 单个工具执行失败、API 自动重试——Pi 会自愈，每次都弹是骚扰
- pi-subagents 子代理会话——只让父会话报告，否则并行子代理会连环刷屏

## 失焦感知

只有当 Pi 所在终端**不在前台**时才通知（Windows 通过前台窗口 PID 与进程祖先链比对；macOS 通过前台应用比对，尽力而为）。检测失败时回退为总是通知。Linux 无可靠检测方案，总是通知。

同一项目的新通知会替换旧通知，不会叠满屏幕；不同项目的 Pi 互不覆盖。

## 跨平台能力矩阵

| 能力 | Windows | macOS | Linux |
| --- | --- | --- | --- |
| 通知渠道 | 系统 Toast（PowerShell WinRT） | 通知中心（osascript） | notify-send |
| 分级音效 | ✅（默认音 / Reminder 提醒音） | ✅（默认音 / Sosumi） | 依桌面环境 |
| 失焦才通知 | ✅ | ✅（尽力而为） | ❌ 总是通知 |

> Windows 为主要开发与实测平台。macOS / Linux 路径未经实机验证，如遇问题请提 issue。

## 安装

```bash
pi install npm:pi-task-notify
```

安装后重启 Pi 即生效。用 `/notify-test` 验证：一键发送 4 条样例通知（不受失焦检测影响），确认 Toast 渲染、音效、通知权限都正常。

也可以先试用而不安装：

```bash
pi -e npm:pi-task-notify
```

## 配置（可选）

配置文件 `~/.pi/agent/pi-task-notify.json`，每次发通知时重新读取，修改后无需 reload。文件缺失或损坏时使用默认值。

```json
{
  "enabled": true,
  "heartbeatMinutes": 10,
  "errorSummaryLength": 100,
  "focusAware": true,
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
| `enabled` | `true` | 总开关 |
| `heartbeatMinutes` | `10` | 心跳间隔（分钟），`0` 关闭心跳 |
| `errorSummaryLength` | `100` | 错误摘要最大长度（字符） |
| `focusAware` | `true` | 失焦才通知（检测失败自动回退为总是通知） |
| `notifyOn.*` | 全 `true` | 按场景开关通知 |


## 工作原理

扩展挂接 Pi 会话事件：`agent_start` 记录起点，`tool_result` 顺带记录最近的报错文本，`turn_end` / `agent_before_settle` 跟踪本次运行结果，`agent_settled`（Pi 完全停止、不再自动重试/压缩/续跑时）发送完成或出错通知，`ui_prompt_start` 在 Pi 等你操作时发送提醒。心跳用会话级定时器实现，`session_shutdown` 时清理。

## License

MIT

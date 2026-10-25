# pi-task-notify 安装与验证

为 Pi 编码代理安装"任务通知"扩展：任务完成、出错、等待确认、长任务心跳时发系统通知。

## 前置条件

- 已安装 [Pi 编码代理](https://pi.dev)（`pi` 命令可用，1.4.0 及以上）
- 操作系统：Windows 10/11（完整体验）、macOS（完整体验，未实机验证）、Linux（基础体验，未实机验证）

## 方式一：从 npm 安装（推荐）

```bash
pi install npm:pi-task-notify
```

## 方式二：下载源码试用（不写入配置）

有 Git 时克隆仓库取 `pi-task-notify/` 子目录，或直接下载
`https://github.com/strive822/zyd-vibe-lab/archive/refs/heads/main.zip` 解压取子目录，然后：

```bash
pi -e ./pi-task-notify
```

`-e` 只在本次运行加载，不修改 `~/.pi/agent/settings.json`。确认可用后再用方式一正式安装。

## 验证安装

1. 重启 Pi（或 `/reload`）
2. 在 Pi 里运行 `/notify-test`
3. 预期：依次弹出 4 条系统通知（✅ 完成 / ❌ 出错 / ❓ 等确认 / ⏳ 心跳），约每秒 1 条，其中"出错"为更急促的提醒音
4. 失焦行为验证：盯着 Pi 终端跑一个小任务（如"只回复 ok"）——完成后不应弹通知；切到别的窗口再跑一次——应弹出 ✅

## 配置

可选。默认零配置可用。如需调整，创建 `~/.pi/agent/pi-task-notify.json`：

```json
{
  "enabled": true,
  "heartbeatMinutes": 10,
  "errorSummaryLength": 100,
  "focusAware": true,
  "notifyOn": { "complete": true, "error": true, "waiting": true, "heartbeat": true }
}
```

字段含义见 [README.md](README.md#配置可选)。每次发通知时重新读取，改完即生效，无需重启。

## 完整性校验（源码方式）

从仓库下载时，可用 Git 自身的对象校验（`git clone` 完整性由 Git 保证）；npm 安装的包内容由 npm registry 校验。如仓库发布档提供 SHA256，下载后用 `certutil -hashfile <文件> SHA256`（Windows）或 `shasum -a 256`（macOS/Linux）比对。

## 权限边界

- 扩展运行在 Pi 进程内，与你授予 Pi 的权限相同
- 它只读取 Pi 会话事件与自身配置文件（`~/.pi/agent/pi-task-notify.json`），不读取会话外的其他文件
- 发通知时会调用系统工具：Windows 调 `powershell.exe`（渲染 Toast 与查询前台窗口），macOS 调 `osascript`，Linux 调 `notify-send`
- 它不联网、不写入会话与项目目录

## 卸载

```bash
pi remove npm:pi-task-notify
```

## 常见问题

- **收不到通知**：检查系统"通知设置"里是否禁用了通知来源（Windows 下来源显示为 `Pi · 项目名`）；检查系统免打扰/焦点助手
- **通知总是弹/从不弹**：失焦检测失败会回退为总是通知；可用 `/notify-test` 区分渠道问题与检测问题
- **改了配置没生效**：确认文件是合法 JSON；扩展在每次通知时重读配置，损坏的文件会静默回退默认值

# pi-task-notify 安装与验证

为 Pi 编码代理安装"任务通知"扩展：任务完成、出错、等待确认、长任务心跳时发系统通知，三档通知模式（总是 / 失焦才 / 关闭）用 `/notify` 切换。

## 前置条件

- 已安装 [Pi 编码代理](https://pi.dev)（`pi` 命令可用，1.4.0 及以上）
- 操作系统：Windows 10/11（完整体验）、macOS（完整体验，未实机验证）、Linux（基础体验，未实机验证）

## 方式一：从 GitHub Release 下载（推荐）

1. 打开 <https://github.com/strive822/zyd-vibe-lab/releases/tag/pi-task-notify-v0.2.0>，下载 `pi-task-notify.zip` 与 `SHA256SUMS.txt`
2. 校验：`certutil -hashfile pi-task-notify.zip SHA256`（Windows）或 `shasum -a 256 pi-task-notify.zip`（macOS/Linux），与 `SHA256SUMS.txt` 中的值比对
3. 解压得到 `pi-task-notify/` 目录

## 方式二：克隆仓库取源码

```bash
git clone https://github.com/strive822/zyd-vibe-lab
# 子目录 zyd-vibe-lab/pi-task-notify/ 即扩展本体
```

也可下载 <https://github.com/strive822/zyd-vibe-lab/archive/refs/heads/main.zip> 解压取子目录。

## 试用与持久安装

试用（只在本次运行加载，不写入配置）：

```bash
pi -e ./pi-task-notify
```

`-e` 只在本次运行加载，不修改 `~/.pi/agent/settings.json`。确认可用后再持久安装（任选其一）：

```bash
pi install ./pi-task-notify
```

或把解压目录的绝对路径加进 `~/.pi/agent/settings.json` 的 `packages` 数组，重启 Pi。

## 验证安装

1. 重启 Pi（或 `/reload`）
2. 在 Pi 里运行 `/notify`，依次切到"总是通知"和"失焦才通知"，确认提示"通知模式已改为……"
3. 在 Pi 里运行 `/notify-test`
4. 预期：依次弹出 4 条系统通知（✅ 完成 / ❌ 出错 / ❓ 等确认 / ⏳ 心跳），约每秒 1 条，其中"出错"为更急促的提醒音
5. 失焦行为验证（"失焦才通知"档下）：盯着 Pi 终端跑一个小任务（如"只回复 ok"）——完成后不应弹通知；切到别的窗口再跑一次——应弹出 ✅；切到"总是通知"档后，盯着终端跑也应弹出 ✅
6. 关闭验证：`/notify` 选"关闭"后跑任意任务，不应有任何通知；`/notify-test` 应提示通知已关闭

## 配置

可选。默认零配置可用。`/notify` 的选择会写入并维护这份文件；也可以手动创建或编辑 `~/.pi/agent/pi-task-notify.json`：

```json
{
  "enabled": true,
  "mode": "focus",
  "heartbeatMinutes": 10,
  "errorSummaryLength": 100,
  "notifyOn": { "complete": true, "error": true, "waiting": true, "heartbeat": true }
}
```

字段含义见 [README.md](README.md#配置可选)。每次发通知时重新读取，改完即生效，无需重启。旧字段 `focusAware` / `enabled: false` 仍被识别，等价关系见 README"通知模式"一节。

## 完整性校验（源码方式）

从仓库下载时，可用 Git 自身的对象校验（`git clone` 完整性由 Git 保证）；从 Release 下载的 ZIP 按"方式一"第 2 步做 SHA256 比对。

## 权限边界

- 扩展运行在 Pi 进程内，与你授予 Pi 的权限相同
- 它只读取 Pi 会话事件与自身配置文件（`~/.pi/agent/pi-task-notify.json`），不读取会话外的其他文件；使用 `/notify` 时会写入这同一份配置文件，不碰其他任何文件
- 发通知时会调用系统工具：Windows 调 `powershell.exe`（渲染 Toast 与查询前台窗口），macOS 调 `osascript`，Linux 调 `notify-send`
- 它不联网、不写入会话与项目目录

## 卸载

```bash
pi remove <安装时的路径>
```

若当初是手工把路径加进 `settings.json` 的 `packages` 数组，删除该行即可；`-e` 试用无需卸载。

## 常见问题

- **收不到通知**：先用 `/notify` 确认当前不是"关闭"档；再检查系统"通知设置"里是否禁用了通知来源（Windows 下来源显示为 `Pi · 项目名`）；检查系统免打扰/焦点助手
- **通知总是弹/从不弹**："失焦才通知"档下检测失败会回退为总是通知；可用 `/notify-test` 区分渠道问题与检测问题
- **改了配置没生效**：确认文件是合法 JSON；扩展在每次通知时重读配置，损坏的文件会静默回退默认值

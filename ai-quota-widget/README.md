# AI 额度悬浮窗（QuotaWidget）

Windows 桌面常驻置顶悬浮小窗，聚合展示多账号 AI 额度：

- **OpenAI Codex**：5 小时窗口 + 周窗口（已用百分比、重置倒计时）
- **智谱 GLM Coding Plan**：5 小时窗口 + 周窗口（**支持多个 API Key**，附加窗口如 MCP 月额度也会显示）
- **DeepSeek**：账户余额

综合了 [glm-quota-monitor](https://github.com/ChenMengfang/glm-quota-monitor)（折叠胶囊、闪烁告警、倒计时）、[CodexUsageBar](https://github.com/luodaoyi/codex-useage-win)（直读 `~/.codex/auth.json` 免装 CLI）、本地 pi `usage-monitor` 扩展（两个额度端点与解析逻辑）三个项目的功能。

## 构建与运行

零依赖：使用系统自带的 .NET Framework 4.x C# 编译器，无需安装任何 SDK。

```bat
cd /d "E:\pi always\1a"
build.bat
bin\QuotaWidget.exe
```

`build.bat` 会先编译主程序，再编译并运行解析单测（全绿才算构建成功）。

## 功能

| 功能 | 说明 |
|---|---|
| 置顶悬浮 | 无边框、始终置顶（每秒重申，防被抢占），按住空白处拖动，位置记忆 |
| 折叠胶囊 | 点击标题栏 `—` 折叠成小圆点（显示最紧急账号的百分比环），再点展开 |
| 按账号隐藏 | 托盘菜单 →「显示账号」勾选控制每个账号是否显示（不显示的也不请求） |
| 刷新 | 默认 300s 自动刷新（可配 60–3600），双击悬浮窗或托盘「立即刷新」手动刷新 |
| 重置倒计时 | 每秒走表，显示距 5h / 周窗口重置的剩余时间 |
| 告警 | 绿 <60% / 黄 60–89% / 红 ≥90%（阈值可配），≥90% 卡片背景闪烁，托盘图标颜色同步 |
| 开机自启 | 托盘菜单勾选，写入 `HKCU\...\CurrentVersion\Run`，无需管理员 |
| 单实例 | 重复启动会唤起已有窗口 |
| Codex 凭据 | 直读 `~/.codex/auth.json`；401 时自动用 refresh_token 刷新并备份回写，无需 codex CLI |

## 配置

首次运行在项目根生成 `config.json` 模板（或 exe 同目录）：

```json
{
  "refreshIntervalSeconds": 300,
  "zaiAuthorization": "raw",
  "warnThreshold": 90,
  "accounts": {
    "codex": { "enabled": true, "visible": true, "name": "OpenAI Codex", "authJsonPath": "" },
    "zhipu": [ { "visible": true, "name": "智谱", "apiKey": "填入 Coding Plan API Key" } ],
    "deepseek": { "enabled": false, "visible": true, "name": "DeepSeek", "apiKey": "" }
  },
  "ui": { "left": -1, "top": -1, "collapsed": false, "opacity": 0.95, "topMost": true }
}
```

- 智谱 Key 在 [bigmodel.cn 控制台](https://open.bigmodel.cn) 获取（`zaiAuthorization` 保持 `raw`；特殊网关可切 `bearer`）
- DeepSeek 开关 `enabled` 后填 Key
- `visible:false` = 启动时不显示该账号
- 改完配置用托盘菜单「重载配置」生效

## 数据源

| 账号 | 端点 | 鉴权 |
|---|---|---|
| Codex | `GET chatgpt.com/backend-api/wham/usage` | auth.json 的 access_token（Bearer）+ chatgpt-account-id |
| 智谱 | `GET open.bigmodel.cn/api/monitor/usage/quota/limit` | `Authorization: <裸Key>` |
| DeepSeek | `GET api.deepseek.com/user/balance` | `Bearer <Key>` |

智谱 429（code 1310/1316/1317）按「已用 100% + 报文内重置时间」兜底显示。

## 隐私与安全

- 所有 Key 仅存本地 `config.json` 与 `~/.codex/auth.json`，不经过任何第三方服务器
- 异常信息只含 HTTP 状态与响应片段，不打印 Key
- 刷新 token 时先写 `auth.json.bak` 备份再回写，失败不会破坏原文件

## 测试

```bat
bin\QuotaTests.exe
```

解析单测覆盖：OpenAI 窗口解析与毫秒/秒换算、百分比 clamp、智谱 limits 解析（5h/周/其他窗口）、429 兜底、DeepSeek 余额、auth.json 解析与 id_token 兜底、时长分类、倒计时格式。

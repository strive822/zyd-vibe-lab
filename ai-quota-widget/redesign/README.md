# QuotaWidget · LED Bridge（redesign v2）

> 一块钉在屏幕边缘的调音台电平桥——余光里的 LED 精密仪器。

这是 `1a/src`（v1 经典卡片版）的重设计实现。设计目标从「一个额度面板」改为「一个环境仪器」：默认态面积压到 **22px 高**的一根细桥，余光 0.5 秒可读，需要细节时点击展开，3 秒无操作自动收回。

## 构建与运行

```bat
cd /d "E:\pi always\1a\redesign"
build.bat
bin\QuotaWidget.exe
```

零依赖：使用系统自带 .NET Framework 4.x csc.exe 编译；build.bat 会先编译主程序、再编译并运行解析单测（全绿才算构建成功）。

## 三态

| 态 | 面积 | 内容 | 切换 |
|---|---|---|---|
| **LINE** | 高 12px | 底部一条状态色线（颜色=最紧急账号），几乎不存在 | 菜单「收成一线」；点击回到桥 |
| **BRIDGE**（默认） | 高 22px | 每账号一个通道：状态点 + 缩写 + 双 LED 电平条（上 5h / 下 周）+ 最紧百分比 | 点击展开面板；按住拖动 |
| **EXPANDED** | ≈352×230px | 全称 / 5H / 周 / 百分比 / 重置倒计时 / 错误态 / footer（上次刷新·每 5s） | 点击任意处收起；3 秒无操作自动收回 |

## 视觉语言

- **LED 电平条**：10 段量化额度，段色由该段上界决定（1-5 绿、6-8 黄、9-10 红）——段色即阈值语义，无需图例
- **颜色只承担功能**：三色=阈值；灰色=次要/过期；底部近黑 #101114 是 LED 的暗室
- **动效仅两处**：高度 150ms ease-out（层级变化）、≥90% 告警呼吸（状态）；**数据更新零动画**——LED 是即时量化的，渐变是撒谎
- **Typography**：Consolas 等宽数字（桥上缩写/百分比）、Microsoft YaHei UI 中文；层级靠灰度与字重，不靠加大字号
- **无卡片套卡片、无图标、无 badge**：分隔只用 1px 线，容器只有窗口本身

## 功能

- **每 5 秒自动刷新**（可在 config.json 调 5–3600s），双通道互不阻塞，失败保留旧数据并标「数据过期」
- Codex 直读 `~/.codex/auth.json`（401 自动 refresh token，原子回写+备份），无需 codex CLI
- 智谱支持多 API Key（`accounts.zhipu` 数组），每个 Key 一个通道
- 按账号隐藏：托盘 →「显示账号」勾选（隐藏的账号不刷新）
- ≥90% 呼吸告警 + 托盘图标颜色同步 + LINE 线色同步
- 托盘：立即刷新 / 收成一线 / 置顶 / 透明度 / 开机自启 / 打开配置 / 重载配置 / 退出
- 单实例；二次启动唤起已有窗口；位置记忆；右缘锚定 + 底缘钳制

## config.json

```json
{
  "refreshIntervalSeconds": 5,
  "zaiAuthorization": "raw",
  "warnThreshold": 90,
  "accounts": {
    "codex": { "enabled": true, "visible": true, "name": "OpenAI Codex", "authJsonPath": "" },
    "zhipu": [ { "visible": true, "name": "智谱", "apiKey": "填入 Coding Plan Key" } ],
    "deepseek": { "enabled": false, "visible": true, "name": "DeepSeek", "apiKey": "" }
  },
  "ui": {
    "left": -1, "top": -1, "opacity": 0.95, "topMost": true,
    "mode": "bridge",
    "autoCollapseSeconds": 3
  }
}
```

## 测试

```bat
bin\QuotaTests.exe
```

解析单测 42 条断言：OpenAI 窗口解析与毫秒/秒换算、百分比 clamp、智谱 limits 解析（5h/周/其他窗口+去重）、429 兜底、DeepSeek 余额、auth.json 解析与 id_token 兜底、时长分类、倒计时格式。

## 隐私

API Key 仅存本地 `config.json` 与 `~/.codex/auth.json`；无日志、无遥测；token 回写前先写 `.bak` 备份。

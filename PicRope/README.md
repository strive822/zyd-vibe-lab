# PicRope · 图绳（个人增强版）

把截图挂在屏幕上沿的 Windows 小工具。上游项目是 [Renly1994/PicRope](https://github.com/Renly1994/PicRope)（v1.2.2，MIT），本目录是本地增强版：补齐了截图入口、扩大了能挂上的内容、把绳子改成“悬浮挂钩才展开”，并新增模型额度面板。

Windows 10/11 · 免费开源 · 中文界面 · 图片本地处理。

## 直接让 Agent 帮你使用

把下面这句话发给具备联网、文件读写和运行能力的 Agent：

```text
下载并安装 https://github.com/strive822/zyd-vibe-lab 里的 PicRope。请先读取 PicRope/INSTALL.md，取得完整独立目录并核验，确认 .NET Framework 4.8 环境，按官方 install.ps1 流程安装到 %LocalAppData%\Programs\PicRope，迁移已有 data 数据，验证程序可启动；不要覆盖用户已有的截图与设置。
```

## 下载

| 文件 | 用途 |
| --- | --- |
| [delivery/PicRope-installer.zip](delivery/PicRope-installer.zip) | 免编译的安装包（`app/` + `install.ps1` + `Install.cmd`） |
| [delivery/INSTALLER-SHA256.txt](delivery/INSTALLER-SHA256.txt) | 安装包的 SHA-256 |
| [delivery/PicRope.zip](delivery/PicRope.zip) | 源码快照，供自己构建或改代码 |

两个包用途不同：装软件用安装包，改代码用源码包。详见 [INSTALL.md](INSTALL.md)。

## 和上游的差别

- **三种截图入口**：托盘菜单分“矩形截图 / 窗口截图 / 全屏截图”。矩形是拖拽框选，窗口是点击窗口整窗截取，全屏一键拍整屏。
- **四个快捷键都能改**：统一截图、矩形、窗口、全屏各自一组组合键，可在“截图快捷键…”里修改，不用的可以禁用，避免和系统或其他软件冲突。
- **剪贴板能挂更多**：复制文件会挂上带图标的文件卡片（单击复制文件，右键打开/复制/取下）；开启“文字”收集后，复制文字会进入文字信封，同时在绳子上挂一张摘要卡片（单击复制全文）。文字收集默认关闭，在托盘面板里打开“文字”开关即可。
- **悬浮挂钩才展开**：屏幕顶端中央常驻一个小木夹，只有鼠标悬浮到它上面，绳子才展开；移开就收起。不再整条顶边误触发。
- **额度面板跟着绳子来**：绳子展开时，额度面板自动在绳子下沿、屏幕右侧浮出；绳子收起时一起隐藏。托盘“更多 → 额度面板跟随绳子”可关闭这一行为，“更多 → 模型额度”可单独手动打开/关闭。
- **绳子上的图片可以调顺序**：在绳子上水平拖动图片卡片到新位置，顺序写入 `data/state.json`，重启后保持。
- **图片篮子可移动**：拖动篮子标题栏即可换位置；篮子里的图片卡片改成和绳子一致的视觉（白底、圆角 12、柔和投影）。
- **模型额度面板**：托盘“更多 → 模型额度”手动打开（也可 `PicRope.exe --quota` 直接打开），或由“额度面板跟随绳子”设置随绳子展开自动浮出。显示 Codex（5 小时窗口与每周额度）、智谱 GLM Coding Plan（5 小时与每周用量）、DeepSeek（账户余额），WorkBuddy 暂无公开接口，面板里说明并给出打开应用的入口。Key 写在 `data/quotas.json`，面板每 5 分钟刷新一次，可在配置里改。

## 数据与配置

| 内容 | 位置 |
| --- | --- |
| 程序 | `%LocalAppData%\Programs\PicRope` |
| 状态与截图 | 安装目录下 `data\`（`state.json`、`Captures\`） |
| 额度面板配置 | `data\quotas.json`（首次打开面板时自动生成模板） |
| 错误日志 | `data\error.log` |

`data/` 保存的是个人截图与密钥，不进本仓库，也不要上传。

## 快捷键默认值

| 功能 | 默认 |
| --- | --- |
| 统一截图（点击窗口或拖拽） | `Ctrl+Alt+S` |
| 矩形截图 | 未设置 |
| 窗口截图 | 未设置 |
| 全屏截图 | 未设置 |

## 来源与许可

- 上游：Renly1994/PicRope v1.2.2（MIT），源自 alejandrobujan/tendedero 的 Windows 移植版
- 完整许可见 [LICENSE](LICENSE)，第三方组件声明见 [NOTICE](NOTICE) 与 `third-party-notices/`
- 上游原始说明保留在 [README-upstream.md](README-upstream.md)

本增强版为个人定制，不代表上游项目，也未获上游作者背书。

## 构建与测试

需要 .NET Framework 4.x 的 `csc.exe`（Windows 自带）与 PowerShell 7：

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File build.ps1 -BuildOnly   # 编译
pwsh -NoProfile -ExecutionPolicy Bypass -File build.ps1 -MenuTests   # 桌面交互回归
pwsh -NoProfile -ExecutionPolicy Bypass -File build.ps1              # 核心测试
```

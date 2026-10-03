# 给 Agent：下载并运行 Windows 额度浮窗

用户提示词：

```text
下载并运行 https://github.com/strive822/zyd-vibe-lab 里的 codex-usage。优先下载 Windows x64 便携包，按 INSTALL.md 核对 SHA-256 后完整解压并启动，保留已有数据。
```

## 默认使用便携包

仅适用于 Windows 10/11 x64。先检查实际系统；WSL 的 Linux Python、macOS 和 Linux 无法替代 Windows 凭据、托盘与桌面功能。纯 Linux/macOS 宿主可下载资料或做离线检查，但应报告不能完成 Windows 桌面运行。

从同一仓库版本取得：

```text
https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/codex-usage/packages/usage-0.1.0-windows-x64.zip
https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/codex-usage/packages/SHA256SUMS.txt
```

下载到新目录，用 SHA-256 比对校验文件中对应 ZIP 的值。在 PowerShell 可用 `Get-FileHash -Algorithm SHA256`，Agent 需实际比较值，不只是打印。校验失败停止；不要运行来源不符的文件。

检查 ZIP 条目没有绝对路径、越界和链接后完整解压。当前包包含 `usage-0.1.0-candidate-<hash>/` 顶层目录，在其中运行 `usage.exe`，保留 app、runtime、packages、licenses 和所有随包文件。包已包含 Python / Qt，不要为日常运行另装开发环境。启动失败先读取随包 README 与 SOP；安全提示交给用户本人处理。

启动后检查进程状态与实际桌面可见状态。若无法读取桌面，只报告进程检查通过、界面未验证。重复启动应恢复已有单实例，不结束用户日常实例。默认数据目录 `%USERPROFILE%\.usage`，密钥使用 Windows 凭据管理器；不要自动替换数据、清空配置、输入密钥或开启登录启动。

## 账号与使用

本机 Codex 需要已安装、已登录官方客户端；GLM / DeepSeek 由用户在应用的账户窗口输入密钥。账号未配置时允许运行并显示未配置；不要为了“安装成功”伪造额度。缓存、未知和查询失败应按实际状态报告。操作见 [使用指南](docs/guides/USAGE.md)。

## 需要开发源码时

安全解压完整仓库 ZIP，取整个 `codex-usage/`。按 [README.md](README.md) 和使用指南创建 Windows Python 3.12 开发环境并安装 requirements-dev.txt。入口是 `src/run_app.py`；`launch.cmd` 在新克隆中需要先解压便携包或创建开发环境。

开发环境与官方嵌入 Python 构建缓存不在 Git，不能假定下载后已存在。构建便携包还需使用指南指定的 Windows Python 3.12.10；用户只想运行时使用已有 ZIP。

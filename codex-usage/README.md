# codex-usage

Windows 三平台额度浮窗，支持六位常用复制、更多文本和每日提醒。

## 启动

双击根目录 **launch.cmd**，启动当前便携版。E 盘副本和 GitHub 下载包见 [交付说明](docs/guides/USAGE.md)。源码运行使用 `src/run_app.py`。

## 目录

| 目录 | 内容 |
| --- | --- |
| `src/` | 生产源码、入口和视觉组件 |
| `tools/` | 检查、截图、性能、录屏和构建工具 |
| `tests/` | 自动测试 |
| `docs/` | 规格、设计、使用指南、历史记录和验收证据 |
| `packaging/` | 启动器、随包说明和构建缓存 |
| `dist/` | 当前可运行便携版 |
| `.venv-win/` | 本机 Windows 开发环境（不上传） |

用户数据统一在 `%USERPROFILE%\.usage`；密钥仍使用 Windows 凭据管理器。

## 开发与检查（Windows PowerShell）

```powershell
.\.venv-win\Scripts\python.exe src/run_app.py
.\.venv-win\Scripts\python.exe -m pytest
.\.venv-win\Scripts\python.exe -m mypy
.\.venv-win\Scripts\python.exe -m ruff check src tests
.\.venv-win\Scripts\python.exe tools/check_frozen_composition.py
.\.venv-win\Scripts\python.exe tools/build_portable.py
```

新机器创建环境及完整使用说明见 [使用指南](docs/guides/USAGE.md)。[文档索引](docs/README.md) · [工具索引](tools/README.md) · [清理记录](docs/history/CLEANUP.md)。

## 下载

[Windows x64 便携 ZIP](packages/usage-0.1.0-windows-x64.zip) · [SHA-256](packages/SHA256SUMS.txt)。完整解压后运行包内 `usage.exe`；首次克隆的开发环境按使用指南创建。

![固定测试数据的四边示例](docs/validation/four-edges.png)

真实账户、私人文本和物理桌面录屏仅留本机，不公开。

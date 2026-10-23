# Windows-MCP

## 直接让 Agent 帮你使用

把下面这段话复制给具备联网、文件读写和运行能力的 Agent。
它应先读本项目 [INSTALL.md](INSTALL.md)，完成提示词授权的下载、核验与使用步骤。
只想保存文件时，把“安装/运行”改成“只下载，不安装、不启动”。

```text
下载并准备使用 https://github.com/strive822/zyd-vibe-lab 里的 Windows-MCP。请先读取该项目 INSTALL.md，在新目录恢复固定源码与入口，使用项目内环境安装必要依赖并验证；保留已有配置，注册 MCP 接入前先说明具体改动。
```

本地独立交付包：`delivery/Windows-MCP.zip`，校验文件：`delivery/SHA256SUMS.txt`。
直接下载：[独立项目 ZIP](https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/Windows-MCP/delivery/Windows-MCP.zip) · [SHA-256](https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/Windows-MCP/delivery/SHA256SUMS.txt) · [逐文件清单](https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/Windows-MCP/delivery/FILES.json)。
Agent 可下载独立 ZIP，或取得完整仓库后只使用本项目目录。

独立项目目录，保留原来的固定版本、个人使用配置和下载校验。无须获取其他项目。

- [Agent 下载与恢复](INSTALL.md)
- [来源与许可](THIRD_PARTY.md)
- `profile/`：启动入口、使用说明和许可副本；这是恢复材料，不能当成已安装程序。
- `assets.json`：仅包含本项目所需的固定下载来源、大小与 SHA-256。
- `restore.py`：只恢复本项目，目标必须是新目录。
- `delivery/`：本项目独立交付 ZIP、SHA-256 与逐文件清单，由根目录脚本生成。

# 我的 Windows-MCP 入口

固定 Windows-MCP 0.8.8，Python 3.14.7；独立运行目录，stdio，关闭匿名遥测。恢复脚本准备固定源码和相对路径启动入口。已有全局连接不需要重复安装。

新电脑需要已有 Windows uv，先检查 `uv --version`，然后在恢复目录运行 `install.cmd`。uv 按固定源码的 uv.lock 安装，在本目录管理独立 Python、source/.venv 和 cache，不升级无关软件。`start.cmd` 使用本目录固定解释器，不依赖手动激活环境。

要新增 Agent 连接，先阅读宿主当前官方配置规则，展示将新增的单个服务配置，再按用户授权操作。保留其他 MCP 服务和配置；不要上传整份本机配置或覆盖旧文件。本包不自动注册。启动命令为 `cmd.exe /d /c` 加上恢复目录中的 `start.cmd` Windows 绝对路径；WSL 也必须通过 Windows 进程运行桌面自动化。两个超时均沿用 120 秒。

安装、发现工具和桌面可用性是三个检查。必须在目标聊天真实调用 Screenshot / Snapshot 等工具才可声称已接入；单元测试和旧截图不能替代验收。截图、窗口信息和运行证据仅放本地。

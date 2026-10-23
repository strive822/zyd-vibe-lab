# LibreTV

## 直接让 Agent 帮你使用

把下面这段话复制给具备联网、文件读写和运行能力的 Agent。
它应先读本项目 [INSTALL.md](INSTALL.md)，完成提示词授权的下载、核验与使用步骤。
只想保存文件时，把“安装/运行”改成“只下载，不安装、不启动”。

```text
下载并运行 https://github.com/strive822/zyd-vibe-lab 里的 LibreTV。请先读取该项目 INSTALL.md，取得完整独立目录，核对校验值，在新目录恢复固定版本、个人启动入口与预置源，准备项目内运行时和依赖，启动并验证页面；不要覆盖现有服务。
```

本地独立交付包：`delivery/LibreTV.zip`，校验文件：`delivery/SHA256SUMS.txt`。
直接下载：[独立项目 ZIP](https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/LibreTV/delivery/LibreTV.zip) · [SHA-256](https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/LibreTV/delivery/SHA256SUMS.txt) · [逐文件清单](https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/LibreTV/delivery/FILES.json)。
Agent 可下载独立 ZIP，或取得完整仓库后只使用本项目目录。

独立项目目录，保留原来的固定版本、个人使用配置和下载校验。无须获取其他项目。

- [Agent 下载与恢复](INSTALL.md)
- [来源与许可](THIRD_PARTY.md)
- `profile/`：启动入口、使用说明和许可副本；这是恢复材料，不能当成已安装程序。
- `assets.json`：仅包含本项目所需的固定下载来源、大小与 SHA-256。
- `restore.py`：只恢复本项目，目标必须是新目录。
- `delivery/`：本项目独立交付 ZIP、SHA-256 与逐文件清单，由根目录脚本生成。

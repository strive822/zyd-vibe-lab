# yt-dlp

## 直接让 Agent 帮你使用

把下面这段话复制给具备联网、文件读写和运行能力的 Agent。
它应先读本项目 [INSTALL.md](INSTALL.md)，完成提示词授权的下载、核验与使用步骤。
只想保存文件时，把“安装/运行”改成“只下载，不安装、不启动”。

```text
下载并准备使用 https://github.com/strive822/zyd-vibe-lab 里的 yt-dlp。请先读取该项目 INSTALL.md，取得完整独立目录并核验，在新目录准备 yt-dlp、FFmpeg、Deno 和下载入口，验证版本；不要全局安装，不自动下载视频。
```

本地独立交付包：`delivery/yt-dlp.zip`，校验文件：`delivery/SHA256SUMS.txt`。
直接下载：[独立项目 ZIP](https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/yt-dlp/delivery/yt-dlp.zip) · [SHA-256](https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/yt-dlp/delivery/SHA256SUMS.txt) · [逐文件清单](https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/yt-dlp/delivery/FILES.json)。
Agent 可下载独立 ZIP，或取得完整仓库后只使用本项目目录。

独立项目目录，保留原来的固定版本、个人使用配置和下载校验。无须获取其他项目。

- [Agent 下载与恢复](INSTALL.md)
- [来源与许可](THIRD_PARTY.md)
- `profile/`：启动入口、使用说明和许可副本；这是恢复材料，不能当成已安装程序。
- `assets.json`：仅包含本项目所需的固定下载来源、大小与 SHA-256。
- `restore.py`：只恢复本项目，目标必须是新目录。
- `delivery/`：本项目独立交付 ZIP、SHA-256 与逐文件清单，由根目录脚本生成。

# 我的下载习惯

Windows PowerShell，在恢复后的工具目录：

```powershell
.\download.cmd '视频页面链接'
.\download.cmd -F '视频页面链接'
.\download.cmd -x --audio-format mp3 '视频页面链接'
```

也可以在聊天中发链接给 Agent，说明使用本工具。默认文件夹为工具旁的 `xiazai`，不是仓库内的媒体备份；只下载单条，使用 Windows 文件名。恢复时将实际目标目录写入 UTF-8 BOM 配置，以支持中文路径。

移动已恢复的工具目录后，应在新目录重新恢复，或修改 `yt-dlp.conf` 三项路径。FFmpeg 的 DLL 必须保留。更新版本需重新记录来源和 SHA-256，不能把更新后的 exe 冒充这里固定的版本。真实站点登录、网络和格式支持以具体链接验证；仅获取有权下载的内容。

# 我的下载习惯

Windows PowerShell，在恢复后的工具目录：

```powershell
.\download.cmd '视频页面链接'
.\download.cmd -F '视频页面链接'
.\download.cmd -x --audio-format mp3 '视频页面链接'
```

也可以在聊天中发链接给 Agent，说明使用本工具。默认文件夹为工具旁的 `xiazai`，不是仓库内的媒体备份；只下载单条，使用 Windows 文件名。恢复时将实际目标目录写入 UTF-8 BOM 配置，以支持中文路径。

移动已恢复的工具目录后，应在新目录重新恢复，或修改 `yt-dlp.conf` 三项路径。FFmpeg 的 DLL 必须保留。更新版本需重新记录来源和 SHA-256，不能把更新后的 exe 冒充这里固定的版本。真实站点登录、网络和格式支持以具体链接验证；仅获取有权下载的内容。

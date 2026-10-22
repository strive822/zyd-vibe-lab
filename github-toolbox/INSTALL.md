# 个人工具箱安装入口

先确认用户点名的工具：LibreTV、yt-dlp、Windows-MCP、rea 或 Winhance。取得完整 `github-toolbox` 目录，保留 `packages`、`profiles`、`assets.json` 和 `restore.py`。不是只下载脚本或上游的 README。

## Windows PowerShell

需要 Windows x64、Python 3.11+ 和网络。LibreTV 恢复脚本自动下载独立 Node.js 22.23.2（含 npm）；不会升级机器上的全局 Node。恢复到**尚不存在的新目录**：

```powershell
cd '下载后的仓库\github-toolbox'
python .\restore.py LibreTV --destination 'D:\MyTools\LibreTV'
python .\restore.py yt-dlp --destination 'D:\MyTools\yt-dlp'
python .\restore.py Windows-MCP --destination 'D:\MyTools\Windows-MCP'
python .\restore.py rea --destination 'D:\MyTools\rea'
python .\restore.py Winhance --destination 'D:\MyTools\Winhance'
```

根据需要选择一条。目录已存在会拒绝，避免覆盖数据。失败时保留现场，修正网络或环境后选择新的目标目录；下载缓存 `.downloads` 会按哈希复用。校验失败时停止，不自动改用 latest 或陌生镜像。

LibreTV 完成后双击 `start.vbs`，读取本机生成的 `source/.env.local` 中 PASSWORD 的值登录。将 `start.vbs` 创建为桌面快捷方式即可沿用双击习惯。桌面入口、浏览器操作和服务启动属于后续使用，不在恢复过程自动执行。不要在已有服务占用 8080 时启动第二套。

yt-dlp 完成后运行 `download.cmd '视频页面链接'`。Windows-MCP 继续读它的 [README](profiles/Windows-MCP/README.md)；REA 和 Winhance 恢复仅准备文件，不代表已经接入 Agent、安装引擎或改变系统。

## WSL / Linux

这是 Windows 使用配置。运行安装请使用 Windows Python，不在 Linux 中直接执行 Windows 桌面组件。WSL 若要调用 Windows-MCP，启动命令经过 `cmd.exe /d /c`，具体路径采用恢复后的 Windows 绝对路径。

## 下载完整性与来源

固定版本及哈希见 [assets.json](assets.json)。FFmpeg 原来来自可变的 latest 发布项，本包改用原始资产 ID `663451527` 并保留原 SHA-256；资产被上游删除后需要维护者重新审查，不会静默更新版本。下载缓存可以保留作本机重装使用，不进入 Git。

LibreTV 源码是随仓库交付的完整当前快照，不依赖上游 main 是否变化。外部二进制由原发布者提供，恢复脚本保留解压包附带的许可；没有重新打包发布 FFmpeg、Deno、Node 或 Winhance 的二进制。

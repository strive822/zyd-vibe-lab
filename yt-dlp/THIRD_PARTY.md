# yt-dlp 工具链：来源与许可

- 本仓库维护的准备/恢复脚本采用 [MIT](LICENSE)，Copyright (c) 2026 zhongyudi；这不替代各工具自身的许可证。

- yt-dlp 固定官方稳定版 [2026.11.23](https://github.com/yt-dlp/yt-dlp/releases/tag/2026.11.23)，提交 `6f73a8d1664a58cdef8c25f01ffb5ab9cf730408`，上一稳定基线为 `f264a6cbd1f630894da0f368df00f8aae50140e0`（2026.10.26）。使用官方 yt-dlp.exe，保留解压/分发的许可，不能将含第三方组件的成品统称为 Unlicense。
- Deno 固定官方 v2.9.8。FFmpeg 使用 [2026-11-25 固定快照](https://github.com/yt-dlp/FFmpeg-Builds/releases/tag/autobuild-2026-11-25-23-12)，Windows x64 GPL shared，版本 `N-129306-g35ef294f5d`，GitHub 资产 793509471。上一快照为 `N-128946-g33a5956d8b`。下载地址、字节和 SHA-256 见 assets.json。
- FFmpeg按该发行包GPL条款保留说明、许可证与DLL；Deno/yt-dlp按各自许可保留。下载缓存和工具二进制不进入源码Git。
- 本地修改为下载/命名/单条策略、锁定工具配套和隔离启动配置；保留用户下载目录与凭据，不自动下载媒体或改全局PATH。
- 上游master尚未发布的变更未纳入本次稳定包同步。

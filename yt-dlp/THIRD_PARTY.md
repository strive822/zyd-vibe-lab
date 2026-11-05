# yt-dlp 工具链：来源与许可

- yt-dlp 固定官方稳定版 [2026.10.26](https://github.com/yt-dlp/yt-dlp/releases/tag/2026.10.26)，源码 tag提交 `f264a6cbd1f630894da0f368df00f8aae50140e0`；当前仍是最新稳定发行。使用官方 yt-dlp.exe，保留解压/分发的许可，不能将含第三方组件的成品统称为 Unlicense。
- Deno固定官方v2.9.8；FFmpeg固定yt-dlp/FFmpeg-Builds资产669997580（win64 GPL shared）。URL、字节和SHA-256均见assets.json，不追踪可变的latest下载结果。
- FFmpeg按该发行包GPL条款保留说明、许可证与DLL；Deno/yt-dlp按各自许可保留。下载缓存和工具二进制不进入源码Git。
- 本地修改为下载/命名/单条策略、锁定工具配套和隔离启动配置；保留用户下载目录与凭据，不自动下载媒体或改全局PATH。
- 上游master尚未发布的变更未纳入本次稳定包同步。

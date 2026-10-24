# 来源、许可和修改边界

这是个人使用配置合集。下表描述所用版本的实际声明，不为其他版本作保证。

| 项目 | 来源 / 版本 | 本仓库处理 |
| --- | --- | --- |
| LibreTV | [LibreSpark/LibreTV](https://github.com/LibreSpark/LibreTV/tree/b08c8242d2a3cdb4309b40c58001c69c04593ce1)，package.json 声明 AGPL-3.0-or-later | 完整本地源码与原 LICENSE、README、版权声明一起保留在源码 ZIP；[许可证副本](https://github.com/strive822/zyd-vibe-lab/blob/09c5c90fad491c0ef94714f1c6842a585e04d28a/github-toolbox/profiles/LibreTV/LICENSE)；个人新增部分是外围启动/停止/窗口脚本和部署配置 |
| Windows-MCP | [CursorTouch/Windows-MCP](https://github.com/CursorTouch/Windows-MCP/tree/9170e1b2a2c0153f6a1d629afaab986c26538b93)，MIT | [许可证](https://github.com/strive822/zyd-vibe-lab/blob/09c5c90fad491c0ef94714f1c6842a585e04d28a/github-toolbox/profiles/Windows-MCP/LICENSE.md)；未改动上游源码；使用个人可迁移 cmd 启动入口 |
| REA | [morluto/rea](https://github.com/morluto/rea/tree/933af60eba43c29f1fb1c606fddcd725ae0d9d96)，MIT，rea-agents 6.7.0 | [许可证](profile/LICENSE)；运行包从 npm 固定下载，包中保留 THIRD_PARTY_NOTICES 和 licenses；遵守其 setup 先展示计划并确认、保留证据、只分析授权目标等规则 |
| yt-dlp | [yt-dlp/yt-dlp 2026.10.21](https://github.com/yt-dlp/yt-dlp/releases/tag/2026.10.21) | 原发布者提供 exe；源码与打包 exe 含第三方组件，许可应按上游对应资产核对，不统一改写为本仓库许可 |
| FFmpeg | [yt-dlp/FFmpeg-Builds 资产](https://api.github.com/repos/yt-dlp/FFmpeg-Builds/releases/assets/669997580)，win64 GPL shared | 下载并完整保留解压目录中的许可/说明及 DLL；二进制不在本仓库再分发 |
| Deno | [denoland/deno v2.9.8](https://github.com/denoland/deno/releases/tag/v2.9.8) | 原发布者提供；解压目录保留，不重打包二进制 |
| Node.js | [nodejs.org 24.22.1](https://nodejs.org/dist/v24.22.1/) | 官方 Windows ZIP 完整解压到独立 runtime，保留 LICENSE 和附带第三方声明 |
| Winhance | [memstechtips/Winhance v26.06.12 LICENSE.txt](https://github.com/memstechtips/Winhance/blob/v26.06.12/LICENSE.txt)，PolyForm Shield 1.0.0 | 按原发布者固定 URL 下载；不修改、改名或作为竞争替代软件发布；保留原许可与 Required Notice，未宣称为通用 MIT 开源工具 |

Winhance 原文 Required Notice: Copyright (c) 2025 Marco du Plessis (https://github.com/Jeyloh/Winhance)。许可原文见上表链接，第三方声明见 [上游 THIRD-PARTY-NOTICES.txt](https://github.com/memstechtips/Winhance/blob/v26.06.12/THIRD-PARTY-NOTICES.txt)。

LibreTV 的源码快照可直接下载并解压审查，`libretv-files.json` 对应全部条目。源码包中的上游 GitHub Actions 只是来源材料，不复制为本仓库的镜像发布流程。若后续改网页源码或提供网络服务，应重新核对该版本 AGPL 原文及相应源码提供要求。

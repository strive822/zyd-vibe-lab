# Repository Cleanup Report

日期：2026-10-22。范围：把 GitHub 灵感目录中的 5 个工具整理为可公开、可迁移的个人使用配置，进入本仓库 `github-toolbox`。原目录只读，未删除日常运行文件。

## Deleted

原目录无删除。发布副本不包含依赖、构建缓存、日志、锁文件、密码、Cookie、下载媒体和桌面截图；这些不是可公开源码。LibreTV 的源码 ZIP 是有意交付产物，保留。

## Archived

LibreTV 当前本地完整源码 167 个文件归入 `packages/libretv-source.zip`，逐文件校验见 `packages/libretv-files.json`。原上游许可、文档、测试和依赖锁文件保留。原目录的历史报告与验证材料留在本机。

## Merged

将散落的日常操作说明整理为本合集入口及各 profile 的 README。没有合并独立应用的运行环境，没有将上游源码认作个人原创。

## Git Ignore

合集忽略下载缓存、恢复目录、运行日志、服务锁、构建、下载媒体和证据；仓库原有环境文件/依赖忽略规则继续生效。仅允许公开的 `.env.example` 进入源码包。

`.gitattributes` 为导出的个人运行文件和元数据保留原始字节与 Windows 行尾，避免跨平台 checkout 自动转换破坏逐字节比对。

## Structure Changes

新增 `github-toolbox`，包含个人 profiles、LibreTV 源码包、固定外部资产清单、恢复工具、检查工具和恢复边界测试。没有移动或修改原目录、桌面快捷方式、全局 MCP 配置和正在运行的服务。

## Documentation Updates

同步根 README、INSTALL 和 AGENTS 的项目入口；新增合集安装说明、第三方声明及各工具使用说明。启动脚本与原个人版一致，Windows-MCP 和下载配置将机器专用路径改为恢复目录。

## Validation

- 已通过 7 项恢复边界测试：路径越界、符号链接、大小写冲突、已有文件保护、下载校验、源码完整性、唯一密码与只读导出。
- LibreTV：在独立 Windows 目录通过 `npm ci` 安装 413 个依赖；Type Check、Lint、35 个文件 / 472 项测试和 Next.js 15.5.26 Production Build 全部通过。本轮重新执行，非沿用旧报告。
- LibreTV Runtime / Critical Path：自动选择隔离端口启动新服务，首页、版本、密码必需标志、两项预置源、密码登录和会话验证通过；`.env.local` 请求返回 404；验证后结束本轮创建的进程。未启动原固定 8080 的日常启动器或改动原服务。
- yt-dlp：从固定来源恢复 Deno / FFmpeg；版本执行通过。自制 1 秒媒体经本地 HTTP 下载到默认 `xiazai`，FFmpeg 转为 MP3，ffprobe 读回时长通过；自制媒体随后删除。真实第三方视频链接不属于本轮验收。
- Windows-MCP / REA / Winhance：恢复与 SHA-256 检查通过。Node、FFmpeg、Deno、Windows-MCP 源码是本轮联网获取；yt-dlp exe、REA tgz、Winhance 安装包从原目录拷贝到哈希缓存后重新核验。未触发全局接入、原生引擎安装或系统优化。
- 原个人版 7 个 LibreTV 运行脚本与导出副本逐字节一致；当前真实 PASSWORD 未出现在公开文件或源码 ZIP 中。根仓库检查通过 290 个 Git 可见文件的语法、链接、Secret 模式和交付包检查；`git diff --check` 通过。测试和源包完整性检查加入 CI。
- 复建提示：上游 ESLint / Vite 发出弃用提示；Next.js 提示用户主目录另有 package-lock，推断 workspace root。以上未导致检查或构建失败，没有改动用户主目录文件。
- 原工作区全量检查额外报告未跟踪的 `pi-usage: ValueError`；该目录在本任务开始前已存在，未纳入本次暂存或上传。发布文件单独导出后执行仓库检查，避免把无关未跟踪项目混入验收范围。

## Manual Review

无待确认删除项。原私人密码、媒体和配置继续只在本机保留；全新安装生成独立密码。第三方源可能失效；完整影视播放、真实站点下载、REA 引擎与新机器桌面行为需要实际使用验收。

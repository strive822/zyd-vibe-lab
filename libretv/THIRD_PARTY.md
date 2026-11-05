# LibreTV：来源、许可与个人修改

- 上游 [LibreSpark/LibreTV](https://github.com/LibreSpark/LibreTV/tree/29cbeb3d37b4876f909a0354087a3531af0447f6)，最新稳定版2.21.1，提交 `29cbeb3d37b4876f909a0354087a3531af0447f6`。
- AGPL-3.0-or-later。完整对应业务源码位于 source/，保留 source/LICENSE、原 README 和版权声明；提供修改后的网络服务时遵守对应源码提供要求。
- 保留 package.json/package-lock.json 的个人依赖安全修复，见 SECURITY_PATCHES.md；这些文件不会被上游旧锁覆盖。其余业务源码与固定上游一致，逐文件哈希见 source-files.json。
- 外围 profile/、restore.py 和 runtime/ 保留个人默认源、启动/停止与环境隔离。生产启动器使用已随 Next.js 分发的 @next/env 解析既有配置，兼容引号并保留原文件。
- Node.js24.22.1固定下载来源与校验见 assets.json；Node及运行包内依赖许可独立保留。Git保存源码，生产运行包在Release。
- 本次未纳入上游尚未发布的音量增强功能；当前稳定版业务与个人依赖修复保持不变。

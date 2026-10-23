# 固定上游与本地依赖修复

源码基于 LibreSpark/LibreTV 2.21.0，提交 `b08c8242d2a3cdb4309b40c58001c69c04593ce1`。
本仓库仅修改源码快照中的 package.json 与 package-lock.json；应用源码、原 README 和 AGPL 许可保留上游原文。个人预置源和启动器位于外围 profile/。

2026-10-24 对上游锁文件执行 npm audit，发现 13 项依赖漏洞，其中包含严重项。本次修复：

- Next.js 与 eslint-config-next 升至 15.5.28 系列；Vitest 从 2.1.9 升至 5.0.5。
- PostCSS 固定最低 8.5.28，并对传递依赖使用同一版本范围。
- sharp 固定最低 0.35.5，source-map-js 最低 1.2.2，postcss-selector-parser 最低 7.1.7。
- 在全新环境重新解析并提交完整锁文件，避免沿用旧依赖树；运行时固定为项目内 Node.js 24.22.1 LTS。

验证结果：类型检查、Lint、37 个测试文件 / 542 项测试、生产构建通过；官方 npm registry 全量审计为 0 项漏洞。
包内各文件哈希见 packages/libretv-files.json；完整源码 ZIP 哈希见 assets.json。安装使用 npm ci，不能只替换 package.json 而沿用旧锁文件。

上游依据：[Next.js 修复公告](https://github.com/vercel/next.js/security/advisories/GHSA-2464-fhr4-w9xw)、[Vitest 修复公告](https://github.com/vitest-dev/vitest/security/advisories/GHSA-82fw-gwwq-j7x9)。后续更新应重新审计，不把本次结果视为永久安全保证。

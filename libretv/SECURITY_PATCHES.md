# 固定上游与本地依赖修复

源码基于 LibreSpark/LibreTV 2.21.1，提交 `29cbeb3d37b4876f909a0354087a3531af0447f6`。
本仓库仅修改源码快照中的 package.json 与 package-lock.json；应用源码、原 README 和 AGPL 许可保留上游原文。个人预置源和启动器位于外围 profile/。

2026-11-01 对上游 2.21.1 锁文件执行 npm audit，发现 25 项依赖漏洞，其中 3 项严重。本次修复：

- Next.js 与 eslint-config-next 固定 15.5.28 系列（当前 15.x 最新正式版，含 GHSA-2464-fhr4-w9xw 等严重漏洞修复）。
- Vitest 从 2.1.8 升至 5.0.5，随之解决 vite、esbuild、tinypool 系列漏洞。
- PostCSS 固定最低 8.5.28，并对传递依赖使用同一版本范围（overrides）。
- sharp 固定最低 0.35.5，source-map-js 最低 1.2.2，postcss-selector-parser 最低 7.1.7。
- 在全新环境重新解析并提交完整锁文件，避免沿用旧依赖树；运行时固定为项目内 Node.js 24.22.1 LTS。

验证结果：类型检查、Lint、37 个测试文件 / 542 项测试、生产构建通过；生产依赖审计（`npm audit --omit=dev`）为 0 项漏洞。
展开源码的逐文件哈希见 source-files.json；生产成品的大小和 SHA-256 见仓库根 releases.json。安装使用 npm ci，不能只替换 package.json 而沿用旧锁文件。

## 开发依赖中已知的遗留审计项

2026-10-30 发布的 GHSA-g3hv-75wg-m249（minimatch glob 放大拒绝服务，11.0.1 修复，无旧版回迁）影响 eslint 工具链：
`@eslint/eslintrc`、`@eslint/config-array`、`@typescript-eslint/typescript-estree` 均以默认导入引用 minimatch 且依赖范围固定在 11 以下，
强制升到 11 会让 ESLint 在加载配置时直接崩溃，生态各包尚未跟进。该公告只涉及开发期 lint 工具链（glob 匹配的是仓库自身配置，不接触外部输入），
生产依赖树审计为 0。因此 CI 与本地审计使用 `npm audit --omit=dev` 把关生产依赖；待 eslint 生态发布兼容 minimatch 11 的版本后
重新恢复全量审计，不把本说明视为永久豁免。

上游依据：[Next.js 修复公告](https://github.com/vercel/next.js/security/advisories/GHSA-2464-fhr4-w9xw)、
[Vitest 修复公告](https://github.com/vitest-dev/vitest/security/advisories/GHSA-82fw-gwwq-j7x9)、
[minimatch 公告](https://github.com/advisories/GHSA-g3hv-75wg-m249)。后续更新应重新审计，不把本次结果视为永久安全保证。

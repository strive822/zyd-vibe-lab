# 固定上游与本地依赖修复

## v2.21.1 依赖修复基线（2026-11-01）

当时使用的 LibreSpark/LibreTV 2.21.1 来自提交 `29cbeb3d37b4876f909a0354087a3531af0447f6`。这轮依赖修复涉及 `package.json` 与 `package-lock.json`。

2026-11-01 对上游 2.21.1 锁文件执行 npm audit，发现 25 项依赖漏洞，其中 3 项严重。本次修复：

- Next.js 与 eslint-config-next 更新至当时的 15.5.28，包含 GHSA-2464-fhr4-w9xw 等修复。
- Vitest 从 2.1.8 升至 5.0.5，随之解决 vite、esbuild、tinypool 系列漏洞。
- PostCSS 固定最低 8.5.28，并对传递依赖使用同一版本范围（overrides）。
- sharp 固定最低 0.35.5，source-map-js 最低 1.2.2，postcss-selector-parser 最低 7.1.7。
- 在全新环境重新解析并提交完整锁文件，避免沿用旧依赖树；运行时固定为项目内 Node.js 24.22.1 LTS。

验证结果：类型检查、Lint、37 个测试文件 / 542 项测试、生产构建通过；生产依赖审计（`npm audit --omit=dev`）为 0 项漏洞。
展开源码的逐文件哈希见 source-files.json；生产成品的大小和 SHA-256 见仓库根 releases.json。安装使用 npm ci，不能只替换 package.json 而沿用旧锁文件。

## v2.23.2 隔离验证（2026-11-16）

上游 v2.23.2（92461b5e458ba45233e1cba30b09ce0bbc0fa911）新增 undici，原个人依赖修复及启动器继续保留。复验类型检查、Lint、43 个测试文件 / 642 项测试和 standalone 生产构建，生产依赖审计为 0 项。

## v2.24.0-r2 依赖修复（2026-11-20）

- Next.js 与 eslint-config-next 同步至 15.5.29。Next.js 的 15.5 维护版本修复了本次生产依赖审计中的三条公告。[Next.js 15.5.29 发布说明](https://github.com/vercel/next.js/releases/tag/v15.5.29)
- 锁定的 typescript-eslint 组件更新至 8.73.0，将受影响的开发依赖 minimatch 更新至 11.0.9。ESLint 其余使用的 3.1.5 不在此次公告的影响范围内。[minimatch 安全公告](https://github.com/advisories/GHSA-g3hv-75wg-m249)
- 修复前生产依赖审计报告 1 项、全量审计报告 7 项中危条目。修复后的两种审计均为 0。LibreTV 的 CI 恢复全量审计。

上游依据：[Next.js 修复公告](https://github.com/vercel/next.js/security/advisories/GHSA-2464-fhr4-w9xw)、
[Vitest 修复公告](https://github.com/vitest-dev/vitest/security/advisories/GHSA-82fw-gwwq-j7x9)、
[minimatch 公告](https://github.com/advisories/GHSA-g3hv-75wg-m249)。后续更新应重新审计，不把本次结果视为永久安全保证。

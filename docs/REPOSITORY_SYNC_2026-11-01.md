# 仓库同步、上游更新与交付验收

日期：2026-11-01。检查对象为 `strive822/zyd-vibe-lab` 的全部 8 个独立项目、公开下载包和第三方固定来源。本轮同时移除了 Winhance、codex-usage、codex-bailong-desktop-pet 三个项目（历史记录见 Git 提交 `29f0df8` 之前的日志）。

## 上游版本

| 组件 | 本次固定版本 / 来源 | 处理 |
| --- | --- | --- |
| LibreTV | 2.21.1，`29cbeb3d37b4876f909a0354087a3531af0447f6` | 从 2.21.0 更新；应用源码与上游逐字一致，依赖修复更新见 LibreTV/SECURITY_PATCHES.md；上游锁文件 25 项漏洞（3 严重）已修复，生产依赖审计 0 项 |
| yt-dlp | 2026.10.26 | 从 2026.10.21 更新；官方 exe 与上游 SHA2-256SUMS 核对一致，实机 `--version` 验证 |
| Windows-MCP | 主干 `94b52cfb48076cb793e710351517fa18a316cd12` | 从 `9170e1b`（10-24）推进一周：上游 PowerShell 引号、进程/注册表列表输出、编码修复等 18 个文件变化及 9 个新测试；未发新 release，按主干提交固定 |
| REA | rea-agents 6.8.0 | 从 6.7.0 更新；npm 官方 tarball 以 registry integrity（sha512）与 shasum（sha1）双重核验一致，包内 THIRD_PARTY_NOTICES 与 licenses 完整 |
| Deno / FFmpeg / Node.js | 2.9.8 / 2026-10-23 构建 / 24.22.1 LTS | 与上一轮一致，未变动 |

上游"最新"仅代表本次联网核查时的结果。源码项目按已核实的提交或 tag 固定，二进制按最新正式 Release 固定。

## 已知边界与说明

- LibreTV 开发依赖存在 2026-10-30 新公告 GHSA-g3hv-75wg-m249（minimatch，11.0.1 修复、无旧版回迁）。eslint 生态各包（@eslint/eslintrc、@eslint/config-array、@typescript-eslint/typescript-estree）以默认导入引用 minimatch 且范围固定在 11 以下，强制升级会使 ESLint 无法加载配置；生态跟进前，CI 与本地审计使用 `npm audit --omit=dev` 把关生产依赖（0 项漏洞），详见 LibreTV/SECURITY_PATCHES.md。
- 本地未安装 uv，Windows-MCP 的源码安装流由模拟恢复测试覆盖；全新目录 uv 环境安装待具备条件时按 INSTALL.md 验收。
- yt-dlp / LibreTV / Windows-MCP / rea 四个项目的同构 THIRD_PARTY.md 历史副本仍互相罗列旧工具箱条目（如 rea 声明内含 LibreTV 行），属遗留文档，未在本轮处理。

## 验证范围

- `python scripts/check_repository.py`：221 个 Git 可见文件的格式、语法、本地链接、敏感模式与全部交付包校验通过。
- `python scripts/agent_entry_policy.py`：全部项目 Agent 入口完整。
- `python -m unittest discover -s scripts/tests`：10 项打包/恢复边界测试通过。
- `python scripts/verify_published.py --ref <推送提交>`：推送后从 GitHub 实际下载全部交付包核验。
- LibreTV 在临时目录用项目内 Node.js 24.22.1 执行：npm ci、类型检查、Lint、542 项测试、生产构建、生产依赖审计全部通过；交付包由当前打包器重建并逐文件核验。
- yt-dlp 2026.10.26 exe 实机运行验证版本输出；rea 6.8.0 tarball 与 npm registry integrity 双重核验；Windows-MCP 源码 ZIP 与 codeload 字节一致。
- 不访问真实账号、密钥、现用服务；真实站点播放与账号额度仍按设备实际情况另行验收。

## 验收后的清理

临时下载（yt-dlp exe、rea tarball、上游源码 ZIP、Node.js 运行时）存放于 `.tmp/upstream-sync-2026-11-01/`，该目录已加入 `.gitignore`；验收完成后整目录删除，交付状态以 Git 工作区与公开下载验证为准。

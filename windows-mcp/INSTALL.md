# Windows-MCP：安装与验证

## 给人：自己动手的步骤

1. 打开 [固定 Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/windows-mcp-v0.8.8-r1)，下载 `windows-mcp-windows.zip` 和 `SHA256SUMS.txt`。
2. 在下载目录执行 `Get-FileHash -Algorithm SHA256 .\windows-mcp-windows.zip`，与校验文件逐项比对；不匹配则停止。
3. 安装器直接运行；ZIP 检查没有绝对路径、越界或链接后解压到新目录，再按下面步骤使用。无需克隆开发仓库。

Windows；准备包需 Python 3.11+、可用网络，后续隔离安装需 uv。解压后双击 prepare.cmd；它按 assets.json 下载并核验固定源码到全新 app/，不启动、不注册宿主。已有 app/ 时拒绝覆盖。

按 app/README.md 运行 app/install.cmd，使用固定源码的 uv.lock 和项目内 Python/环境；之后 app/start.cmd 是 stdio 入口。注册 Agent 时只新增这个服务，保留其他 MCP 配置；宿主配置必须按该宿主当前规则执行。WSL 也要通过 Windows 进程调用桌面能力。

文件准备、服务可启动、宿主发现工具和真实桌面调用分别验收；只有目标聊天真实调用 Screenshot/Snapshot 后，才报告已接通。本轮分发整理不自动注册或读取桌面内容。

## 给 Agent：交给 AI 执行

```text
安装并使用 https://github.com/strive822/zyd-vibe-lab 里的 windows-mcp。先读取该项目 INSTALL.md，从固定 Release 下载对应成品并校验，按项目类型安装或启动；保留已有数据与配置。日常使用不克隆开发仓库、不重新构建前端；只下载时不安装或启动。
```

本文全部小节是 Agent 执行时的完整约束。先检查已有安装、数据与端口；复用已验收现用程序或按本次授权升级，保留账号和用户文件。用户仅要求下载时，不安装、不启动；用户要求安装或启动时，按已给授权完成。不要安装无关项目。首次联网准备与实际启动/宿主接入分别报告。

固定附件及其大小/哈希登记在仓库根 releases.json；有源码仓库副本时可用 `python scripts/get_release.py --project windows-mcp --destination <仓库外的新目录>` 下载并得到 JSON 核验结果。下载器不执行程序。

## 源码开发

开发源码位于本仓库 `windows-mcp/`，第三方来源与许可见本目录 LICENSE / THIRD_PARTY（存在时）。阅读 AGENTS.md 后再测试或构建；常规使用只取 Release。编译缓存、依赖环境和构建输出放任务临时目录，最终程序不提交 Git。

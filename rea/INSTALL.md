# REA：安装与验证

## 给人：自己动手的步骤

1. 打开 [固定 Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/rea-v6.8.0-r2)，下载 `rea-windows.zip` 和 `SHA256SUMS.txt`。
2. 在下载目录执行 `Get-FileHash -Algorithm SHA256 .\rea-windows.zip`，与校验文件逐项比对；不匹配则停止。
3. 安装器直接运行；ZIP 检查没有绝对路径、越界或链接后解压到新目录，再按下面步骤使用。无需克隆开发仓库。

Windows，准备包需 Python 3.11+、网络；CLI 需符合包 engines 的 Node/npm（本机 Node22.23.4 满足）。解压后双击 prepare.cmd，下载并核验 rea-agents-6.8.0.tgz 到全新 app/；不会全局安装、执行 setup 或安装分析引擎。

包准备后按 app/README.md 检查 `npx.cmd --yes rea-agents@6.8.0 --help`。需要 setup 时先展示将新增的单个宿主配置与引擎计划，按用户已授权范围执行，保留其他配置。原 tgz 可作为 npm 的本地来源；不要用未知镜像替换锁定包。

不自动安装无关 Node、Java、Ghidra 等；仅分析有权处理的目标。不把帮助输出或包下载成功声称为原生分析引擎已经可用。

## 给 Agent：交给 AI 执行

```text
安装并使用 https://github.com/strive822/zyd-vibe-lab 里的 rea。先读取该项目 INSTALL.md，从固定 Release 下载对应成品并校验，按项目类型安装或启动；保留已有数据与配置。日常使用不克隆开发仓库、不重新构建前端；只下载时不安装或启动。
```

本文全部小节是 Agent 执行时的完整约束。先检查已有安装、数据与端口；复用已验收现用程序或按本次授权升级，保留账号和用户文件。用户仅要求下载时，不安装、不启动；用户要求安装或启动时，按已给授权完成。不要安装无关项目。首次联网准备与实际启动/宿主接入分别报告。

固定附件及其大小/哈希登记在仓库根 releases.json；有源码仓库副本时可用 `python scripts/get_release.py --project rea --destination <仓库外的新目录>` 下载并得到 JSON 核验结果。下载器不执行程序。

## 源码开发

开发源码位于本仓库 `rea/`，第三方来源与许可见本目录 LICENSE / THIRD_PARTY（存在时）。阅读 AGENTS.md 后再测试或构建；常规使用只取 Release。编译缓存、依赖环境和构建输出放任务临时目录，最终程序不提交 Git。

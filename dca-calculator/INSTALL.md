# 三资产定投计算器：安装与验证

## 给人：自己动手的步骤

1. 打开 [固定 Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/dca-calculator-v1.0.0-r1)，下载 `dca-calculator-windows.zip` 和 `SHA256SUMS.txt`。
2. 在下载目录执行 `Get-FileHash -Algorithm SHA256 .\dca-calculator-windows.zip`，与校验文件逐项比对；不匹配则停止。
3. 安装器直接运行；ZIP 检查没有绝对路径、越界或链接后解压到新目录，再按下面步骤使用。无需克隆开发仓库。

Windows，需 Python 3.11+ 和首次安装依赖的网络；成品已包含静态前端，不需要 Node。解压到新目录，双击 start.cmd。首次在本目录创建 backend/.venv 并安装 requirements-runtime.txt，随后打开 http://127.0.0.1:8000 。终端 Ctrl+C 停止。

验证 `/api/health` 返回 `{"status":"ok"}` 且首页可访问。行情不可达时应显示明确错误，不伪造权重；此工具不执行交易。端口冲突时识别已有服务，不结束未知进程。删除程序目录前停服务，无账号数据需要迁移。

## 给 Agent：交给 AI 执行

```text
安装并使用 https://github.com/strive822/zyd-vibe-lab 里的 dca-calculator。先读取该项目 INSTALL.md，从固定 Release 下载对应成品并校验，按项目类型安装或启动；保留已有数据与配置。日常使用不克隆开发仓库、不重新构建前端；只下载时不安装或启动。
```

本文全部小节是 Agent 执行时的完整约束。先检查已有安装、数据与端口；复用已验收现用程序或按本次授权升级，保留账号和用户文件。用户仅要求下载时，不安装、不启动；用户要求安装或启动时，按已给授权完成。不要安装无关项目。首次联网准备与实际启动/宿主接入分别报告。

固定附件及其大小/哈希登记在仓库根 releases.json；有源码仓库副本时可用 `python scripts/get_release.py --project dca-calculator --destination <仓库外的新目录>` 下载并得到 JSON 核验结果。下载器不执行程序。

## 源码开发

开发源码位于本仓库 `dca-calculator/`，第三方来源与许可见本目录 LICENSE / THIRD_PARTY（存在时）。阅读 AGENTS.md 后再测试或构建；常规使用只取 Release。编译缓存、依赖环境和构建输出放任务临时目录，最终程序不提交 Git。

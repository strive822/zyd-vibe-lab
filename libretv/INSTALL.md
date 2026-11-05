# LibreTV：安装与验证

## 给人：自己动手的步骤

1. 打开 [固定 Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/libretv-v2.21.1-r1)，下载 `libretv-windows.zip` 和 `SHA256SUMS.txt`。
2. 在下载目录执行 `Get-FileHash -Algorithm SHA256 .\libretv-windows.zip`，与校验文件逐项比对；不匹配则停止。
3. 安装器直接运行；ZIP 检查没有绝对路径、越界或链接后解压到新目录，再按下面步骤使用。无需克隆开发仓库。

Windows，需 Node.js 22 或更新版本。成品已包含 standalone 生产输出，不运行 npm install 或 npm build。解压到新目录，双击 start.cmd；打开 http://127.0.0.1:8080 。只监听本机，Ctrl+C 停止。

首次运行生成本地 `.env.local` 随机密码；在该文件读取 PASSWORD 登录，文件不能上传。DEFAULT_SOURCES 使用包内 defaults.json；再次启动保留原密码和设置。升级停服务，将旧 `.env.local` 保留并迁入新版本目录，不覆盖已有程序目录。`/api/status` 应报告版本2.21.1且 passwordRequired 为 true；这不代表所有外部播放源都可用。

AGPL-3.0-or-later；完整对应源码在本仓库 libretv/source。修改后提供网络服务时遵守 AGPL 源码义务。

## 给 Agent：交给 AI 执行

```text
安装并使用 https://github.com/strive822/zyd-vibe-lab 里的 libretv。先读取该项目 INSTALL.md，从固定 Release 下载对应成品并校验，按项目类型安装或启动；保留已有数据与配置。日常使用不克隆开发仓库、不重新构建前端；只下载时不安装或启动。
```

本文全部小节是 Agent 执行时的完整约束。先检查已有安装、数据与端口；复用已验收现用程序或按本次授权升级，保留账号和用户文件。用户仅要求下载时，不安装、不启动；用户要求安装或启动时，按已给授权完成。不要安装无关项目。首次联网准备与实际启动/宿主接入分别报告。

固定附件及其大小/哈希登记在仓库根 releases.json；有源码仓库副本时可用 `python scripts/get_release.py --project libretv --destination <仓库外的新目录>` 下载并得到 JSON 核验结果。下载器不执行程序。

## 源码开发

开发源码位于本仓库 `libretv/`，第三方来源与许可见本目录 LICENSE / THIRD_PARTY（存在时）。阅读 AGENTS.md 后再测试或构建；常规使用只取 Release。编译缓存、依赖环境和构建输出放任务临时目录，最终程序不提交 Git。

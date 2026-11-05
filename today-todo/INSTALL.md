# 今日待办：安装与验证

## 给人：自己动手的步骤

1. 打开 [固定 Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/today-todo-v1.0.0-r1)，下载 `today-todo-windows.zip` 和 `SHA256SUMS.txt`。
2. 在下载目录执行 `Get-FileHash -Algorithm SHA256 .\today-todo-windows.zip`，与校验文件逐项比对；不匹配则停止。
3. 安装器直接运行；ZIP 检查没有绝对路径、越界或链接后解压到新目录，再按下面步骤使用。无需克隆开发仓库。

Windows，需 Node.js 18+。解压到新目录，双击 start.bat；本项目零依赖，不需要 npm install。浏览器打开终端显示的 localhost 地址，默认3000，被占用时按原逻辑使用3001–3005。

验证页面、添加一条合成待办并重启后仍在；唯一用户数据是 data/todos.json，升级先停服务、备份并保留 data/。Ctrl+C 或关闭服务终端停止；不要用扫描端口方式结束未知进程。手机访问需同一 Wi-Fi 的真实验证，不自动修改防火墙或加入开机自启。

卸载前保留需要的 data/，停止自己的服务，再删除应用目录。

## 给 Agent：交给 AI 执行

```text
安装并使用 https://github.com/strive822/zyd-vibe-lab 里的 today-todo。先读取该项目 INSTALL.md，从固定 Release 下载对应成品并校验，按项目类型安装或启动；保留已有数据与配置。日常使用不克隆开发仓库、不重新构建前端；只下载时不安装或启动。
```

本文全部小节是 Agent 执行时的完整约束。先检查已有安装、数据与端口；复用已验收现用程序或按本次授权升级，保留账号和用户文件。用户仅要求下载时，不安装、不启动；用户要求安装或启动时，按已给授权完成。不要安装无关项目。首次联网准备与实际启动/宿主接入分别报告。

固定附件及其大小/哈希登记在仓库根 releases.json；有源码仓库副本时可用 `python scripts/get_release.py --project today-todo --destination <仓库外的新目录>` 下载并得到 JSON 核验结果。下载器不执行程序。

## 源码开发

开发源码位于本仓库 `today-todo/`，第三方来源与许可见本目录 LICENSE / THIRD_PARTY（存在时）。阅读 AGENTS.md 后再测试或构建；常规使用只取 Release。编译缓存、依赖环境和构建输出放任务临时目录，最终程序不提交 Git。

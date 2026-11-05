# 飞鼠格式：安装与验证

## 给人：自己动手的步骤

1. 打开 [固定 Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/flyingmouse-format-v0.7.10-r1)，下载 `flyingmouse-format-windows.zip` 和 `SHA256SUMS.txt`。
2. 在下载目录执行 `Get-FileHash -Algorithm SHA256 .\flyingmouse-format-windows.zip`，与校验文件逐项比对；不匹配则停止。
3. 安装器直接运行；ZIP 检查没有绝对路径、越界或链接后解压到新目录，再按下面步骤使用。无需克隆开发仓库。

Windows 10/11 x64。解压联网安装入口，双击 install.cmd；它下载未改动的官方 FlyingMouse-Format-Setup-0.7.10-x64.exe，核验 SHA-256 `56c022bc5ec1904300c8ffe77f892d0bea09fe157fbbf402589a64decab2587b` 后打开原安装向导。也可从上游官方 Release 直接下载同名安装器。

上游地址：https://github.com/LaoFeng-mouse/flyingmouse-format/releases/tag/v0.7.10 。完整离线应用约3.76 GiB，主要是 Office、OCR、音视频等必需引擎；这是程序运行内容，不能当开发缓存删除。已有安装时先检查版本与路径，不重复下载整套引擎。

启动 FlyingMouse Format.exe，做一张合成图片转 PNG 或一个小 TXT 转 PDF 验证，不改用户原始文件。上游为非商用许可，保留牢蜂/LaoFeng署名、LICENSE与第三方说明，不套壳改名。Agent 驱动转换按 agent-skill/flyingmouse-format/SKILL.md，在应用内完成连接后使用 CLI，不声称仅复制技能就已连接。

## 给 Agent：交给 AI 执行

```text
安装并使用 https://github.com/strive822/zyd-vibe-lab 里的 flyingmouse-format。先读取该项目 INSTALL.md，从固定 Release 下载对应成品并校验，按项目类型安装或启动；保留已有数据与配置。日常使用不克隆开发仓库、不重新构建前端；只下载时不安装或启动。
```

本文全部小节是 Agent 执行时的完整约束。先检查已有安装、数据与端口；复用已验收现用程序或按本次授权升级，保留账号和用户文件。用户仅要求下载时，不安装、不启动；用户要求安装或启动时，按已给授权完成。不要安装无关项目。首次联网准备与实际启动/宿主接入分别报告。

固定附件及其大小/哈希登记在仓库根 releases.json；有源码仓库副本时可用 `python scripts/get_release.py --project flyingmouse-format --destination <仓库外的新目录>` 下载并得到 JSON 核验结果。下载器不执行程序。

## 源码开发

开发源码位于本仓库 `flyingmouse-format/`，第三方来源与许可见本目录 LICENSE / THIRD_PARTY（存在时）。阅读 AGENTS.md 后再测试或构建；常规使用只取 Release。编译缓存、依赖环境和构建输出放任务临时目录，最终程序不提交 Git。

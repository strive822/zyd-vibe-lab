# 岛仔 Daozai：安装与验证

## 给人：自己动手的步骤

1. 打开 [固定 Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/daozai-v0.6.50-r5)，下载 `Daozai-Setup-v0.6.50-x64.exe` 和 `SHA256SUMS.txt`。
2. 在下载目录执行 `Get-FileHash -Algorithm SHA256 .\Daozai-Setup-v0.6.50-x64.exe`，与校验文件逐项比对；不匹配则停止。
3. 双击安装器，升级前退出已有实例；无需克隆开发仓库或重新编译。

Windows 10/11 x64。下载 `Daozai-Setup-v0.6.50-x64.exe` 与 `SHA256SUMS.txt`，核验后双击。默认当前用户安装到 `%LOCALAPPDATA%\Programs\Daozai`，不需要管理员权限；创建开始菜单入口，桌面快捷方式和开机自启由安装时选择。升级先退出托盘中的旧实例，保留账号和设置。

安装后从开始菜单或桌面“岛仔”启动。应仅有一个 daozai.exe，路径为选定安装目录，版本0.6.50；EXE SHA-256 为 `DC52A836DAE57F3F8FC0248694AA2D481C6FF76E3419CF9C249E48E4F3ADA4EE`，GLM 显示斜线 Z 标。不要把同版本上游包误认成本个人版。

复制文字、图片或文件时应显示独立复制图标的“剪贴板 / 已复制”提示。设置 → 常规 → 岛体显示可开启“双击右键居中”，默认关闭；开启后在岛体上连续右击两次，位置恢复所选屏幕中央并保存。采用 Windows 双击间隔与距离设置；单击、长按及混合鼠标键不触发。系统提示遵从“系统状态”开关，与暂存收集、普通岛仔提醒分开。

暂存站可拖入文字、链接、文件、文件夹、多文件和图片。网页图片、邮件附件等虚拟内容按系统提供的 PNG/DIB/位图或 FileGroupDescriptorW + FileContents（流/内存）接收，保留附件原名和字节；本地文件只引用原路径。按住 `·` 可穿透到下层窗口，松开恢复接收。

卸载走 Windows“已安装的应用”；用户数据保留。异常回退先退出程序，再恢复事先备份的程序；不覆盖安装后新增数据。安装器 SHA-256 为 `c5242a64858546f91c34bdd17c1abbf8ae407c6288fc3b8570ad0e81e3481230`。

## 给 Agent：交给 AI 执行

```text
安装并使用 https://github.com/strive822/zyd-vibe-lab 里的 daozai。先读取该项目 INSTALL.md，从固定 Release 下载对应成品并校验，按项目类型安装或启动；保留已有数据与配置。日常使用不克隆开发仓库、不重新构建前端；只下载时不安装或启动。
```

本文全部小节是 Agent 执行时的完整约束。先检查已有安装、数据与端口；复用已验收现用程序或按本次授权升级，保留账号和用户文件。用户仅要求下载时，不安装、不启动；用户要求安装或启动时，按已给授权完成。不要安装无关项目。首次联网准备与实际启动/宿主接入分别报告。

固定附件及其大小/哈希登记在仓库根 releases.json；有源码仓库副本时可用 `python scripts/get_release.py --project daozai --destination <仓库外的新目录>` 下载并得到 JSON 核验结果。下载器不执行程序。

## 源码开发

开发源码位于本仓库 `daozai/`，第三方来源与许可见本目录 LICENSE / THIRD_PARTY（存在时）。阅读 AGENTS.md 后再测试或构建；常规使用只取 Release。编译缓存、依赖环境和构建输出放任务临时目录，最终程序不提交 Git。

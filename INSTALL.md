# 给 Agent 的下载与使用入口

这是包含三个独立项目的仓库。用户要你下载、安装或运行时，请完成实际操作，并报告文件、环境和运行的真实结果。

## 按用户点名的项目选择

| 用户描述 | 目标项目 | 先读取 |
| --- | --- | --- |
| 毕业论文、论文工作流、graduation-thesis-workflow | 安装论文技能，再进入需求访谈 | [论文安装入口](graduation-thesis-workflow/INSTALL.md) |
| 定投、三资产、计算器、dca-calculator | 下载源码、准备依赖、启动本地网页 | [计算器安装入口](dca-calculator/INSTALL.md) |
| 额度、浮窗、usage、codex-usage | Windows x64 优先使用便携包 | [浮窗安装入口](codex-usage/INSTALL.md) |

仅说“安装这个仓库”且无法从上下文确定项目时，只询问选择哪个项目；不要默认安装三个。说“安装工作流”沿用论文入口。

## 获取完整文件

仓库：`https://github.com/strive822/zyd-vibe-lab`。

有 Git 时可克隆到新的目录。没有 Git 时，由 Agent 用实际可用的下载和文件工具取得 `https://github.com/strive822/zyd-vibe-lab/archive/refs/heads/main.zip`，安全解压后取目标子目录；不要求用户先学 Git。需要源码的项目不能只下载 README、单个脚本或单独的 exe。

需要直接读取入口时，使用：

```text
https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/INSTALL.md
https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/graduation-thesis-workflow/INSTALL.md
https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/dca-calculator/INSTALL.md
https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/codex-usage/INSTALL.md
```

按当前宿主识别 Windows / PowerShell、WSL / Linux 或 macOS，并检查实际可用工具。Agent 自动完成已授权且必要的依赖准备；组织策略和系统权限提示仍使用正常流程，不绕过。

下载放到本次专用临时目录。拒绝绝对路径、`..` 越界、符号链接逃逸和文件名冲突；解压前检查条目。已有同名目录先检查内容；不同或不完整内容保留，选新目录，更新则依用户授权先备份。验证提供的校验和；失败最多重试两次，不换未知来源。

## 完成标准

报告选择了哪个项目、实际保存或安装路径、依赖准备结果、启动命令或访问地址、验证结果，以及仍需用户处理的步骤。文件已下载、进程已启动、页面可访问、账号已连接、技能已被宿主发现是不同状态，逐项如实说明。

真实论文材料不进入公共仓库；密钥在本机安全输入；额度浮窗安装不自动开启登录启动。不能把合成测试数据、历史截图或缓存值报告为当前真实结果。

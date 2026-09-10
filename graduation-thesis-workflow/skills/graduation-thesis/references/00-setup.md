# 零基础用户的环境准备

用户不需要会终端、Git、Python、pip 或 JSON。不要把安装命令甩给用户；由助手检查、运行和核验，向用户只说明正在做什么。首次安装技能本身若宿主没有自动导入能力，让用户在 WorkBuddy 界面导入 ZIP，这是客户端操作，不是假设可以改内部配置。

## 授权与工作目录

新手启动语授权下载必要免费依赖时，直接在授权目录配置，无需逐包再问。若没有安装授权，先告诉用户将安装哪些必要工具并取得授权。系统、组织或宿主的权限提示不能绕过；用户只需处理真实权限弹窗。付费、账号登录和未公开资料外传不包含在免费依赖授权内。

请用户选择工作文件夹；如不知道怎么选，由助手提出其可访问的默认目录。助手新建 `.thesis-tools/` 存运行环境，另建空的 `thesis-project/` 存论文资料。不得先在 thesis-project 写 capabilities 再调用要求空目录的 init；能力记录先存工具目录，初始化后再写入项目。

## Windows 10/11（首版自动安装路径）

Windows 自带 PowerShell，不要求预装 Python 或 Git。先检测宿主自带且允许使用的 Python，其次使用以下脚本。脚本实际路径由已安装技能位置确定，不让用户手填。

```text
powershell.exe -NoProfile -File <技能目录>/scripts/bootstrap-windows.ps1 -ToolsDir <工作目录>/.thesis-tools -Profile core
```

若脚本执行策略阻止运行，遵守宿主/组织策略，通过授权的执行入口运行；不能修改机器级执行策略。无执行能力时说明宿主权限限制，不能声称已安装。

脚本自动探测兼容 Python；没有时从 python.org 下载固定的 Python 3.13.15 官方安装器，检查 Windows 签名与 Python Software Foundation 发布者，执行当前用户安装，不修改全局 PATH、不安装启动器。然后创建隔离环境。固定版本失效/不可达时不能换随机镜像，核对 Python 官方 Windows 发布页后修正或报告真实阻塞。

从 `.thesis-tools/runtime.json` 读取 python 的绝对路径；实际 status=ready 后才用该解释器运行项目初始化和其他脚本。不要要求用户激活环境。保存来源、版本与失败情况。

学校要求 Word、PDF、PPT、表格或绘图时再执行相同脚本的 `-Profile documents`。它从官方 PyPI 安装 python-docx、reportlab、PyMuPDF、python-pptx、openpyxl、matplotlib，检查实际导入并记录版本。仅在需求需要时安装，不做无关依赖堆积。新安装包以后分发产物时需注意各自许可，不能把仓库 MIT 当成包许可证。

## 文档输出与额外工具

导入库成功不等于文件排版通过。生成实际小样验证所需格式；PDF 用可用渲染库查看。Word/PPT 的版式核验优先复用宿主 Office/LibreOffice/文档转换能力。若需要而未安装，由助手从官方发布渠道获取合适平台安装器，核查来源与签名、按当前用户条件安装，然后用实际转换验证。遇到管理员权限或许可确认，只请求必要用户操作；不虚构验证成功，不把 Word 源码检查充当可视检查。

特殊研究依赖如 R、LaTeX、统计软件，按已确认课题实际需要选择。免费安装可沿用授权，收费软件另问；安装受阻时继续无依赖工作。

## macOS/Linux 与恢复

本包目前只提供 Windows 的可执行自动安装脚本。其他系统由助手核查宿主现有 Python 和官方安装方式，不能运行 Windows 脚本或宣称已经验证这些系统的零依赖启动。

网络失败最多重试两次；记录具体失败来源。再次进入先复用 ready 环境，不重复下载。已有不完整安装目录先检查，禁止递归清空用户环境。核心安装和文档安装分别记录结果，不让文档安装失败伪装成全套就绪。

官方依据：[Python Windows 安装](https://docs.python.org/3/using/windows.html)、[Windows 发布列表](https://www.python.org/downloads/windows/)。

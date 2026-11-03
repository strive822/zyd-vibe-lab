# 给 Agent：flyingmouse-format（飞鼠格式）下载、核验与使用

本目录是上游 [LaoFeng-mouse/flyingmouse-format](https://github.com/LaoFeng-mouse/flyingmouse-format) v0.7.10 的完整源码快照（固定 commit `a7b9b15d32db80cecedae00e89289088656fb1ae`），原样保留上游 `LICENSE`、`THIRD_PARTY_NOTICES.md`、`README.md`（仅在顶部前置 Agent 入口段落）与上游自带的 `agent-skill/`。上游为非商用许可：个人免费使用与传播，禁止商业售卖与套壳。

## 获取完整文件

单独传递时，取本目录 `delivery/flyingmouse-format.zip` 与配套校验文件，实际核对 SHA-256，检查归档路径后解压到新目录。包内包含完整 `flyingmouse-format/` 目录，不依赖仓库内其他项目。

官方仓库内的完整独立包与校验文件：

```text
https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/flyingmouse-format/delivery/flyingmouse-format.zip
https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/flyingmouse-format/delivery/SHA256SUMS.txt
https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/flyingmouse-format/delivery/FILES.json
```

先核验 ZIP 的 SHA-256（与 `SHA256SUMS.txt` 首行比对），再检查归档条目没有绝对路径、`..`、链接或重名冲突，解压到新目录并与 `FILES.json` 比对逐文件哈希。校验失败即停止，不换未知来源。

PowerShell 核验示例：

```powershell
$expected = (Get-Content .\SHA256SUMS.txt).Split(' ')[0]
$actual = (Get-FileHash .\flyingmouse-format.zip -Algorithm SHA256).Hash.ToLower()
if ($expected -ne $actual) { throw 'SHA-256 mismatch' }
Expand-Archive .\flyingmouse-format.zip -DestinationPath D:\MyTools\
```

## 只想要软件本体：官方安装包（推荐）

用户只想在 Windows 上转换文件时，直接用上游官方 release 安装包，不经过本仓库二次打包：

```text
https://github.com/LaoFeng-mouse/flyingmouse-format/releases/download/v0.7.10/FlyingMouse-Format-Setup-0.7.10-x64.exe
SHA-256: 56c022bc5ec1904300c8ffe77f892d0bea09fe157fbbf402589a64decab2587b
```

系统要求 Windows 10/11 x64。下载后核对 SHA-256，再安装：

- 图形安装：双击运行安装包。
- Agent 静默安装（NSIS）：

```powershell
Start-Process -FilePath 'D:\Downloads\FlyingMouse-Format-Setup-0.7.10-x64.exe' -ArgumentList '/S', '/D=C:\Users\me\Desktop\飞鼠格式转换' -Wait
```

`/D=` 指定安装目录，必须是最后一个参数、等号后不换行；省略 `/D=` 时默认装到用户目录。安装完成后主程序为安装目录下的 `FlyingMouse Format.exe`（由启动器拉起 `FlyingMouse Format Runtime.exe` 窗口进程）。

## 验证

1. 启动 `FlyingMouse Format.exe`，窗口（标题含 FlyingMouse Format）出现即启动成功；窗口进程是 `FlyingMouse Format Runtime.exe`。首次启动可能比后续慢（杀软扫描与缓存预热），属正常现象。
2. 转换自测：拖入一张图片转 PNG，或用一个小 TXT 转 PDF，在保存目录确认产物存在且能打开。

## 让 Agent 驱动转换（可选）

上游自带 `agent-skill/flyingmouse-format/`（含 `SKILL.md`）。按该目录说明把技能装进 Agent 后，可走应用 CLI 检查与转换：

```powershell
node scripts/flyingmouse-format.js targets <file> --json
node scripts/flyingmouse-format.js convert <files...> --to <format> --output-dir <dir> --json
node scripts/flyingmouse-format.js merge-pdfs <pdfs...> --output <result.pdf> --json
```

CLI 依赖已安装的应用在应用内“Connect to Agent”完成连接；未连接时先做 GUI 安装与验证。

## 源码路径（阅读与二次开发）

- 运行时要求：Node.js ≥ 18。`npm ci` 安装依赖，`npm test` 跑上游测试套件。
- 转换引擎（FFmpeg / LibreOffice / Poppler / Tesseract 等）由上游构建流程按锁定清单下载打包，源码目录不包含引擎二进制；阅读与修改源码不需要引擎，直接运行转换需要官方安装包或自行准备引擎。

## 权限边界

- 非商用许可：个人免费使用、传播时必须保留 `LICENSE` 与原作者（牢蜂 / LaoFeng）署名；禁止销售、倒卖、套壳改名后冒充自有产品。
- 安装只写入用户指定的安装目录；不改动系统 PATH、不写注册表外的系统位置；转换在本地离线完成，文件不上传云端。
- 核验失败即停止并报告，不下载或替换为未知来源的文件；不自动删除用户的原始文件与转换产物。

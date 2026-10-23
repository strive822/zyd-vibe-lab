# 给 Agent：LibreTV 独立下载与恢复

## 获取完整文件

本地目录可直接使用。单独传递时，取本目录 `delivery/LibreTV.zip` 与
`delivery/SHA256SUMS.txt`，实际核对 SHA-256，检查归档路径并解压到新目录。
包内包含完整 `LibreTV/` 目录，不依赖 github-toolbox 或其他项目。

官方仓库内的完整独立包与校验文件：

```text
https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/LibreTV/delivery/LibreTV.zip
https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/LibreTV/delivery/SHA256SUMS.txt
https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/LibreTV/delivery/FILES.json
```

先核验 ZIP 的 SHA-256，再检查归档条目没有绝对路径、`..`、链接或重名冲突。
解压到新目录，并与 FILES.json 比较逐文件哈希。校验失败停止，不换未知来源。


## 恢复（用户要求安装或准备运行环境时）

使用 Windows x64 的 Python 3.11+。在本项目目录执行：

```powershell
python .\restore.py --destination 'D:\MyTools\LibreTV'
```

只处理本项目，校验大小与 SHA-256；目标已存在时拒绝覆盖。
缺少运行时先检查实际环境，按用户授权放到项目目录，不改系统 PATH、不全局安装。
仅要求下载时停在文件保存与核验阶段，不执行 restore.py。

LibreTV 恢复会准备独立 Node 和依赖并构建；yt-dlp 会准备 FFmpeg/Deno 并检查版本。
Windows-MCP 仅保存源码与入口，后续依赖安装和 MCP 注册另行处理。
REA 仅保存固定 npm 包，不运行 setup 或安装分析引擎。
Winhance 仅保存官方安装器，不运行安装器或修改系统设置。
本项目具体使用方式见 README.md 和 profile/ 中的说明。

## 可以直接给 Agent 的提示词

```text
请下载并核验 LibreTV 的独立交付包，保留全部文件和许可，解压到新目录。
先阅读包内 INSTALL.md；只下载，不安装、不启动、不修改全局配置。
```

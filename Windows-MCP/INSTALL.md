# 给 Agent：Windows-MCP 独立下载与恢复

## 获取完整文件

本地目录可直接使用。单独传递时，取本目录 `delivery/Windows-MCP.zip` 与
`delivery/SHA256SUMS.txt`，实际核对 SHA-256，检查归档路径并解压到新目录。
包内包含完整 `Windows-MCP/` 目录，不依赖 github-toolbox 或其他项目。

官方仓库内的完整独立包与校验文件：

```text
https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/Windows-MCP/delivery/Windows-MCP.zip
https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/Windows-MCP/delivery/SHA256SUMS.txt
https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/Windows-MCP/delivery/FILES.json
```

先核验 ZIP 的 SHA-256，再检查归档条目没有绝对路径、`..`、链接或重名冲突。
解压到新目录，并与 FILES.json 比较逐文件哈希。校验失败停止，不换未知来源。


## 恢复（用户要求安装或准备运行环境时）

使用 Windows x64 的 Python 3.11+。在本项目目录执行：

```powershell
python .\restore.py --destination 'D:\MyTools\Windows-MCP'
```

只处理本项目，校验大小与 SHA-256；目标已存在时拒绝覆盖。
缺少运行时先检查实际环境，按用户授权放到项目目录，不改系统 PATH、不全局安装。
仅要求下载时停在文件保存与核验阶段，不执行 restore.py。

恢复只保存固定 Windows-MCP 0.8.8 源码和入口。用户要求安装时，先确认 Windows uv 可用，再在恢复目录运行 install.cmd；该入口用源码 uv.lock 创建 source/.venv 和项目内 Python 3.14.7，不改全局环境。缺少 uv 时取得官方 Windows uv 便携程序，放到项目内并在当前进程 PATH 使用。

用 source/.venv/Scripts/python.exe -m windows_mcp --help 检查入口。start.cmd 以 stdio 运行固定源码；MCP 注册是另外的宿主配置步骤，依用户授权操作，不能凭下载或 --help 声称已接入。具体说明见 profile/README.md。

## 可以直接给 Agent 的提示词

```text
请下载并核验 Windows-MCP 的独立交付包，保留全部文件和许可，解压到新目录。
先阅读包内 INSTALL.md；只下载，不安装、不启动、不修改全局配置。
```

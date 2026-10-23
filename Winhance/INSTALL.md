# 给 Agent：Winhance 独立下载与恢复

## 获取完整文件

本地目录可直接使用。单独传递时，取本目录 `delivery/Winhance.zip` 与
`delivery/SHA256SUMS.txt`，实际核对 SHA-256，检查归档路径并解压到新目录。
包内包含完整 `Winhance/` 目录，不依赖 github-toolbox 或其他项目。

官方仓库内的完整独立包与校验文件：

```text
https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/Winhance/delivery/Winhance.zip
https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/Winhance/delivery/SHA256SUMS.txt
https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/Winhance/delivery/FILES.json
```

先核验 ZIP 的 SHA-256，再检查归档条目没有绝对路径、`..`、链接或重名冲突。
解压到新目录，并与 FILES.json 比较逐文件哈希。校验失败停止，不换未知来源。


## 恢复（用户要求安装或准备运行环境时）

使用 Windows x64 的 Python 3.11+。在本项目目录执行：

```powershell
python .\restore.py --destination 'D:\MyTools\Winhance'
```

只处理本项目，校验大小与 SHA-256；目标已存在时拒绝覆盖。
缺少运行时先检查实际环境，按用户授权放到项目目录，不改系统 PATH、不全局安装。
仅要求下载时停在文件保存与核验阶段，不执行 restore.py。

恢复只下载官方 Winhance v26.06.12 的 Winhance.Installer.exe，核对 assets.json 中的大小和 SHA-256，保存许可和 Required Notice。

成功标准是固定版本安装器与校验值一致。下载请求不运行安装器，也不宣称系统已经安装或优化。安装和系统改动由用户另行指定；具体许可见 THIRD_PARTY.md。

## 可以直接给 Agent 的提示词

```text
请下载并核验 Winhance 的独立交付包，保留全部文件和许可，解压到新目录。
先阅读包内 INSTALL.md；只下载，不安装、不启动、不修改全局配置。
```

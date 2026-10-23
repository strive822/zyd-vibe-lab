# 给 Agent：rea 独立下载与恢复

## 获取完整文件

本地目录可直接使用。单独传递时，取本目录 `delivery/rea.zip` 与
`delivery/SHA256SUMS.txt`，实际核对 SHA-256，检查归档路径并解压到新目录。
包内包含完整 `rea/` 目录，不依赖 github-toolbox 或其他项目。

官方仓库内的完整独立包与校验文件：

```text
https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/rea/delivery/rea.zip
https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/rea/delivery/SHA256SUMS.txt
https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/rea/delivery/FILES.json
```

先核验 ZIP 的 SHA-256，再检查归档条目没有绝对路径、`..`、链接或重名冲突。
解压到新目录，并与 FILES.json 比较逐文件哈希。校验失败停止，不换未知来源。


## 恢复（用户要求安装或准备运行环境时）

使用 Windows x64 的 Python 3.11+。在本项目目录执行：

```powershell
python .\restore.py --destination 'D:\MyTools\rea'
```

只处理本项目，校验大小与 SHA-256；目标已存在时拒绝覆盖。
缺少运行时先检查实际环境，按用户授权放到项目目录，不改系统 PATH、不全局安装。
仅要求下载时停在文件保存与核验阶段，不执行 restore.py。

恢复只取得校验后的 rea-agents 6.7.0 npm 发布包和许可，不运行 setup、不安装分析引擎。

用户要求使用时，在本项目准备符合包 engines 的独立 Node/npm（推荐 24.22.1 LTS），按 profile/README.md 运行固定版本的帮助入口。setup 可能修改 Agent 配置和下载引擎，先展示具体计划；只下载请求停在包完整性核验。

## 可以直接给 Agent 的提示词

```text
请下载并核验 rea 的独立交付包，保留全部文件和许可，解压到新目录。
先阅读包内 INSTALL.md；只下载，不安装、不启动、不修改全局配置。
```

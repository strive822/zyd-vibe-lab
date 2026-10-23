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

恢复准备 LibreTV 2.21.0、项目内 Node.js 24.22.1 LTS、个人预置源，并执行依赖安装、类型检查、Lint、测试和构建。首次恢复生成独立随机访问密码，保存在恢复目录 source/.env.local，不回显或上传。

运行时在恢复目录双击 start.vbs，访问 http://localhost:8080；停止用 stop.vbs。先检查端口占用，验证 /api/status 返回 version=2.21.0、页面可访问与登录状态。源站搜索、播放可用性须用实际链接验证，构建通过不能替代。

## 可以直接给 Agent 的提示词

```text
请下载并核验 LibreTV 的独立交付包，保留全部文件和许可，解压到新目录。
先阅读包内 INSTALL.md；只下载，不安装、不启动、不修改全局配置。
```

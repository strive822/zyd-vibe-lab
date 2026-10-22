# 我的 GitHub 工具箱

保存我在 Windows 上实际使用的 5 个 GitHub 工具及其个人使用配置。整理基线：2026-10-22。入口面向日常使用和换目录恢复，源码作者、版权和项目名称仍归各上游。

| 工具 | 固定版本 | 我的使用方式 | 本仓库保留什么 |
| --- | --- | --- | --- |
| LibreTV | 2.19.7 | 双击启动，后台服务复用，Edge 新窗口最大化，量子/非凡两项预置源 | 当前本地完整源码快照、锁文件、启动/停止/重建脚本、预置源 |
| yt-dlp | 2026.10.21 | 在聊天中提供视频链接，下载到工具旁的 `xiazai`；默认单条，可转 MP3 | 路径自适应的下载入口与配置生成；固定 FFmpeg / Deno 来源 |
| Windows-MCP | 0.8.7 | 独立 Windows 运行环境，stdio，关闭遥测；供 Agent 操作桌面 | 可迁移的安装/启动脚本、固定源码、接入边界 |
| REA | rea-agents 6.7.0 | 按需使用 CLI；接入 Agent 时走原向导 | 固定包及来源、操作说明；没有虚构已经接入的个人配置 |
| Winhance | v26.06.12 | 按需打开工具，逐项理解后调整 | 官方安装包校验和与个人使用说明；未发现可发布的个人配置导出 |

## 换电脑 / 换目录

先读 [安装入口](INSTALL.md)。取得本仓库的完整 `github-toolbox` 目录后，在 Windows PowerShell 使用 Python 3.11+ 恢复到新目录；下载与解压按大小和 SHA-256 核验。LibreTV 自动安装锁定依赖、类型检查、Lint、测试和生产构建。

```powershell
python .\restore.py LibreTV --destination 'D:\MyTools\LibreTV'
python .\restore.py yt-dlp --destination 'D:\MyTools\yt-dlp'
```

每次只选择要用的工具。原工作目录及正在运行的服务保持原样。首次恢复需要联网，源码包不包含 `node_modules`、`.next` 和 Node.exe；这些从固定来源重新获取，不依赖我电脑上其他目录。

## 日常使用

- LibreTV：双击恢复目录的 `start.vbs`；密码在该目录 `source/.env.local`，每次新安装随机生成。`stop.vbs` 停止本启动器的服务。关闭网页不等于停止后台服务。桌面快捷方式可手动指向 `start.vbs`。
- yt-dlp：[下载说明](profiles/yt-dlp/README.md)。聊天中给 Agent 一个你有权下载的视频链接，或运行 `download.cmd`。保持“单条、Windows 文件名、默认 xiazai、FFmpeg、Deno”的原习惯。
- Windows-MCP：[连接说明](profiles/Windows-MCP/README.md)。恢复与注册连接分开进行，保留原有 Agent 设置；当前聊天中真实调用工具才算接入验收。
- REA：[使用说明](profiles/rea/README.md)。保留按需安装/向导确认方式，避免自动改全局 Agent 配置。
- Winhance：[使用说明](profiles/Winhance/README.md)。这里只恢复安装包，运行软件、系统权限和具体系统设置由本人决定。

LibreTV 只监听 `127.0.0.1:8080`，端口冲突会报错。第三方源存在时效性；本轮验证结果与未验收项见 [整理报告](REPOSITORY_CLEANUP_REPORT.md)。

## 结构与维护

`profiles` 是个人启动方式和公开默认值；`packages/libretv-source.zip` 是从当前本地目录导出的完整源码，不重新抓取上游 main；`packages/libretv-files.json` 逐文件记录 SHA-256；[assets.json](assets.json) 固定外部下载与大小、SHA-256；`restore.py` 负责恢复。

LibreTV 源码基线为上游 `9d86ec2568895b2a8b52da47fc9bfea6c74f8378`，快照保存整理时实际本地内容，包括当前 package-lock。REA 本地参考源码为 `933af60eba43c29f1fb1c606fddcd725ae0d9d96`，其 npm 发布包与源码 main 分开记录；未修改的参考源码从上游固定提交获取，不作为个人原创重复发布。

维护者在 Windows PowerShell 的仓库根目录执行：

```powershell
python github-toolbox/scripts/export_profile.py --source 'E:\GitHub灵感'
python -m unittest discover -s github-toolbox/tests -v
python scripts/check_repository.py
```

重新导出后必须同步更新 `assets.json` 中本地源码 ZIP 的大小和 SHA-256，再验证。导出脚本只读原目录，`.env.local` 只提取公开 `DEFAULT_SOURCES`，密码不导出。发布前审查这些 URL 是否仍为公开地址及是否含凭据。

## 许可与隐私

保留上游许可证和来源，详见 [THIRD_PARTY.md](THIRD_PARTY.md)。没有用一个统一 MIT 声明覆盖全部工具。密码、Cookie、会话、下载媒体、个人系统配置、MCP 配置整份备份、截图和日志不进入 GitHub。已有本地程序、依赖、构建和历史记录保留在原目录；本次整理不会删除日常运行所需文件。

# 每个项目的 Agent 交付规范

用户要求：现在所有项目，以及以后上传的项目，都提供可直接复制给 Agent 的使用入口。
项目各自放在独立子目录；LibreTV、yt-dlp、Windows-MCP、REA、Winhance 分别交付。

## README 模板

每个项目 README.md 的开头须包含以下内容，并替换真实名称和操作范围：

````markdown
## 直接让 Agent 帮你使用

把下面这段话复制给具备联网、文件读写和运行能力的 Agent。
先阅读本项目 [INSTALL.md](INSTALL.md)，再下载、核验与按需使用。

```text
下载并使用 https://github.com/strive822/zyd-vibe-lab 里的 <项目目录名>。
请先读取该项目 INSTALL.md，下载完整文件并核验，按说明准备项目内环境并验证结果；保留已有文件。
```
````

提示词按项目目的区分“仅下载”“安装”“运行”。不要让下载 Winhance 自动变成安装或系统优化，
也不要把 REA 下载、MCP 源码准备自动变成修改所有 Agent 配置。

## INSTALL.md 与交付包

- 说明完整获取方式、平台、运行时要求、固定下载来源与实际校验方法。
- 提供 Agent 可执行的命令，依赖放项目内，检查已有目录和端口，保留用户配置。
- 提供启动方法和能证明结果的检查；如实区分文件保存、进程启动、页面可访问和账号接入。
- 独立包保留源码、脚本、配置模板、必要资产清单和许可证，不依赖兄弟项目。
- `delivery/<项目名>.zip` 配套 `SHA256SUMS.txt` 和 `FILES.json`，禁止打包凭据、缓存、真实用户数据。
- 发布前更新根 README 提示词、项目表和下载链接。仅在真实上传并核验后声称远端可下载。

## 维护检查

```text
python scripts/agent_entry_policy.py
python -m unittest discover -s scripts/tests -v
python scripts/package_projects.py
python scripts/check_repository.py
```

打包脚本自动发现有 README.md 和 INSTALL.md 的独立项目。检查策略扫描所有非隐藏项目目录，
缺少 README、INSTALL.md、指定标题或包含项目名的可复制提示词时，CI 拒绝通过。

# 源码与 Release 交付规范

根 AGENTS.md 是权威规则。全部项目使用“Git 保存开发源码，Release 交付实际安装/运行内容”；Git 提交与标签保留；每个项目的 Release 仅保留最新一版。

## 两类读者

各项目 README 必须有 `## 直接让 Agent 帮你使用` 与含仓库 URL、项目名、INSTALL.md 的 text 提示词。每份 INSTALL.md 同时具有 `## 给人：` 与 `## 给 Agent：`：人可从浏览器下载、校验、安装和启动；Agent 按同一文档直接执行并报告真实结果。下载、安装、运行和宿主接入分别验证。

## 按类型打包

- 岛仔：已验收 GLM Z 标安装 EXE + SHA256SUMS.txt；无需便携/源码套娃包。
- 飞鼠：轻量官方安装器入口 + 校验；联网下载并核验固定的原版安装器，不重新打包离线转换引擎。
- DCA：静态导出的前端、Python 后端运行代码、依赖清单和 start.cmd；用户无需 Node 或前端构建。
- LibreTV：Next standalone 生产输出、静态资源、许可和 start.cmd；用户只需 Node，首次运行生成私有密码。
- Today Todo：零依赖服务、静态资源和启停入口；不含用户 data、测试或截图。
- Pi：宿主真正加载的扩展文件、package.json 和许可，不包含开发依赖。
- 论文：由 canonical skill 生成四个平台可导入 ZIP。
- yt-dlp / Windows-MCP / REA：联网准备包包含已锁来源、安装/恢复入口、使用配置及许可；不会自动下载媒体、注册 MCP 或执行 REA setup。

## 维护命令

```text
python scripts/agent_entry_policy.py
python -m unittest discover -s scripts/tests -v
python scripts/check_repository.py
```

构建输出必须位于仓库外，例如 ~/.codex/.tmp/<任务名>/release。先在仓库外复制并构建 dca-calculator/frontend（DCA_EXPORT=1）、libretv/source（DOCKER_BUILD=1），准备好 production 输出；复制运行依赖的许可证。再运行：

```text
python scripts/package_projects.py --output <任务目录>/release --prepared <任务目录>/prepared --installer <已验收Z标安装器路径> --update-catalog
```

prepared 下布局：dca-calculator/frontend/out、libretv/.next/standalone 和 libretv/.next/static。构建脚本拒绝仓库内输出。每项目可用 --project 单独构建。应用本体未变时可使用上版已验收且匹配固定哈希的岛仔安装器；应用改动后必须重新验收、更新打包脚本固定哈希与来源记录。

## 发布顺序

1. 保留用户工作，完成代码、文档和程序的必要检查、独立复审；确认 releases.json 的固定 tag、字节和哈希与最终包一致。
2. 提交源码；先推一个临时发布分支，让 commit 在 GitHub 可达，但不提前推进 main。
3. 对每个变更项目创建新 tag / Release，只上传该类型的成品和 SHA256SUMS.txt；说明运行时、是否首次联网和验证边界。已发布附件不原地覆盖。新版本下载核验通过后，备份同项目旧 Release 的元数据、附件和校验值，再清理旧 Release 及附件；Git 标签和源码提交保留。以 releases.json 按项目确定当前版本，不按全仓库唯一的 Latest 标记删除其他项目。
4. 下载所有新附件并逐项比对本地目录、releases.json 和 SHA256SUMS.txt；运行 `python scripts/verify_published.py --ref <commit>`。
5. 将 main 正常快进到同一 commit，核验远端 refs 与 CI。完成后删除本次临时发布分支、可重建缓存与重复下载；保留正式程序和必要证据。

GitHub 自动生成的 Source code ZIP/tar.gz 属平台功能；它不是手动上传的程序附件。用户入口直接指向成品；开发者从 Git 获取源码。

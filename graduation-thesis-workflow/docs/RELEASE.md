# GitHub 发布

公开副本位于 zyd-vibe-lab/graduation-thesis-workflow。在现有仓库根目录的 main 分支推送已经检查的本地提交；不要初始化新仓库或替换 remote。

1. 修改技能源后运行 `python -m unittest discover -s tests -v`。
2. 运行 `python scripts/package.py --out <仓库外的任务目录>`，生成四端可导入 ZIP；源码留在本项目，ZIP 与校验文件只发布到 GitHub Release。默认输出也在用户 Codex 临时目录，不在项目里。
3. 仓库维护时使用根 `scripts/package_projects.py --output <仓库外的任务目录> --project graduation-thesis-workflow --update-catalog` 生成 SHA256SUMS.txt 并更新 releases.json。原 `scripts/build_delivery.py` 仅保留为四端包构建兼容入口，不再创建源码套娃 ZIP。相同源码保持确定性条目和元数据。
4. 核对本地链接、ZIP 完整性、许可与校验和；只提交本项目文件，不混入原始论文、学校模板、凭证或其他项目修改。
5. 推送前核对 origin/main 与本地分支，保持使用者未提交的其他改动。先推临时发布分支，在同一 commit 的新 tag 发布并下载核验成品，再正常快进 main；完整顺序见根 docs/AGENT_DELIVERY_STANDARD.md，不覆盖旧 Release。
6. 安装/脚本测试与实际宿主端到端验收分别记录，不能把一种说成另一种。

原创内容适用 MIT；Humanizer 保留上游许可。调研来源与实际复制组件分开记录。实际论文项目应放在公开仓库之外。

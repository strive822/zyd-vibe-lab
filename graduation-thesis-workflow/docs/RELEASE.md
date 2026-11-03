# GitHub 发布

公开副本位于 zyd-vibe-lab/graduation-thesis-workflow。在现有仓库根目录的 main 分支推送已经检查的本地提交；不要初始化新仓库或替换 remote。

1. 修改技能源后运行 `python -m unittest discover -s tests -v`。
2. 运行 `python scripts/package.py --out packages`，把四个 ZIP 与 checksums.json 随本项目一起提交。规范源目录也可以用默认 dist 暂存构建结果。
3. 运行 `python scripts/build_delivery.py` 重建 `delivery/` 的 ZIP、SHA256SUMS 与 FILES.json。该脚本固定条目顺序、时间戳与平台字段，同一份签出字节重建结果相同；项目在 `.gitattributes` 中标记为 `-text`，因此 CRLF 签出不会改变 FILES.json。
4. 核对本地链接、ZIP 完整性、许可与校验和；只提交本项目文件，不混入原始论文、学校模板、凭证或其他项目修改。
5. 推送前核对 origin/main 与本地分支，保持使用者未提交的其他改动。推送不等于发布 GitHub Release。
6. 安装/脚本测试与实际宿主端到端验收分别记录，不能把一种说成另一种。

原创内容适用 MIT；Humanizer 保留上游许可。调研来源与实际复制组件分开记录。实际论文项目应放在公开仓库之外。

# 维护流程

1. 修改唯一技能源；阶段逻辑变化时检查对缺材料、证据范围和恢复行为的影响。
2. 脚本变更运行 `python -m unittest discover -s tests -v`。测试使用临时目录，不接触用户论文。
3. 可使用 skill-creator 的 quick_validate 检查源 SKILL.md；它不是研究行为验证。
4. 涉及检索时，用公开查询做一次真实联网检查，结果只放 `.test-output/`；网络故障不能记录为通过。
5. 运行 `python scripts/package.py --out packages`，检查三个 ZIP 和哈希。
6. 更新 DEVLOG、GOTCHAS、DECISIONS 与 docs/VALIDATION。发布按 docs/RELEASE.md。

开始真实论文：读完整入口，初始化独立私有目录，确认需求，再按状态推进。检查器报错先查实际产物，不为通过测试修改真假判定或删掉需求。

新增安装器测试需在允许执行 PowerShell 的正常用户权限下运行，不修改系统执行策略。技能、脚本或 vendor 变更后重建 packages，保留第三方许可。polishing.json 缺失的旧论文项目应先创建 pending 记录并实际执行润色，不回填虚假完成状态。

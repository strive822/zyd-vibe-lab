# 项目状态与证据协议 v1

初始化脚本生成 JSON 骨架及私有目录。空骨架故意不能通过交付检查。所有文件路径相对于论文项目根目录，不得跳出；技能和论文项目相互独立。JSON 使用 UTF-8。用 `project.py hash <实际文件>` 计算哈希，不手填猜测。

## requirements.json

保留 schema_version=1。version 是从 1 开始的需求版本。confirmed 只在实际确认后置 true，confirmation_path 指向确认摘要。discipline/topic/deadline 按用户实际输入填写。methods 从 literature、quantitative、qualitative、engineering、experimental 选择，可多选。

school_requirements_path 指向读取学校材料后形成的要求表，表内含来源、定位与原文件路径；材料尚缺则保留阻塞。ai_policy.status 在实际检查后设 checked，source_path 指向检查笔记（含所查来源、结论和未知项）；checked 不表示学校允许所有 AI 用法。

deliverables 每项为 `{ "id": "thesis", "path": "deliverables/thesis.docx" }`。实际项目按用户所需格式填写。

acceptance_criteria 每项包含 id、requirement、status（pending/met）、review_path、review_sha256。requirement 写实际学校要求；例如篇幅、模板、引用、必需章节、AI 限制等。不能只写“完成论文”。review_path 指向已执行检查的记录，哈希绑定记录。是否充分覆盖学校要求由实质审查检查。

## state.json

schema_version=1，requirements_version 必须匹配需求版本。status 取 intake/design/research/drafting/review/polishing/delivery/needs_input/complete。blockers 是未解决问题的字符串列表；不得为了通过检查清空真实缺口。next_action 写具体恢复动作。阶段完成更新 NEXT.md 与 DEVLOG.md。不要把等待时间当成用户确认。

## evidence.json（对象列表）

每项必须有 id、kind、path、sha256、provenance、retrieved_at、verification。

- kind：literature/data/run/derivation/source。
- path：实际保存的论文笔记、原始数据、运行输出、推导或其他材料；文献笔记中包含所读原文定位及来源。
- provenance：取得方式及采集/运行者，写实际情况。
- retrieved_at：实际获取日期/时间。
- verification：checked 表示已执行相应来源核对；user_supplied_unverified 表示用户提供且采集来源未独立核实，不等于数据被判定虚假。
- literature 另需 url 和 read_scope（metadata/abstract/fulltext），不能随意升级阅读范围。

### 文献的 source_check

正式交付至少登记一条经核验的文献证据。每条 `kind=literature` 的记录均需 `verification=checked` 和 `source_check` 对象。填写实际操作：

| 字段 | 内容 |
|---|---|
| `provider` | 实际核对书目的学术数据库、出版方或权威机构名称 |
| `record_url` | 具体学术条目 URL。外部书目记录可与实际阅读所用的 `url` 相同 |
| `checked_on` | 实际核对日期，YYYY-MM-DD |
| `publication_status` | `no_notice_found` 表示在已查来源未见更新公告，`corrected` 表示已核对更正并采用相应版本 |
| `status_url` | 实际检查的出版状态页面、公告或条目；同一条目能核对状态时可复用其 URL |
| `search_log_path` | 项目内检索日志的相对路径，通常为 `literature/search-log.md` |

撤稿、撤回、关注声明和状态仍待核对的文献留在筛选日志。论文分析某项撤稿时，可登记核验过的撤稿公告。文献笔记保存书目详情、实际阅读范围与定位，DOI 缺失可用稳定条目核验。

大文件可放在私有项目内；不能把敏感原始数据塞进公开仓库。多个文件可分别登记并通过 runs 记录关联。

## claims.json（对象列表）

每项为 id、text、location（正文章节/段落）、status（supported/unsupported）、evidence_ids（id 列表）、required_scope、locator（证据的页/段/表/运行位置）、rationale（为何支持）。required_scope 取 metadata/abstract/fulltext/original；original 用于自己的数据、运行、推导等。混合论断应拆分，避免用摘要支撑全文级细节。

引用 user_supplied_unverified 证据时另填 provenance_disclosure，记录论文如何披露来源核验限制。unsupported 的事实句不能进入最终稿。所有核心论点、数字、引语及文献性事实都要登记，检查器无法自动证明正文没有遗漏登记。

## artifacts.json（对象列表）

每项 id 对应 deliverables id，并有 path、sha256、status=reviewed、review_path、review_sha256。审查报告说明审阅人/代理、日期、实际检查范围、结果与局限。输出更新后旧哈希失效；不要不经重审就刷新哈希。

## 检查的边界

`project.py audit` 检查必需记录、非空文件、路径范围、哈希、需求版本、阻塞、引用 id 和阅读范围。`check_literature.py` 额外检查文献登记字段、URL 格式、出版状态和检索日志。后者离线运行，实际访问、来源权威性、文献真实性、引用一致性和论据是否充分由阶段 03 与 06 核验。排版由阶段 07 实际渲染检查。

## polishing.json

初始为 tool=humanizer-zh、status=pending（0.3.x 及更早项目记录为 tool=humanizer，审计同时接受两个值）。实际润色后填写 status=applied、before_path/before_sha256、after_path/after_sha256、review_path/review_sha256。前后文件和审查报告都必须实际存在且哈希匹配。学校明确禁止时允许 status=skipped_school_policy，另需 reason、policy_source_path 和审查报告。工具检查不能证明润色质量，仍须审查其语义与最终文件来源。旧项目缺少此记录时创建 pending 并补做，不能直接标完成。

## final-review.json：绑定实际审查版本

完成内容、语言、排版和交付记录的实质审查后运行 `project.py review-snapshot <项目目录> --report reviews/final-review.md`。该命令只生成当前文件哈希快照，不执行审查、不自动批准、也不设置 complete。

快照绑定 requirements/evidence/claims/artifacts/polishing 五份 JSON 及其中 path 或 *_path 指向的文件，以及最终审查报告。变更这些文件后，audit 拒绝沿用旧快照，即使人工刷新 artifacts 中的哈希也会失败。未登记文件不受此检查覆盖，必须把实际使用的材料和交付物完整登记。进度日志与 state 不绑定，便于交付后记录 complete。

旧项目保持 schema_version=1。使用新流程续做正式交付时，重新打开旧来源并补齐实际核验记录和检索日志，保留已有稿件；记录变动后按当前材料重审并建立新快照。缺润色或审查记录时实际补做，不能回填虚假历史。

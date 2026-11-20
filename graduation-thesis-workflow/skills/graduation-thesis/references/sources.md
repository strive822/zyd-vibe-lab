# 公开文献来源与访问边界

按研究问题、语言和文献类型选择入口。搜索引擎和 AI 推荐只用于发现，正式核对时打开可定位到具体作品的官方条目或授权原文，并记录实际访问范围。

| 来源 | 用途与限制 |
|---|---|
| [中国知网](https://www.cnki.net/) / [万方数据](https://www.wanfangdata.com.cn/) | 中文期刊、学位论文等；查看具体条目，全文权限以实际访问为准 |
| [国家哲学社会科学文献中心](https://www.ncpssd.cn/) | 中文人文社科期刊、集刊、古籍等；核对具体记录与版本 |
| [Crossref REST API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/) | 核对注册 DOI 与书目；用本包脚本保存实际响应。覆盖不完整，需对照出版条目 |
| [Crossmark](https://www.crossref.org/crossmark/) / [Crossref 的 Retraction Watch 数据](https://www.crossref.org/documentation/retrieve-metadata/retraction-watch/) | 补查更正与撤稿；与出版方原始公告对照，未发现记录时注明实际检查范围 |
| [arXiv](https://arxiv.org/) | 预印本与版本；不能把预印本称为已同行评审 |
| [PubMed](https://pubmed.ncbi.nlm.nih.gov/) / [PMC](https://pmc.ncbi.nlm.nih.gov/) | 生物医学检索与部分合法全文；PubMed 命中不保证全文开放 |
| [Europe PMC](https://europepmc.org/) | 生命科学文献及部分全文，按条目核实访问和许可 |
| [DOAJ](https://doaj.org/) | 开放获取期刊发现，仍须核对具体文章 |
| [ERIC](https://eric.ed.gov/) | 教育领域，按条目区分全文和索引 |
| [ACM DL](https://dl.acm.org/) / [IEEE Xplore](https://ieeexplore.ieee.org/) | 计算机与工程出版记录；全文取决于实际访问条件 |
| 出版社官网、大学机构仓储、国家统计机构、正式法规网站 | 按课题查原始出版物、数据、史料或法条，核对版本与使用条件 |

摘要支持的范围局限于其实际内容。搜索引擎摘要用于发现，不作为论文核心证据。无法获取全文时请求用户通过合法权限提供，或使用能够支持相同问题的其他真实材料；不能写“已通读”。

API 接口及访问政策可能变化。本包直接实现 Crossref，其他入口通过宿主浏览器/搜索使用，并未实现专用 API 连接器。不要凭这张目录声称接入了全部数据库。

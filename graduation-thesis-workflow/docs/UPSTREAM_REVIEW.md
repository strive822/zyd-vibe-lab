# 上游调研与本次采用范围

调研用于选择设计，不代表已验证这些项目的全部功能或论文质量。本次新增代码和中文指引为本项目独立实现，没有复制下列仓库代码或技能文本；已内置 Humanizer 仍按 THIRD_PARTY_NOTICES.md 单独保留原版与许可。

| 参考项目 | 采用的设计思路 | 没有引入的部分 |
| --- | --- | --- |
| [academic-writing-toolkit](https://github.com/yha9806/academic-writing-toolkit) | 证据笔记与论点关联、审查绑定具体文件哈希、结构检查不等于语义真实性 | Node 运行框架及整套命令系统 |
| [codex-paper-workflow](https://github.com/shuohui-air-technology/codex-paper-workflow) | 润色保留原稿、保护数字/引用/公式、修改后重审 | 多阶段人工确认及外部依赖全量安装 |
| [scholarly-agent-skills](https://github.com/hideshi/scholarly-agent-skills) | 来源批判、逐论点核验、来源定位和阅读范围 | 未适配的多提供商检索器及其配置 |
| [claude-academic-workflow](https://github.com/ericluo04/claude-academic-workflow) | 实证方法适用条件与可复现记录，作为会计分支参考 | 自动套用因果模型、整套专家调度 |

未纳入 academic-research-skills-workbuddy 全套：功能与现有入口重叠，且其 CC BY-NC 许可需要单独遵守，不能把复制的内容当作本项目 MIT 代码重新许可。非商业许可并非禁止所有再分发。

后续若真正引入任何第三方文件，必须重新检查当时的许可、固定提交、保存许可和来源哈希，再验证依赖与三端适配；本页的链接并不是依赖锁文件。

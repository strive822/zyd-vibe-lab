# REA：来源、版本与许可

- 运行包固定为 npm [rea-agents 6.8.0](https://registry.npmjs.org/rea-agents/-/rea-agents-6.8.0.tgz)，字节和 SHA-256 见 assets.json；该包仍是最新稳定发行。
- 对应上游 [morluto/rea 的 rea-agents-6.8.0 tag](https://github.com/morluto/rea/tree/rea-agents-6.8.0)，提交 `160d821ac9a0310afcb8d1fc427862dd6508add5`。旧参考933af60早于该版本，现已纠正；不把源码参考当作 npm 成品的替代校验。
- MIT；保留 profile/LICENSE 与包内 LICENSE、THIRD_PARTY_NOTICES、licenses。
- 包的 Node engines 为 `^22.23.4 || ^24.22.1 || >=26.12.1`。当前未追踪未发布主线，不自动安装分析引擎或运行 setup。
- 本地修改为固定下载、核验与使用入口；保留 setup 先展示改动计划、保护其他宿主配置和只分析授权目标的边界。

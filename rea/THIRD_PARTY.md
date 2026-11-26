# REA：来源、版本与许可

- 运行包固定为 npm [rea-agents 6.10.1](https://registry.npmjs.org/rea-agents/-/rea-agents-6.10.1.tgz)，字节和 SHA-256 见 assets.json。
- 上游 [rea-agents-6.10.1](https://github.com/morluto/rea/tree/rea-agents-6.10.1) 提交为 `8bb01b514ac766c0c3ecc8f362bd38186eaec9c2`，与 npm provenance 记录的构建提交一致。上一固定版为 `d74549e495c58eb4a560279fd9f05508401ea0a0`（6.9.0）。
- MIT；保留 profile/LICENSE 与包内 LICENSE、THIRD_PARTY_NOTICES、licenses。
- 包的 Node engines 为 `^22.23.4 || ^24.22.1 || >=26.12.1`。当前未追踪未发布主线，不自动安装分析引擎或运行 setup。
- 本地修改为固定下载、核验与使用入口；保留 setup 先展示改动计划、保护其他宿主配置和只分析授权目标的边界。

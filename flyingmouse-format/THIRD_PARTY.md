# 飞鼠格式：来源、许可与本地修改

- 上游：[LaoFeng-mouse/flyingmouse-format](https://github.com/LaoFeng-mouse/flyingmouse-format)，稳定版 v0.8.3，固定提交 `e8d0827016192f980893b08c09920305ef089dab`。旧基线 v0.7.10 为 `a7b9b15d32db80cecedae00e89289088656fb1ae`。
- 保留原作者牢蜂（LaoFeng）、原 LICENSE、THIRD_PARTY_NOTICES.md、第三方补丁许可证和完整公开业务源码。非商用许可：仅供个人免费使用，禁止商业售卖、转卖与套壳；未改变许可或产品品牌。
- 本地修改为 README/AGENTS 的 Agent 入口、安装说明、忽略规则和联网安装包装；业务代码按旧基线三方同步到 v0.8.3。上游测试 fixture 的 CRLF 差异保持本地内容，JSON 与上游一致。
- 不在源码 Git 中跟踪预编译 EXE。AVS3 helper 从上述固定提交单独下载并校验；保留 bin/avs3/THIRD_PARTY_NOTICE.txt 与 model.bin。转换引擎由官方安装器分发，各自许可见原 THIRD_PARTY_NOTICES.md。
- 官方安装器：[FlyingMouse-Format-Setup-0.8.3-x64.exe](https://github.com/LaoFeng-mouse/flyingmouse-format/releases/download/v0.8.3/FlyingMouse-Format-Setup-0.8.3-x64.exe)，1,618,541,947 bytes，SHA-256 `3a3825bd3eb751c451978c6248a52c17e122fdf708556fd7a4cc55739592ec2d`（官方 GitHub 资产摘要）。本仓库只提供核验和启动官方安装器的轻量入口，不重命名软件。
- 上游 main 的 0.8.4 Store 候选未纳入本次稳定版同步。本次没有替换本机已装 0.7.10，也不沿用旧版安装验收作为新版结论。

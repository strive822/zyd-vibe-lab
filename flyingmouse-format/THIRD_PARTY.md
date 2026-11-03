# 来源、许可和修改边界

这是个人使用配置合集。下表描述所用版本的实际声明，不为其他版本作保证。

| 项目 | 来源 / 版本 | 本仓库处理 |
| --- | --- | --- |
| 飞鼠格式 FlyingMouse Format | [LaoFeng-mouse/flyingmouse-format](https://github.com/LaoFeng-mouse/flyingmouse-format/tree/a7b9b15d32db80cecedae00e89289088656fb1ae)，v0.7.10，[非商用许可](https://github.com/LaoFeng-mouse/flyingmouse-format/blob/main/LICENSE)（个人免费使用与传播，禁止商业售卖、倒卖、套壳） | 完整源码与原 `LICENSE`、`THIRD_PARTY_NOTICES.md`、上游 README 一起保留；仅在 README 顶部前置"直接让 Agent 帮你使用"入口段落，未改动上游源码与署名；不重新打包、不冒充自有产品 |

## 引擎与二进制边界

- 仓库密钥扫描对 `tests/electron-security.test.js` 整文件豁免：该文件是上游安全测试，内含 `user:pass@` 形状的 URL 假样本（非真实凭据），豁免已在 `scripts/check_repository.py` 的 `SECRET_SCAN_EXEMPT` 中注明理由。
- 转换引擎（FFmpeg、LibreOffice、Poppler、Tesseract、Pandoc 等）不在本目录内再分发：源码快照只含源码与锁定清单（`ci-engines-v1.json`、`*-engine-lock.json`），引擎二进制由上游官方 release 安装包按锁定版本分发，各组件许可见上游 `THIRD_PARTY_NOTICES.md`。
- Windows 安装包应从上游官方 release 下载并核对官方 SHA-256（见本目录 INSTALL.md），不通过本仓库镜像分发安装包。
- 上游 `agent-skill/flyingmouse-format/` 属上游原样内容，许可与署名要求同上。

若后续对本目录源码做修改并公开发布，须显著标注原作者：牢蜂（LaoFeng），并同样遵守上游非商用许可的限制。

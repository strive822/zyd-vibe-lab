# 上游同步与个人修改保留（2026-11-05）

Git 保存源码、测试、锁定来源和许可证；各项目成品另发新 Release，既有标签和附件保持不变。本轮未改写历史，也不将 upstream main 等同于正式稳定版。

| 项目 | 本轮固定来源 | 处理 |
| --- | --- | --- |
| 岛仔 | [v0.6.50 / b93dd84](https://github.com/Renly1994/xiaotang-daozai/tree/b93dd84fc9bdb95978fef72ffb7068bdf47ac5a9) | 保留八家额度、整岛定位、暂存、GLM Z 标等个人修改；新增复制 HUD、拖动修正和可选右键长按居中 |
| 飞鼠 | [v0.8.3 / e8d0827](https://github.com/LaoFeng-mouse/flyingmouse-format/tree/e8d0827016192f980893b08c09920305ef089dab) | 从 0.7.10 三方同步；保留本地 Agent 入口、安装器下载锁和源码分发边界；未追 0.8.4 Store 候选 |
| Windows-MCP | [固定主线快照 9ab92bc](https://github.com/CursorTouch/Windows-MCP/tree/9ab92bca2772dfb53ae3ed4feb98dac22c5b3dea) | 包含文件移动目录重叠修复；保留 Python 3.14.7、stdio、关闭遥测/看门狗的个人配置；不是新的正式版本号 |
| LibreTV | [v2.21.1 / 29cbeb3](https://github.com/LibreSpark/LibreTV/tree/29cbeb3d37b4876f909a0354087a3531af0447f6) | 保留 package.json / lock 的个人安全修复；启动器使用已有 @next/env 读取旧配置，未纳入未发布音量增强 |
| REA | [rea-agents-6.8.0 / 160d821](https://github.com/morluto/rea/tree/160d821ac9a0310afcb8d1fc427862dd6508add5) | npm 固定 6.8.0 不变；纠正旧源码参考和 Node engines 范围 |
| yt-dlp | [2026.10.26 / f264a6c](https://github.com/yt-dlp/yt-dlp/tree/f264a6cbd1f630894da0f368df00f8aae50140e0) | 保持正式版及已锁配套工具，纠正来源说明，不追 master |

DCA、Today Todo、Pi 通知扩展和论文技能不套用其他项目上游代码。Humanizer 引用保持已核对的固定来源。各目录 THIRD_PARTY.md 保留本项目来源与许可，飞鼠非商用约束、LibreTV AGPL 和配套工具的 GPL 说明继续保留。

## 验证边界

- 飞鼠业务代码对固定 0.8.3 逐文件对照；差异限于本地文档/Agent 约定、源码忽略规则、等价 JSON 换行与排除的预编译程序。新增 OFD 是上游合成测试夹具，不是用户文档。
- 飞鼠隔离副本运行完整测试，接只读现装引擎；文档结构引擎先通过上游锁定清单的哈希验证。结果 1226 通过、0 失败、13 跳过，其中一项因本机缺符号链接权限显式跳过。未改系统权限，未替换或测试操作现用飞鼠界面。
- Windows-MCP 的文件系统重叠回归 22 项通过。测试在 Python 3.12 上隔离桌面导入依赖，仅证明文件系统逻辑；没有安装 Python 3.14、注册宿主或实测桌面控制。
- LibreTV 引号配置、首次创建和重启登录三个场景通过，已有 .env.local 字节保持不变；未使用真实账号。
- 岛仔新增界面沿用以太网/中英文输入提示的 HUD，导出四档缩放对照图。自动测试、构建和本机安装的最新结论见 [岛仔交付记录](../daozai/docs/RELEASE-0.6.50-personal.md)，不能将自动回归当作真实设备和账号验收。

## 后续维护

先核对固定基线、正式 tag 与主线差异，再对有个人修改的文件作三方合并；不直接覆盖工作区。源码包/安装器更换后同步各项目来源、下载锁、INSTALL.md 和根 releases.json，重新构建受影响成品并从远端下载核验。旧 Release、私有回退归档和用户数据保留。

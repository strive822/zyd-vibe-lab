# 来源、许可与个人修改

| 内容 | 固定来源 | 处理 |
| --- | --- | --- |
| 岛仔 Daozai | [Renly1994/xiaotang-daozai](https://github.com/Renly1994/xiaotang-daozai/tree/11c52336d594d24bebc1bec865ab375626ca1e0f)，v0.6.65 commit `11c52336d594d24bebc1bec865ab375626ca1e0f` | MIT，保留原作者“小唐的Token and Daozai contributors”及 [LICENSE](LICENSE)；个人整合源快照 `07022995c16ab65353c11d38b61e1120ce5c18ef`，本仓库按目录跟踪后续修改 |
| AI 品牌图标 | Lobe Icons commit `ea434b96e75813517b377825e01c0df61dee8836`，`packages/static-svg/icons/zai.svg` 等 | MIT，出处与许可见 [图标说明](assets/ai-icons/README.md) |
| 本地 vendor 补丁与其他素材 | eframe 和 egui 0.31.1、imap 2.4.1、imap-proto 0.10.2、ureq 2.12.1 | 保留原 license；见 [依赖说明](docs/DEPENDENCIES.md)、[第三方声明](THIRD_PARTY_NOTICES.txt) 和各 vendor 目录 |

个人修改包含八家额度整合、暂存站修复、整岛拖动、顶栏信息入口、饮水/待办/日历显示及 GLM Z 标修正。具体行为与验证边界见 [交付记录](docs/RELEASE-0.6.50-personal.md)。README/INSTALL 与恢复脚本是本合集的使用入口，不将第三方项目冒充为自研项目；版权与商标仍归各权利人。

新增恢复脚本、包装测试及使用入口文档采用 MIT，Copyright (c) 2026 zhongyudi；原项目和第三方许可不变。

未复制本机真实配置、凭据、审查副本、临时日志或含本机路径的交接文档。原应用内作者支持入口及素材保持上游内容。

原生拖入使用现有锁定依赖 windows-rs 0.58.0（MIT / Apache-2.0），按 Microsoft 的 [Shell 数据格式](https://learn.microsoft.com/en-us/windows/win32/shell/clipboard) 和 [RegisterDragDrop](https://learn.microsoft.com/en-us/windows/win32/api/ole2/nf-ole2-registerdragdrop) 协议实现；支持 CF_HDROP、Unicode、PNG/DIB/位图与 FileGroupDescriptorW/FileContents。参考了 winit 0.30.13 的 `src/platform_impl/windows/drop_handler.rs` 的接口边界（MIT / Apache-2.0），没有复制其代码或修改全局依赖缓存。实现位于 `src/native_drop.rs`，替换只需撤销窗口注册并恢复 winit 的拖放开关。

文件夹仍走置物架原有缩略图队列。隔离候选从 [上游 1287316](https://github.com/Renly1994/xiaotang-daozai/commit/12873165fa22651261c8360220aba7288c81ade6) 三方合入 src/icons.rs 的文件夹系统图标修复，沿用本项目 MIT LICENSE。当时的完整上游基线为 v0.6.50。

### r8 部分同步

从 [上游 1c7702f](https://github.com/Renly1994/xiaotang-daozai/commit/1c7702f41547b3147e85be7022ce21dcbb4ff72b) 单独合入静止播放图标的绘制修复及光栅回归用例。当时的完整上游基线为 v0.6.50。随后在 v0.6.65 基线上继续维护个人功能。

### v0.6.65-r2 个人差异

个人版移除了上游 v0.6.65 的 `src/clipboard.rs` 历史记录模块、设置入口和暂存站剪贴板分栏。后续合入上游改动时继续排除这项功能。暂存收集和「已复制」提示仍由 `src/collect.rs` 提供。旧设置键自动忽略，已保存的 `clipboard.json` 留在原处供回退。回归测试覆盖两个界面入口、旧历史文件保留、暂存收集和复制提示。

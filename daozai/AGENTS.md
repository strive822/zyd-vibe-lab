# 岛仔个人版维护入口

先遵守仓库根 [AGENTS.md](../AGENTS.md)；独立包不存在父仓库时，以本文件及 INSTALL.md 为本项目边界。

- 来源：上游 v0.6.66 commit `08250c583dfda4fe3643af9e27cc93221b4170e9`，个人整合快照 `0702299`；详见 THIRD_PARTY.md。保留 LICENSE、vendor 许可和图标出处。
- 源码导航：src/app.rs 状态与布局，pages.rs 面板，main.rs/native.rs 原生窗口，quota.rs/quota_ui.rs 八家额度，staging.rs/collect.rs 暂存，display_layout.rs 多屏与整岛定位。
- 验证：`python -m unittest discover -s packaging_tests -v`；`cargo test --locked --all-targets --features record -- --test-threads=1`；release 构建与运行库检查命令见 README。测试会修改数据目录环境变量，必须单线程。真实账号 ignored 测试默认不运行。
- 不破坏 Claude/Kimi/Gemini 等现有八家额度来源；GLM 使用 assets/ai-icons/zai.svg。顶栏命中、悬停选页与拖岛排除范围必须一致。穿透行为与设置内排序维持已验收版本。
- 位置计算经 display_layout 和 native::place_on_display。读取旧设置时保留 `Settings::island_x` 的顶边逻辑像素偏移。完成一次新停靠拖动后保存 `dock` 和 `island_offset`，清除旧偏移。窗口实际位置可用于下一次拖动，系统边界和 OLED 像素偏移不得回写持久位置。
- 试运行设置独立 DAOZAI_DATA_DIR，先放禁用额度的 ai-quota.json。不得读取、打包或上传真实 AppData、Cookie、密钥、凭据管理器及个人备份。
- 不操作日常运行实例做自动测试。安装替换先备份并由用户终审，完成后核对路径、哈希、单实例与重启配置。不要把上游同版本安装包误称为本个人版。
- 临时文件与编译缓存置 ~/.codex/.tmp/；源码留 Git，安装器与校验只放 Release。运行根 python scripts/check_repository.py，发布规范见根约定。restore.py 只复制源码到全新目录，不安装或启动，不复制远端成品。
- restore.py 只复制 assets.json 的 source_files 白名单，新增/删除发布源码时同步该清单；不包含 packages 或 delivery。不得改回遍历整个工作目录复制私有文件。程序来源和哈希见根 releases.json。

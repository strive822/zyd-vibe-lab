# agent-desktop 维护说明

- `source/` 是完整上游快照，来源、提交及 Git tree 见 `upstream.json`。保留原署名、许可证、测试、隐藏配置和可执行脚本模式。修改上游源码时遵循 `source/AGENTS.md`。
- 本地源码位于发布后的上游提交。Windows x64 交付包使用 v1.3.1 的原版 `agent-desktop.exe`，与开发源码版本分别记录。
- Windows 检查开发源码时，从 `source/` 运行 `cargo metadata --locked --offline --no-deps --format-version 1`。进行 Rust 构建和测试时，按上游说明选择 Windows 包，并把 `CARGO_TARGET_DIR` 指向仓库外的本次任务目录。
- 先从 `upstream.json` 指定的官方 Release 下载并验证压缩包，再把解压的 `agent-desktop.exe` 放到仓库外 `prepared/agent-desktop/`。`python scripts/package_projects.py --project agent-desktop --output <仓库外目录> --prepared <prepared目录>` 会验证可执行文件哈希并生成 Windows 运行包和校验文件。
- 成品验证运行 `--version`，如需验证 MCP，使用只读 `desktop_list_windows`。宿主注册和桌面交互以用户本次授权为准。

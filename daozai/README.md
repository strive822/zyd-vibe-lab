# 岛仔 Daozai 个人版

Windows 10/11 x64 顶部信息岛，基于 [Renly1994/xiaotang-daozai](https://github.com/Renly1994/xiaotang-daozai) v0.6.50 整合并修复。保留原作者署名与 MIT 许可；这里发布的是个人修改版。

## 直接让 Agent 帮你使用

```text
安装并使用 https://github.com/strive822/zyd-vibe-lab 里的 daozai。先读取该项目 INSTALL.md，从固定 Release 下载对应成品并校验，按项目类型安装或启动；保留已有数据与配置。日常使用不克隆开发仓库、不重新构建前端；只下载时不安装或启动。
```

## 下载与使用

[固定 Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/daozai-v0.6.50-r2) 仅提供 Z 标个人版安装器与 SHA256SUMS.txt。使用步骤见 [INSTALL.md](INSTALL.md)；源码、许可与开发记录保存在仓库。

包含音乐/歌词、专注、饮水、待办、日历、邮件、暂存站及八种 AI 额度来源。此次修正版支持整岛拖动与位置保存、顶栏饮水百分比/未完成待办数/日期或星期，并使用 GLM 开放平台的斜线 Z 标识。图标排序在设置内进行；文件穿透沿用先拖文件再按 `·` 的行为。

安装包仍为 0.6.50；本个人版 EXE SHA-256 是 `B30AE844473A89A51C245E35A803DA630B23A3FAA452E06CC02CA0F640DA514F`，请用哈希区分同版本的上游包和较早个人构建。程序内“检查更新”只提示上游版本，不会自动覆盖个人版。

## 验证与维护

```powershell
python -m unittest discover -s packaging_tests -v
cargo test --locked --all-targets --features record -- --test-threads=1
cargo build --locked --release --bin daozai --target x86_64-pc-windows-msvc
./scripts/check-runtime.ps1 -Executable ./target/x86_64-pc-windows-msvc/release/daozai.exe
```

Rust stable、MSVC C++ 构建工具及 Windows SDK 用于源码构建；使用成品包不需要 Rust。测试必须单线程，真实账号相关 ignored 测试默认不运行。验证记录与边界见 [版本交付记录](docs/RELEASE-0.6.50-personal.md)。Windows 11 已本机安装并重启验收；Windows 10、其他真实 DPI/多屏及八家真实额度服务实连没有新增验收结论。

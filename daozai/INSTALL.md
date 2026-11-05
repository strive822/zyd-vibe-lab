# 下载、核验与使用岛仔个人版

本目录独立可用，不依赖同仓库其他项目。需要 Windows 10/11 x64 和支持 OpenGL 的显卡驱动；成品已包含所需 C/C++ 运行库。Python 3.11+ 仅用于恢复源码副本和包装测试。

## 1. 获取完整目录

从 https://github.com/strive822/zyd-vibe-lab/releases/tag/daozai-v0.6.50-r1 下载 `daozai.zip`、`SHA256SUMS.txt`、`FILES.json`。也可从仓库 `daozai/delivery/` 取得同名三件套。将下载保存至新的任务目录，核对 `Get-FileHash -Algorithm SHA256 .\daozai.zip` 与清单一致，再安全解压到新目录。ZIP 顶层是 `daozai/`，每个文件的 SHA-256 见 `FILES.json`；拒绝越界路径、符号链接和大小写冲突。不要覆盖已有目录。

需要固定源码而非独立包时，可克隆仓库后取本目录。下载完成不等于安装或运行。

## 2. 核验 Windows 成品

完整目录包含以下 `packages/` 文件；Release 也提供相同成品附件及 `SHA256SUMS-windows.txt`。直接从 Release 下载成品时，仍先读取本 INSTALL.md 并核对清单。

| 文件 | SHA-256 |
| --- | --- |
| `Daozai-Setup-v0.6.50-x64.exe` | `2FF8DBE6F9E26CC703CF87CFE7B2D7F27B6CE3FA3D0C351A439F5BE6D4D6CC3B` |
| `Daozai-v0.6.50-windows-x64.zip` | `D6B735862F42CCF715AC9608BD01F653A8A9A55F195653F4FB8A6030AB19A076` |

```powershell
Get-FileHash -Algorithm SHA256 .\packages\Daozai-Setup-v0.6.50-x64.exe
Get-FileHash -Algorithm SHA256 .\packages\Daozai-v0.6.50-windows-x64.zip
```

成品未签商业代码证书；遇到系统安全提示交由用户处理。不要绕过组织或系统安全策略。

## 3. 安装与启动

先检查是否已安装或正在运行岛仔。已有安装时，备份现用 EXE 和 `%APPDATA%\Daozai`，保留凭据管理器内的账号；向用户说明并确认替换及快捷方式/自启选项，退出旧实例并等待完全结束后再运行安装器。单实例限制会使第二个进程退出。

双击 `packages/Daozai-Setup-v0.6.50-x64.exe`，选择安装位置和快捷方式/自启选项，完成后从开始菜单启动“岛仔”。默认程序路径为 `%LOCALAPPDATA%\Programs\Daozai\daozai.exe`。这是会修改本机安装与入口的步骤，不能仅因已下载就自动执行。

也可将便携 ZIP 安全解压到新目录后运行 `daozai.exe`；它默认仍使用 `%APPDATA%\Daozai`，不代表数据隔离。需要无账号试运行时，先关闭旧实例，在新目录设置 `DAOZAI_DATA_DIR`，并创建以下 `ai-quota.json`，避免首次运行自动发现本机额度凭据：

```json
{"enabled":false,"compact":true,"selected":"","accounts":[],"colors":{}}
```

邮箱、工作日历与额度服务的登录/授权由用户自己完成；合成示例或进程启动不能证明真实账号已接入。具体功能见 [使用指南](docs/USAGE.md)。

## 4. 源码恢复与构建

源码已经在本目录中，无需联网恢复上游。若要准备独立工作副本，在本目录运行：

```powershell
python restore.py --destination C:\new-path\daozai-personal
```

目标必须不存在，且不能位于当前目录内。脚本核验 `assets.json` 中的成品，只复制其 `source_files` 发布白名单中的源码和成品，拒绝越界路径及链接；不安装、不启动、不复制后来放进工作目录的私有文件。个人配置说明见 [profile/README.md](profile/README.md)。依赖由锁文件固定；首次构建需要联网下载 Cargo 依赖。

在新副本安装好 Rust stable、MSVC C++ 构建工具和 Windows SDK 后：

```powershell
$env:CARGO_BUILD_JOBS = '1'
$env:CARGO_TARGET_DIR = Join-Path $PWD 'target'
cargo test --locked --all-targets --features record -- --test-threads=1
cargo build --locked --release --bin daozai --target x86_64-pc-windows-msvc
./scripts/check-runtime.ps1 -Executable ./target/x86_64-pc-windows-msvc/release/daozai.exe
```

开发试运行一律使用隔离 `DAOZAI_DATA_DIR` 与上述禁用额度配置。构建产物不保证跨工具链逐字节相同；本文 EXE 哈希对应随包分发、已在本机验收的成品。

## 5. 完成检查与回退

核对实际进程只有一个、路径是选定安装目录，EXE FileVersion 为 0.6.50、SHA-256 为 `B30AE844473A89A51C245E35A803DA630B23A3FAA452E06CC02CA0F640DA514F`。观察岛体贴顶、GLM 显示斜线 Z 标，重启后位置与配置保持；设置有意改动除外。保留安装前数据，异常时先退出新进程，再恢复备份的程序。不要为回退覆盖用户安装后新增的数据。

卸载通过 Windows“已安装的应用”；程序保留用户数据，删除用户数据需要单独授权。最终报告下载/安装路径、哈希、启动和验证结果，以及未实际验证的账号/设备状态。

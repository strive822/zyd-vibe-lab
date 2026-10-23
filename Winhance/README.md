# Winhance

## 直接让 Agent 帮你使用

把下面这段话复制给具备联网、文件读写和运行能力的 Agent。
它应先读本项目 [INSTALL.md](INSTALL.md)，完成提示词授权的下载、核验与使用步骤。
只想保存文件时，把“安装/运行”改成“只下载，不安装、不启动”。

```text
下载 https://github.com/strive822/zyd-vibe-lab 里的 Winhance。请先读取该项目 INSTALL.md，取得完整独立目录，下载官方固定版本安装包并核对 SHA-256，保留使用说明和许可；只下载，不运行安装器或修改系统设置。
```

本地独立交付包：`delivery/Winhance.zip`，校验文件：`delivery/SHA256SUMS.txt`。
直接下载：[独立项目 ZIP](https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/Winhance/delivery/Winhance.zip) · [SHA-256](https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/Winhance/delivery/SHA256SUMS.txt) · [逐文件清单](https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/Winhance/delivery/FILES.json)。
Agent 可下载独立 ZIP，或取得完整仓库后只使用本项目目录。

独立项目目录，保留原来的固定版本、个人使用配置和下载校验。无须获取其他项目。

- [Agent 下载与恢复](INSTALL.md)
- [来源与许可](THIRD_PARTY.md)
- `profile/`：启动入口、使用说明和许可副本；这是恢复材料，不能当成已安装程序。
- `assets.json`：仅包含本项目所需的固定下载来源、大小与 SHA-256。
- `restore.py`：只恢复本项目，目标必须是新目录。
- `delivery/`：本项目独立交付 ZIP、SHA-256 与逐文件清单，由根目录脚本生成。

# 我的 Winhance 使用入口

固定 v26.06.12 安装包，从原发布者下载并校验。本机目录还存在解压后的便携运行文件；未找到可以作为个人配置发布的导出文件，因此本合集保留使用方法与安装来源，没有编造系统优化预设。

恢复后自行运行 `Winhance.Installer.exe`，按安装器提供的选项安装/解压。Software & Apps 管软件，Optimize 查看系统选项，Customize 调外观。每次理解少量设置后再操作；配置导出不等于系统备份。恢复脚本不启动安装器、不卸载软件、不更改系统设置。

本版本为 PolyForm Shield 1.0.0；原许可及 Required Notice 见合集 THIRD_PARTY.md 和上游 LICENSE.txt。它不能被当作可随意改名发布的竞争替代软件。本轮仅验证下载完整性，不宣称系统优化效果或原生设备验收。

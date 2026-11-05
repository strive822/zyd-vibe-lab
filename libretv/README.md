# LibreTV

## 直接让 Agent 帮你使用

把下面这段话复制给具备联网、文件读写和运行能力的 Agent。
它应先读本项目 [INSTALL.md](INSTALL.md)，完成提示词授权的下载、核验与使用步骤。
只想保存文件时，把“安装/运行”改成“只下载，不安装、不启动”。

```text
安装并使用 https://github.com/strive822/zyd-vibe-lab 里的 libretv。先读取该项目 INSTALL.md，从固定 Release 下载对应成品并校验，按项目类型安装或启动；保留已有数据与配置。日常使用不克隆开发仓库、不重新构建前端；只下载时不安装或启动。
```

独立项目目录，保留原来的固定版本、个人使用配置和下载校验。无须获取其他项目。

当前固定 LibreTV 2.21.1 与 Node.js 24.22.1 LTS；源码快照包含已验证的依赖修复，见 [修复记录](SECURITY_PATCHES.md)。

- [Agent 下载与恢复](INSTALL.md)
- [来源与许可](THIRD_PARTY.md)
- `profile/`：启动入口、使用说明和许可副本；这是恢复材料，不能当成已安装程序。
- `assets.json`：仅包含本项目所需的固定下载来源、大小与 SHA-256。
- `restore.py`：只恢复本项目，目标必须是新目录。

## 成品下载

[固定 Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/libretv-v2.21.1-r1)：网页生产运行包，附 SHA256SUMS.txt。完整步骤见 [INSTALL.md](INSTALL.md)。仓库内保留源码，不保存构建包或依赖缓存。

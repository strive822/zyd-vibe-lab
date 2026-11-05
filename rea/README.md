# rea

## 直接让 Agent 帮你使用

把下面这段话复制给具备联网、文件读写和运行能力的 Agent。
它应先读本项目 [INSTALL.md](INSTALL.md)，完成提示词授权的下载、核验与使用步骤。
只想保存文件时，把“安装/运行”改成“只下载，不安装、不启动”。

```text
安装并使用 https://github.com/strive822/zyd-vibe-lab 里的 rea。先读取该项目 INSTALL.md，从固定 Release 下载对应成品并校验，按项目类型安装或启动；保留已有数据与配置。日常使用不克隆开发仓库、不重新构建前端；只下载时不安装或启动。
```

独立项目目录，保留原来的固定版本、个人使用配置和下载校验。无须获取其他项目。

- [Agent 下载与恢复](INSTALL.md)
- [来源与许可](THIRD_PARTY.md)
- `profile/`：启动入口、使用说明和许可副本；这是恢复材料，不能当成已安装程序。
- `assets.json`：仅包含本项目所需的固定下载来源、大小与 SHA-256。
- `restore.py`：只恢复本项目，目标必须是新目录。

# 我的 REA 使用入口

保留 rea-agents 6.8.0 npm 发布包使用方式。当前没有已确认的个性化 Agent 接入配置，因此恢复只准备包和说明，不自动执行 setup 或安装分析引擎。

Windows PowerShell，有满足包 engines 的 Node/npm 时：

```powershell
npx.cmd --yes rea-agents@6.8.0 --help
npx.cmd rea-agents@6.8.0 setup
```

第一条是帮助检查；第二条按原向导先展示将修改的配置与安装计划，再由用户确认。该包允许 Node ^22.19.0、^24.11.0 或 >=26；Node 24.22.1 满足 Node 版本条件；运行时需另行在本项目内准备，但 REA 的引擎和实际目标分析需单独验证。WSL 请使用 WSL 的 Node/npm 和该环境的配置，不把 Windows 路径混进去。

原下载包也可作为 `npm install` 的本地来源，但不强制全局安装。保留包内原许可、THIRD_PARTY_NOTICES 和 licenses。源码参考提交为 `933af60eba43c29f1fb1c606fddcd725ae0d9d96`，不是 npm 包构建结果的替代证明。

仅分析有权处理的目标；区分观察、推断和未知项；保留证据出处。不要自动安装/升级无关 Node、Java、Ghidra 或其他引擎，不宣称具备未实测的原生反编译能力。

## 成品下载

[固定 Release](https://github.com/strive822/zyd-vibe-lab/releases/tag/rea-v6.8.0-r1)：固定版本 CLI 联网准备包，附 SHA256SUMS.txt。完整步骤见 [INSTALL.md](INSTALL.md)。仓库内保留源码，不保存构建包或依赖缓存。

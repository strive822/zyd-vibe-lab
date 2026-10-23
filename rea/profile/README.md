# 我的 REA 使用入口

保留 rea-agents 6.7.0 npm 发布包使用方式。当前没有已确认的个性化 Agent 接入配置，因此恢复只准备包和说明，不自动执行 setup 或安装分析引擎。

Windows PowerShell，有满足包 engines 的 Node/npm 时：

```powershell
npx.cmd --yes rea-agents@6.7.0 --help
npx.cmd rea-agents@6.7.0 setup
```

第一条是帮助检查；第二条按原向导先展示将修改的配置与安装计划，再由用户确认。该包允许 Node ^22.19.0、^24.11.0 或 >=26；项目内 Node 24.22.1 满足 Node 版本条件，但 REA 的引擎和实际目标分析需单独验证。WSL 请使用 WSL 的 Node/npm 和该环境的配置，不把 Windows 路径混进去。

原下载包也可作为 `npm install` 的本地来源，但不强制全局安装。保留包内原许可、THIRD_PARTY_NOTICES 和 licenses。源码参考提交为 `933af60eba43c29f1fb1c606fddcd725ae0d9d96`，不是 npm 包构建结果的替代证明。

仅分析有权处理的目标；区分观察、推断和未知项；保留证据出处。不要自动安装/升级无关 Node、Java、Ghidra 或其他引擎，不宣称具备未实测的原生反编译能力。

# CodeGraph

为代码仓库建立本地知识图谱。Agent 可通过 MCP 或 CLI 找符号、跟踪调用路径并评估变更影响。

- [安装与验证](INSTALL.md)使用固定的官方 Windows x64 或 ARM64 便携包。
- [开发源码](source/)包含 CLI、MCP 服务、解析器、查看器和测试。版本与校验值见 [upstream.json](upstream.json)，原署名与许可见 [LICENSE](source/LICENSE)。

## 直接让 Agent 帮你使用

```text
安装并使用 https://github.com/strive822/zyd-vibe-lab 里的 codegraph。先读该项目 INSTALL.md，下载并核验适合本机的 CodeGraph 官方固定版本。已有同版本 CLI 时复用。确认 codegraph --version，只有我要求接入宿主或给项目建索引时才执行对应步骤。
```

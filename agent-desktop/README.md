# agent-desktop

Vercel Labs 开发的桌面操作工具，通过操作系统的无障碍接口读取和操作桌面应用。CLI 可独立运行，也可以通过 MCP 接入 Codex 等宿主。

- [安装与验证](INSTALL.md)适用于 Windows x64，包含 CLI 和 Codex MCP 入口。
- [上游源码](source/)固定在 [e8934a5e](https://github.com/vercel-labs/agent-desktop/tree/e8934a5e95e1d212c74ead95cd3e4701c04eca31)。源码、测试和开发说明均保留，使用 [Apache-2.0](source/LICENSE) 许可证。
- Windows 交付包使用 Vercel Labs 发布的 [v1.3.1 官方二进制](https://github.com/vercel-labs/agent-desktop/releases/tag/v1.3.1)。[upstream.json](upstream.json) 记录源码和程序各自的版本及校验值。

## 直接让 Agent 帮你使用

```text
安装并使用 https://github.com/strive822/zyd-vibe-lab 里的 agent-desktop。先读该项目的 INSTALL.md，下载 Windows x64 成品并校验，再用 --version 和只读 list-windows 验证。只有我明确要求接入 Codex 时才注册 MCP。
```

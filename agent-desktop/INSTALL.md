# 安装和验证 agent-desktop

## 给人：Windows x64

1. 打开 [agent-desktop v1.3.1-r1](https://github.com/strive822/zyd-vibe-lab/releases/tag/agent-desktop-v1.3.1-r1)，下载 `agent-desktop-windows.zip` 和 `SHA256SUMS.txt`。
2. 在下载目录运行 `Get-FileHash -Algorithm SHA256 .\agent-desktop-windows.zip`，将结果与 `SHA256SUMS.txt` 比对。校验通过后解压到一个新目录。
3. 在解压后的 `agent-desktop` 目录运行以下只读命令。第一条应显示 `agent-desktop 1.3.1`，第二条应返回 `ok: true` 和当前可见窗口列表。

   ```powershell
   .\agent-desktop.exe --version
   .\agent-desktop.exe list-windows
   ```

4. 如需接入 Codex，先通过 `codex mcp list` 查看已有注册。尚未注册时，从这个目录运行以下命令。注册会使后续本地会话能够读取和操作桌面应用。

   ```powershell
   $agentDesktop = (Resolve-Path -LiteralPath '.\agent-desktop.exe').Path
   codex mcp add agent-desktop -- "$agentDesktop" mcp
   ```

在新开的本地 Codex 会话里请它调用 `desktop_list_windows`，确认实际接入。撤销注册可运行 `codex mcp remove agent-desktop`，再退出相关会话并移除解压目录。

## 给 Agent：按本次授权执行

```text
安装并使用 https://github.com/strive822/zyd-vibe-lab 里的 agent-desktop。先读 agent-desktop/INSTALL.md 和 releases.json，获取固定的 Windows x64 成品并核验大小、SHA-256。将成品解压到新目录，经同意后运行 --version 和 list-windows。只有我明确要求时才注册 Codex MCP。已有同名注册时检查命令和版本，变更它前先确认。
```

仅下载时在校验后结束。报告下载、安装、MCP 注册和窗口列表调用各自的结果。桌面操作按当前任务授权执行。

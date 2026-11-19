# CodeGraph 安装与验证

## 给人：用官方 Windows 便携包

1. 已有 `codegraph` 时先运行 `codegraph --version`。本项目固定 `1.6.3`。
2. 打开 [CodeGraph 官方 v1.6.3 Release](https://github.com/colbymchenry/codegraph/releases/tag/v1.6.3)，选择 `codegraph-win32-x64.zip` 或 `codegraph-win32-arm64.zip`，并下载 `SHA256SUMS`。
3. 在下载目录运行 `Get-FileHash -Algorithm SHA256 ./codegraph-win32-x64.zip`。ARM64 请替换文件名。与官方 `SHA256SUMS` 和 [upstream.json](upstream.json) 对照，有差异就停止。
4. 解压到新目录，在解出的 `codegraph-win32-x64` 或 `codegraph-win32-arm64` 目录内运行 `.\bin\codegraph.cmd --version`，应输出 `1.6.3`。便携包自带 Node.js。可使用启动器绝对路径。需要从任意目录直接用 `codegraph` 时，将该包的 `bin` 加入用户 PATH，再开一个新终端。
5. 在需要建立索引的仓库根目录运行 `codegraph init`，用 `codegraph status` 核对文件和节点数，再用 `codegraph explore <符号名>` 验证结果。`.codegraph/` 是本地生成目录，应由该仓库忽略。

## 给 Agent：安装与 MCP 接入

```text
安装并使用 https://github.com/strive822/zyd-vibe-lab 里的 codegraph。先读该项目 INSTALL.md，下载并核验适合本机的 CodeGraph 官方固定版本。已有同版本 CLI 时复用。确认 codegraph --version，只有我要求接入宿主或给项目建索引时才执行对应步骤。
```

下载、CLI 启动、建索引和宿主接入分别验证。新增 MCP 时，只写对应宿主的 CodeGraph 服务条目。使用 stdio，启动参数为 `serve --mcp`。已在 PATH 的 CLI 可用 `codegraph install --print-config codex` 生成配置参考，把 `codex` 换成 `pi` 或 `dsh` 可查看各自格式。便携包也可用 `node.exe` 的绝对路径作为命令，依次传入 `lib/dist/bin/codegraph.js` 的绝对路径、`serve`、`--mcp`。重载宿主后，对已索引项目调用一次 `codegraph_explore`。

## 源码开发

将 [source/](source/) 复制到仓库外的任务目录。用 Node.js 22.12 至 24.x 和 npm，运行 `npm ci`、`npm run build`，然后用 `node dist/bin/codegraph.js --version` 检查本次构建。测试与可选 Rust 内核的步骤见 [上游开发说明](source/CONTRIBUTING.md)。

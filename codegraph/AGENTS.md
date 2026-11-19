# CodeGraph 维护说明

- `source/` 保存 [upstream.json](upstream.json) 固定的上游源码。保留原许可证、署名、文件内容和可执行模式。修改上游代码前读 [source/AGENTS.md](source/AGENTS.md)。
- 同步时检查 `source_commit` 和 `source_tree`，更新 `imported_tree` 与排除路径记录。当前快照仅省略一个 Python 字节码缓存，保留构建使用的解析器资源。
- 使用官方固定 Release。发布包、索引、依赖和构建产物保存在仓库之外。新增 MCP 服务配置只按用户授权执行。
- 源码开发见 [INSTALL.md](INSTALL.md#源码开发)。提交前运行根仓库的入口、源码边界和分发检查。

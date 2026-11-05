# Windows-MCP：来源与许可

- 上游 [CursorTouch/Windows-MCP](https://github.com/CursorTouch/Windows-MCP)，MIT；许可副本保留于 profile/LICENSE.md，恢复源码也保留原 LICENSE.md。
- 当前固定主线快照 `9ab92bca2772dfb53ae3ed4feb98dac22c5b3dea`，声明版本0.8.8，Python >=3.14。它是稳定 tag v0.8.8 之后的开发快照，不冒称新的官方稳定版。
- 原固定快照 `94b52cfb48076cb793e710351517fa18a316cd12`；本次前进19提交，包含将文件移动到目录时误删目录的修复及相应重叠路径回归测试。
- 上游源码不在本仓库重复保存；assets.json 固定 codeload URL、字节数和 SHA-256，restore.py 下载并校验到全新目录。
- 本地修改为隔离的安装/stdio启动入口、Python3.14.7、关闭匿名遥测与 watchdog、宿主接入说明。保留用户其他 MCP 服务与配置，本次不自动注册或启动桌面服务。

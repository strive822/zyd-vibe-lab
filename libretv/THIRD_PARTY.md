# LibreTV：来源、许可与个人修改

- 上游 [LibreSpark/LibreTV](https://github.com/LibreSpark/LibreTV/tree/92461b5e458ba45233e1cba30b09ce0bbc0fa911)，稳定版 v2.23.2，提交 92461b5e458ba45233e1cba30b09ce0bbc0fa911。上一完整基线为 v2.21.1（29cbeb3d37b4876f909a0354087a3531af0447f6）。
- AGPL-3.0-or-later。完整对应业务源码位于 source/，保留 source/LICENSE、原 README 和版权声明；提供修改后的网络服务时遵守对应源码提供要求。
- 保留 package.json/package-lock.json 的个人依赖安全修复，见 SECURITY_PATCHES.md。本地修正配置导入和旧快照迁移、片尾微调、连接防护状态、音频中断恢复及完成下载的暂存预算。逐文件哈希见 source-files.json。
- 外围 profile/、restore.py 和 runtime/ 保留个人默认源、启动/停止与环境隔离。生产启动器使用已随 Next.js 分发的 @next/env 解析既有配置，兼容引号并保留原文件。
- Node.js24.22.1固定下载来源与校验见 assets.json；Node及运行包内依赖许可独立保留。Git保存源码，生产运行包在Release。
- 本次纳入上游 v2.23.2 发布的下载、播放器和访问防护更新。保留个人依赖修复、默认源和启动入口。

- 同源设置写入用 Web Locks 串行化，也支持 IndexedDB 事务作为后备。退出时保留待写字段供下次恢复，同一字段按编辑时间合入。导入通过独立快照提交。同一下载任务在支持 Web Locks 的标签之间共享所有权，刷新后可选新保存位置继续。豆瓣推荐保留已发布的分页和回调清理。直连和代理都以重定向后的地址为清单基址，支持 HLS 变量继承。Windows 单进程代理会暂存较大的父清单变量快照。
- 父清单快照按最近使用保留最多 500 条。播放中若服务重启、换到另一个服务进程或快照被逐出，重新加载视频可取得新的引用。

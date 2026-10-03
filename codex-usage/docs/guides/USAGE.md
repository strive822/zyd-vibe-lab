# usage

Windows 三平台额度浮窗：Codex／GLM 双窗口额度、DeepSeek 余额，兼具快捷文本复制和每日提醒。

## 下载与运行

下载 [Windows x64 便携 ZIP](../../packages/usage-0.1.0-windows-x64.zip)，完整解压，再运行文件夹里的 **usage.exe**。无需安装 Python。包未做发行签名，属于个人使用候选；[校验值](../../packages/SHA256SUMS.txt)与[使用说明](../../packaging/README.md)随仓库提供。

本地解压版位于 `dist/usage-0.1.0-candidate-a67c2763ffd8/usage.exe`，根目录 `launch.cmd` 指向此候选。

![四边形态](../validation/four-edges.png)

截图来自固定测试数据，不代表用户当前账户状态。

## 使用

- 悬浮收起球展开，悬浮平台看明细；移出自动收起。拖动小球或叶片空白可吸附四边，或自由放置。
- C／G 对应平台，H／W 对应 5h／周；优先显示本家较低的已知额度。未知、旧值、故障明确区分。DeepSeek 仅显示余额，不构造余额百分比。
- 六颗常用复制球；更多文本保留其余条目。记事本中按 Ctrl+S 保存后复制内容随之更新。
- 每日提醒到点通知并保留未读铃铛，全部标为已读后清除。
- 设置是普通窗口，其他应用可覆盖；托盘提供恢复、隐藏、刷新与退出。

数据统一保存在 `%USERPROFILE%\.usage`，密钥使用 Windows 凭据管理器。包不含用户密钥、私人正文或账户数据。内部目录标识沿用旧代号，便于继续使用已保存内容。详情见 [SOP](SOP.md)。

额度正常刷新间隔：收起／展开均为 5 秒，从上一次成功响应完成后计算。失败继续按 30／60／120／300 秒退避，并遵守平台 Retry-After；鉴权失败暂停，重新配置授权后恢复。界面倒计时本地计算。

## 开发（Windows PowerShell）

```powershell
py -3.12 -m venv .venv-win
.\.venv-win\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv-win\Scripts\python.exe src/run_app.py
.\.venv-win\Scripts\python.exe -m pytest
.\.venv-win\Scripts\python.exe -m mypy
.\.venv-win\Scripts\python.exe -m ruff check src tests tools
```

`src/main.py` 同时提供冻结视觉复核入口，并被生产组件导入；不能删除。`tools/check_frozen_composition.py` 使用已保留的 `docs/evidence/m1-r4/frozen-source` 对照当前核心。

构建：在 Windows Python 3.12.10 环境执行 `tools/build_portable.py`。先从 [Python 官方来源](https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip)下载嵌入运行时到 `packaging/cache/python-3.12.10-embed-amd64.zip`，SHA-256 必须为 `4acbed6dd1c744b0376e3b1cf57ce906f9dc9e95e68824584c8099a63025a3c3`。本机副本已有此缓存；许可与构建入口在仓库中保留。

## 项目资料

[规格](../specs/SPEC.md) · [计划](../specs/PLAN.md) · [设计](../specs/DESIGN.md) · [决策](../specs/DECISIONS.md) · [数据模型](../specs/DATA_MODEL.md) · [接口契约](../specs/API_CONTRACT.md) · [测试计划](../specs/TEST_PLAN.md) · [清理记录](../history/CLEANUP.md) · [验证摘要](../validation/README.md)

源码、测试、构建入口、冻结基线及合成示例公开。真实账户证据、桌面录屏和完整本机审计资料仅留本机 `evidence`，不提交到 GitHub。

## 启动来源与已有数据

2026-10-01修复AppData重定向造成的两份配置：默认统一到`%USERPROFILE%\.usage`，首次完整复制既有配置、正文和提醒账本并保留旧目录。Windows凭据引用、六个绑定和账号身份不变。重复双击launch／usage.exe通过文件锁和恢复协议只唤回当前实例；连接确认失败也不会另开未知数据窗口。

已有记事本标签页仍指向旧目录的正文：升级后请从当前“快捷文本”窗口重新打开正文再编辑；旧文件保留为备份，不会自动覆盖新目录。

## 2026-10-03 登录启动修复

当时候选 `799ba808dfca`。已修复MSIX私有注册表覆盖层导致设置读写与登录会话不一致的问题；便携版登记当前usage.exe与日常数据目录。保存时通过既有Explorer桌面写入并核验，仅操作本应用的当前用户启动项，构造和读取不会登记。真实桌面执行和第二次启动恢复已检查；真实重启登录仍待用户确认。移动或更新便携目录后，请重新保存开机启动设置。

# AI 额度悬浮窗 · 像素能源控制器

Windows 常驻额度窗口，显示 Codex、智谱 Coding Plan 的 5 小时与周剩余额度，以及 DeepSeek 分币种余额。主窗、设置与菜单共用像素风格；内容过多时滚动。

## 构建与运行

在 **Windows 命令提示符**执行，无需另装 .NET SDK：

```bat
cd /d "E:\pi always\1a\redesign"
build.bat --test-only
build.bat --stage-only
```

构建使用 Windows 自带的 .NET Framework C# 编译器。`--test-only` 只编译并运行测试；`--stage-only` 生成独立候选，输出 `bin\QuotaWidget.staged-数字-数字.exe` 路径。

无参数的 `build.bat` 在编译、测试通过后尝试替换 `bin\QuotaWidget.exe`。如果程序被占用，返回退出码 3，保留暂存产物且不终止进程。构建会尝试生成 `.next.exe` 便捷副本；验收始终使用输出的明确候选路径。

当前保留候选和是否已验收见 [UAT.md](UAT.md)。运行正式程序：

```bat
bin\QuotaWidget.exe
```

## 日常使用

- 右键或 Shift+F10 打开菜单；托盘左键隐藏或恢复；菜单“退出”结束程序。
- 额度显示剩余百分比、重置时刻及倒计时。DeepSeek 各币种独立显示，不相加或换汇。
- 默认每 10 秒检查；账号独立刷新，同账号同时最多一个请求。失败保留旧值并标过期，手动刷新不能越过 429 冷却。
- 设置支持 Codex 登录路径、智谱多账号、DeepSeek Key、10–3600 秒刷新间隔和置顶。Key 输入遮蔽；保存失败保留草稿并提示；取消丢弃草稿。
- 设置窗位于主窗上方。空间不足时调整两窗的位置与可滚动区域，关闭设置后恢复主窗位置。当前不提供透明度设置。
- 主窗底栏“最近请求结束”只表示请求完成时间，各账号的数据有效性单独显示。
- 修改名称等外观设置复用状态；换凭据取消旧请求并清空旧缓存；隐藏账号停止启动新请求。

## 配置与认证

有效配置为本目录的 `config.json`；保存保留 `config.json.bak`。首次启动可在界面配置。损坏 JSON 或错型结构会停止刷新和保存，修复后须重启。智谱稳定 ID 和账号扩展字段随账号保留。

Codex 只读用户目录下 `.codex/auth.json` 或指定文件，不自行续期或写回。401 时仅在重读发现凭据改变后重试一次，失效时需在官方客户端登录。智谱与 DeepSeek 使用各自 Key。

配置包含本机明文凭据，不应提交仓库。`local-backup/` 仅保留早期版本的配置和备份，应用不会自动读取该目录。

## 预览与排查

对构建输出的候选添加 `--preview`，使用合成配置，不读取真实凭据、不请求服务、不修改开机自启。`--mock` 同样隔离。

可选参数：

- `--preview-scenario=normal|stale|error|empty|no-accounts|balance|many|partial|login|limited|long|extreme|unknown|loading|refresh-error|config-error`，每次选一个。
- `--preview-scale=1|1.5|2`：诊断布局倍率，不代表系统 DPI 已验收。
- `--preview-instance=<GUID>`：独立模拟实例。
- `--settings-demo`、`--menu-demo`、`--submenu-demo`：打开对应入口。

设置演示可选择 `save-error|settings-focus|settings-bottom|config-error|config-error-bottom`。`save-error` 展示合成错误，真实保存失败由回归测试覆盖。

构建后运行 `bin\QuotaTests.exe --render` 可按需重新生成界面诊断图，日常目录不保存旧截图。只读在线检查源码为 `tests/LiveSmoke.cs`，需显式传入 `--config`；离线测试不能证明当前服务连通。

## 维护资料

| 文件 | 用途 |
| --- | --- |
| [SPEC.md](SPEC.md) | 产品行为、功能边界 |
| [DESIGN.md](DESIGN.md) | 当前布局、颜色与交互规范 |
| [DECISIONS.md](DECISIONS.md) | 架构决定及取舍 |
| [DATA_MODEL.md](DATA_MODEL.md)、[API_CONTRACT.md](API_CONTRACT.md) | 配置、状态与 Provider 契约 |
| [PLAN.md](PLAN.md) | 当前进度与交付门槛 |
| [TEST_PLAN.md](TEST_PLAN.md) | 需求到测试的对应及运行方法 |
| [UAT.md](UAT.md) | 当前候选、复审结论与未验证项 |

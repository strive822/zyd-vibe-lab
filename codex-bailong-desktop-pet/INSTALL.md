# 下载、准备环境与使用

这是 Windows x64 / Python 3.12 的个人多平台白龙桌宠源码版，目录名 `codex-bailong-desktop-pet`。源码、依赖清单、字体许可、素材来源和启动脚本在同一项目内；不依赖其他项目。

## 1. 完整获取与核验

从 https://github.com/strive822/zyd-vibe-lab 完整克隆，或下载本项目的 `delivery/codex-bailong-desktop-pet.zip`，同时取得 `delivery/SHA256SUMS.txt`、`delivery/FILES.json`。下载入口如下，三份文件取自同一提交版本。下载只保存文件，不运行安装器。

```text
https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/codex-bailong-desktop-pet/delivery/codex-bailong-desktop-pet.zip
https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/codex-bailong-desktop-pet/delivery/SHA256SUMS.txt
https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/codex-bailong-desktop-pet/delivery/FILES.json
```

```powershell
Get-FileHash .\codex-bailong-desktop-pet.zip -Algorithm SHA256
```

将结果与 SHA256SUMS.txt 比较，再检查 ZIP 不含绝对路径、`..`、链接或重复名称，解压到新目录。FILES.json 提供每个源码文件的 SHA-256；逐项核验。已有项目、账号、设置和素材不覆盖。

## 2. 项目内依赖

确认已有 Python 3.12，缺少时先向用户说明运行时的下载与安装范围。不要改变系统 PATH，不全局安装包。在项目根目录执行：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-enhanced.txt
```

## 3. 动画素材

Git 和源码交付 ZIP 不包含大型角色动画，保留 [NOTICE.md](NOTICE.md) 和 [上游素材说明](docs/upstream/ASSETS.md)。优先复用用户已下载的白龙播放素材：

```powershell
.\.venv\Scripts\python.exe tools\import_installed_assets.py --source '已有白龙目录'
```

没有已有素材时，在用户已授权准备运行环境后执行：

```powershell
.\.venv\Scripts\python.exe tools\prepare_assets.py --download
```

该命令只下载固定的官方 v0.9.3 Windows 容器（约740MB），校验 SHA-256 `d31a35f3c2b7214c408843853bd6f4d9e73f61935a49e22e06b64efec45b1915`。官方 ZIP 内是安装器，脚本使用已声明的 PyInstaller 库将内嵌 payload.zip 作为数据读取，只取播放清单和引用的动画，临时文件自动清理，不执行安装器或安装其程序。来源和哈希固定在 `tools/prepare_assets.py`。也可用 `--archive` 提供同一已下载 ZIP。已有动画或不匹配的清单会保留并拒绝覆盖；源码自带且与容器完全一致的清单原样保留，仅补齐缺失动画。上游撤回该版本或哈希不符时停止，不换未知镜像。

## 4. 启动与验证

双击 `启动白龙.cmd`，或执行：

```powershell
.\.venv\Scripts\python.exe app\enhanced.py --settings
```

确认人物和卡片实际显示；中间胶囊悬浮展开正常卡片，右侧额度胶囊悬浮展开详情，离开后收回；左侧快捷按钮仍为点击。设置中的快捷动作可选择 Codex。聊天入口已移除。快捷方式图标使用项目内 `app\branding\bailong.ico` 的官方白龙娘头像；目标保持源码启动入口。

在“设置 → 连接 → 其他平台账号”连接本人账号。保存后表单收起，点“管理”修改。顶部平台菜单切换额度与 Token，日报“模型”可按平台筛选。详细数据口径和限制见 [多平台账号说明](docs/多平台账号说明.md)。GLM、DeepSeek、WorkBuddy、Antigravity 额度正常每5秒刷新；限流与失效会退避，失败保留有效旧值。Token 获取失败不影响额度。

后台运行不等于账号成功；分别核验余额/积分/比例与 Token 的连接状态。DeepSeek 用量需单独在官方页面登录，API Key 仅能查余额。WorkBuddy 云端会话未提供 Token 时显示“未提供”，不按积分估算。Antigravity 需原应用登录并打开项目。

账号密钥、浏览器登录状态和统计缓存只保存在 `%LOCALAPPDATA%\BailongEnhanced`，Windows DPAPI 加密凭据不可直接迁移到其他用户。不要上传、导出或代填密钥；不自动开启自启动。原有内置更新入口面向上游正式版本，安装上游版本会替换本项目的自定义扩展，应从本项目源码维护。

## 5. 维护检查

```powershell
$env:PYTHONPATH='app'
$env:QT_QPA_PLATFORM='offscreen'
.\.venv\Scripts\python.exe -m unittest test_provider_accounts test_provider_tokens test_provider_ui test_token_charts test_daily_report test_quota_summary_data test_island test_refresh_flow -q
.\.venv\Scripts\python.exe -m compileall -q app tools
```

真实登录与原生桌面行为另行验证，不能用合成测试冒充。历史上游测试中含已移除的聊天用例及依赖开发素材的用例，不能声称全部历史测试均可在干净环境通过。卸载源码目录前先退出桌宠；保留本机用户数据，清理数据须用户明确要求。

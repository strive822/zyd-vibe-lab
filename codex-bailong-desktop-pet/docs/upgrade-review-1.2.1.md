# v1.2.1 升级候选终审

状态：候选于2026-10-29完成隔离合并、检查和独立复审；用户于2026-10-30明确“继续”，已完成终审确认并更新源码运行版。下文保留审查范围与回滚依据。

## 目标与范围

- 合入原作者8d86342的v1.2.1累计更新：卡片共有模块连续过渡、悬停提示、托盘额度、DPI恢复，以及累计迁移恢复和标准Windows启动入口修复。
- 保留五平台额度和真实金额/积分单位、独立Token曲线与模型筛选、Codex专属额度对比、无聊天及说明入口、中间/右胶囊悬浮、左快捷点击、通知默认关闭。
- 终审前运行源为f880e1d/v1.1.0，交付仓库为3e6ca336；获确认后源码运行版升级到v1.2.1。账号、安装位置和素材目录不迁移，本次不运行真实安装器或托盘历史清理。

## 涉及文件与顺序

先合并窗口与显示模块，保留compact_bubble/daily_report/desktop/desktop_core/desktop_settings中的个人扩展；再核对windows_entries、deployment_state、program_location、program_update_apply、tray_history；之后补回归、原生隔离启动、独立只读复审。所有写入只发生在本候选worktree及其隔离测试目录。

## 验证结果

- 两组相关回归299+397=696项通过，app/tools编译通过。角色播放依赖的32个轻量输入逐项SHA-256匹配后，只读硬链接到本候选；未写入原素材。
- C#安装桥6项stage-only校验通过：首次卡片、既有素材/设置保留、篡改、摘要、越界和大小写冲突；没有部署真实安装。
- 新上下文只读复审发现并修复一个P2：周额度异常入口用Codex单平台快照覆盖模型页汇总。现统一使用report_snapshot()。新增断言在修复前可复现失败，修复后54项相关检查通过；独立复审再次确认闭环。
- 合成数据的Windows原生窗口启动成功且无异常，预览位于.local/review/bubble-preview.png；不是本机真实账号证明，也未宣称人工悬浮/切页已验收。
- 隔离offscreen动画采样5秒：累计CPU1.703秒、RSS81.1MiB、读取0.25MiB；无后台账号监测、无真实托盘注册、decode_error=null。该结果不能表示真实整机占用、帧率或相对旧版性能提升。

原隔离worktree中的本地证据（不进入交付包）：.local/platform-tests.log、.local/broad-tests.log、.local/review/model-entry-before-fix.log、model-entry-after-fix.log、bootstrap-result.json、performance.json。

最贴近的复验入口（PowerShell，工作目录为本候选；使用现有项目内Python）：

```powershell
$env:PYTHONPATH='app'
$env:QT_QPA_PLATFORM='offscreen'
$env:BAILONG_ISOLATED='1'
$env:LOCALAPPDATA="$PWD\.local\validation-state"
$env:CODEX_HOME="$PWD\.local\empty-codex"
& 'E:\Github项目\codex-bailong-desktop-pet\.venv\Scripts\python.exe' -m unittest test_provider_ui test_daily_report test_quota_summary test_shared_card_transition -q
```

通过信号：54项检查末尾为OK；非零退出或FAILED均为未通过。完整两组的模块清单保留在本轮工具记录中，日志提供实际通过结果。

## 人工终审的影响面

| 位置 | 触发条件 | 影响与保护 |
| --- | --- | --- |
| [windows_entries.py](../app/windows_entries.py) | 主动配置自启动、迁移或升级受管安装 | 标准COM写lnk；只退役严格识别的旧VBS/快捷方式，其他同名入口报错保留。 |
| [deployment_state.py](../app/deployment_state.py) | 受管安装失败后的入口恢复 | 快照支持旧/新Codex联动入口；恢复范围仍限当前应用清单。 |
| [program_location.py](../app/program_location.py) | 用户主动迁移程序位置 | 新位置就绪receipt改放到新exe同目录；先确认就绪再提交入口。 |
| [tray_history.py](../app/tray_history.py) | 已提交的受管冻结安装成功启动 | 精确匹配本应用路径/UID，先备份后处理历史及排序；源码和BAILONG_ISOLATED=1直接退出，不改真实注册表。 |
| 原生窗口/解码模块 | 远控、多屏DPI变化、连续过渡和中途退出 | 已做合成/隔离回归；真实Explorer托盘恢复、多屏及特定远控软件仍需用户现场终审。 |

权限、安全边界、迁移和启动入口按用户当前规则必须人工终审。本轮已获得部署/同步/上传确认；这不是对真实多屏或Explorer行为已完成验收的承诺。

## 回滚路径

部署前已在用户数据目录留存settings.json、偏好/路径配置及现有桌面入口，附逐文件摘要。需要回退时先退出桌宠，将源码回到已保留的personal/pre-v1.2.1（f880e1d/v1.1.0），按需恢复备份设置与入口并按原快捷方式启动。配置、凭据、Token库和动画均留在原位置，不通过清空数据恢复。已部署的受管安装继续使用安装管理的上一版本及其入口快照；本源码升级不运行真实安装器或目录迁移。

## 清理

只读复审没有产生额外文件。合成截图与最小验收报告已归入.local/review；播放输入保留供终审复验。对本次新建的字节码、隔离测试状态和安装桥暂存执行了边界/链接检查，但删除被自动安全检查拒绝（blocked by policy，无更具体原因），因此仍保留，不会进入Git或交付包。未触碰现用环境、账号数据和旧回退版本。

## 2026-10-30 实际运行验证

运行时版本为1.2.1，notifications=false，decode_error=null。GLM、DeepSeek与Antigravity额度状态ok，其中Antigravity使用cloud来源；WorkBuddy初次返回authentication；用户重新登录后，已观察到state=ok且返回真实积分指标，四个平台额度均查询成功。旧错误日志10799字节最后修改于2026-10-29，启动后未新增；不把历史日志当作本轮错误，也不删除用户诊断记录。

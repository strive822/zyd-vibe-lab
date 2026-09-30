# 数据模型

状态：M2–M5 领域、存储、设置及提醒账本已实现；schemaVersion 1。六常用位为 2026-10-01 用户授权的加法修订，原 0–3 位保留原身份。更新：2026-10-01。

## 1. 核心实体

| 实体 | 关键字段 | 约束 |
| --- | --- | --- |
| AppSettings | schemaVersion、language、dockPolicy、motionMode、refreshPolicy、lastPlacement | 版本化；位置用设备与相对锚点表示，不只保存裸像素 |
| Account | id、provider、displayName、connectionMode、credentialRef、enabled | 每 provider 最多一个；credentialRef 仅是引用 |
| UsageSnapshot | accountId、sourceKind、windows、balances、sourceObservedAt、lastSuccessAt、lastAttemptAt、status、error | 最后成功数据与最近失败分别保存 |
| QuotaWindow | id、sourceBucketId、label、durationMinutes、usedPercent、remainingPercent、usedAmount、totalAmount、unit、recoveryKind、nextRecoveryAt、recoveryAmount | 可选字段可空；缺值不等于零 |
| Balance | currency、total、granted、toppedUp、isAvailable | decimal 字符串或 Decimal；不使用 float 处理钱 |
| BenefitRule | id、provider、version、timezone、effectiveFrom、effectiveTo、modelScope、peakIntervals、holidayPolicy、benefitKind、factor、sourceUrl、verifiedAt | 仅常态规则；限时活动另类且首版不加载 |
| HolidayCalendar | id、region、year、dates、coverage、sourceUrl、verifiedAt | 区分日历不存在与当天不是假日 |
| Snippet | id、name、description、iconId、contentPath、sortOrder、favoriteSlot、lastLoadedAt、contentStatus | ID 不因改名改变；正文是独立文件 |
| Reminder | id、title、localTime、timeZonePolicy、enabled、createdAt | 每日重复；使用本机时区或未来明确指定时区 |
| ReminderOccurrence | reminderId、localDate、scheduledAt、state、claimedAt、deliveredAt、acknowledgedAt | reminderId + localDate 为幂等键 |
| WidgetPlacement | monitorKey、edge、edgeOffsetRatio、floatingPosition、displayMode | 丢失显示器时回落到当前可见工作区 |

关联：一个 Account 产生一组最新 UsageSnapshot；每份快照包含多个 QuotaWindow 或 Balance。Snippet 通过稳定 ID 绑定功能球。Reminder 每天派生一个 Occurrence。BenefitRule 是显示时段规则，不修改快照。

## 2. 状态与空值

数据状态建议：未连接、加载中、新鲜、旧数据、暂时离线、需重新授权、限流等待、响应不兼容。加载可以叠加最后成功数据，不先清空界面。

恢复类型建议：

- fixed_reset：已知的整窗口重置。
- rolling_replenishment：已知的下一次额度补回。
- unknown：有额度，但恢复语义不明。
- not_applicable：例如 DeepSeek 余额，没有配额重置。

remainingPercent 只有在源值语义明确时派生。usedPercent → 100 - usedPercent；异常值保留诊断并标异常，不生成漂亮但错误的百分比。多个桶/窗口分别保留，不求平均。

## 3. 时间

- 绝对事件内部使用有时区的 UTC 时间；接口 Unix 秒/毫秒必须在适配器内明确转换。
- 界面绝对时间按用户显示时区；优惠规则固定 Asia/Shanghai，并在详情标明 UTC+8。
- 悬浮/动画/请求超时使用单调时钟，避免系统校时触发乱序。
- 倒计时依据当前绝对时间重算；休眠恢复和系统时间改变后整体重算。
- 每日提醒使用本地墙上时间；DST 缺失时段顺延到当日第一个有效时刻，重复时段只提醒一次，具体行为列入测试。
- 日常时段使用左闭右开区间，例如开始时刻即进入，结束时刻即退出。
- 节假日覆盖未知时，受其影响的时段状态为“待核验”，不能直接判定优惠关闭或开启。

## 4. 收起球的派生状态

额度概况使用用户关注的窗口，默认可取同一服务各可用窗口剩余百分比的最小值；这只是该服务的紧张程度，不表示三家合并额度。无有效百分比就显示未知样式。

DeepSeek 只有余额状态点，不画虚构余额百分比。低余额阈值按币种设置，未设置时只表达是否有余额以及数据新鲜度。

信息优先级：需处理的授权/故障 → 未读提醒 → 低额度/低余额 → 正常状态。GLM、DeepSeek 优惠各保留固定标记，不能混成一个“全平台 ×2”。半球布局须把所有关键编码投射到露出的部分。

融合方向沿用同一收起信息语义：两家额度概况、余额状态、分别编码的优惠与需处理事项。轮廓可以不同，不能因选视觉方向改变业务含义。最终视觉编码在方向选择后收敛。

## 5. 临时交互状态

WidgetViewState 建议包含 hoverProvider、focusedProvider、detailPinned、activeAction、dockTransitionProgress、detailTransitionProgress、interactionLocks。它只保存当前交互，不作为服务快照写入磁盘。

概要与明细读取同一个 accountId 对应的 UsageSnapshot。切换悬浮不重新请求数据；它只切换被呈现的已有信息。一个时刻最多展示一个平台的内部时间明细，异步数据返回仍按账号和请求世代更新，不能因焦点切换而串家。结束会话不恢复一个悬空的 hoverProvider。

明细的显示/关闭计时和整个浮窗的收起计时相互独立；详情锁、菜单锁和键盘焦点可阻止整窗收起。UI 状态不改变额度、更新时间和优惠判断。

### 固定内部时间槽（已选的融合方向）

RecoveryFocus 是 UsageSnapshot 的派生视图，包含 accountId、windowId、recoveryKind、recoveryAt、sourceFreshness、displayMode。M1 用户已修订默认选择：Codex／GLM 的 5h／周四个窗口取最低已知剩余，同值先 5h、再 Codex；恢复事件承担说明，未知不派生倒计时。DeepSeek 余额不参加百分比排序或产生配额恢复事件。

悬浮或键盘聚焦某个平台时，时间槽呈现该家两种窗口及更新时间；退出且未固定时，返回四窗口最低已知剩余。此切换不改变下方概要或重新请求数据。缺失事件时显示“恢复时间未提供”，全部到点未核验时显示“等待更新”；旧数据显式标旧，不暗示服务已实际恢复。

融合稿保留 B 的窗口对照概要，采用固定时间槽；不再实现 A/B 的外接注释。摘要与时间槽始终读取同一份源快照。

### CountdownPresentation

这是视图派生值，源模型仍只保留真实时间：windowId、recoveryAt、remainingSeconds、unitMode（DHM/HMS）、fields、status、revision。以同一个 now 计算两个窗口的剩余秒数；正值向上取整秒并夹到零。remainingSeconds >= 86400 使用 DHM，否则 HMS；长模式省略不足一分钟的秒，不声称分钟精度以外的值。

fields 中每项包含 unit、整数 value、格式化数字与固定槽位。首项不补零，后两项两位；时间未知的 status 是 unavailable，不能派生0。到点状态为 awaiting_confirmation，数字可为0时00分00秒但快照额度不改变。

渲染状态单独保留上一次完整 presentation 和当前过渡进度。模式相同逐位匹配，模式不同整组过渡；不得将旧 value 与新 unit 拼接。隐藏/减少动态效果/账号切换/时钟跳变可以取消过渡；显示时采用当前计算结果，不积压历史帧。默认焦点事件到点后保留待确认，取得新成功快照后才重新判断，不能因本地计时归零就宣称恢复。

## 6. 本地存储建议

应用数据位于 Windows 当前用户的 LocalAppData 下独立目录；正式目录名随产品命名确定。

| 文件/位置 | 内容 |
| --- | --- |
| config.json | AppSettings、账号引用、Snippet 元数据、Reminder 定义 |
| snapshots.json | 最后成功快照与其时间；不保存原始授权响应 |
| reminder-ledger.json | 去重和未读状态；建议只保留近期 30 天 |
| snippets/{id}.txt | 用户主动保存的 UTF-8 纯文本正文 |
| Windows 凭据存储 | GLM / DeepSeek 密钥或经验证可用的授权引用 |
| logs/ | 脱敏运行诊断；不记录预存正文、剪贴板内容或密钥 |

同目录原子替换与上一版备份防止半写入。只有成功保存配置后 UI 才报告保存成功。遇到更高 schemaVersion 时只提示不兼容，不覆盖原文件。账号解绑清除相关凭据引用和缓存，不影响其他服务。

## 7. 提醒一致性边界

先持久化当日事件和待通知状态，再尝试送达；崩溃后可显示未读并避免重复弹窗。系统通知“已提交”不等于用户“已看到”。首版承诺应用层去重与可恢复未读，不承诺跨崩溃的严格一次送达。

## 8. 迁移边界

这里只定义新项目 v1 数据。没有旧项目迁移、旧路径兼容或历史配置导入任务。未来扩展使用 schemaVersion 和明确迁移函数，不在界面中临时猜测旧结构。

## 9. 已实现的物理存储

当前目录为 `%LOCALAPPDATA%\Duizhaoye`。`config.json` 顶层 `accounts` 保存三平台本地 UUID、名称、连接模式、凭据引用与启停；`settings.lastPlacement` 保存设备键、边、相对位置、自由朝向与固定展开，`settings.motionMode` 保存 full／reduced。`snapshots.json` 以 accountId 索引最后成功快照，Decimal 写成字符串；实时的 lastAttemptAt／status／error 放在独立 ProviderState 中，启动时有缓存标旧并重新请求。

GLM／DeepSeek 换密钥时生成新的本地账户身份，避免旧账号缓存或晚到响应串入；配置原子提交失败会清理临时凭据并保留旧配置／旧密钥。Windows 凭据目标限定在 Duizhaoye 命名空间，没有文件明文回退。

M4：`config.json.snippets` 保存 ID、名称、说明、图标、派生路径、顺序和常用位；正文为 `snippets/{id}.txt`。载入时间／状态在运行时，不把正文复制到配置或日志。最大正文 1 MB，支持 UTF-8 和 UTF-8 BOM；空、丢失、无法读取、错误编码与超限分别表达。Win32 `CF_UNICODETEXT` 保留字符、空格、制表符及逻辑换行，仅将剪贴板换行规范为 CRLF。

`favoriteSlot` 现为 null 或整数 0／1／2／3／4／5，每位最多绑定一个稳定 ID；重新绑定只释放该位的旧绑定，不删除正文。ID 必须是规范小写 UUID，避免 Windows 大小写路径产生别名；派生文件拒绝符号链接、目录联接和共享硬链接。原四位配置无需迁移，原 ID／顺序／正文保持；新增第五／第六位显式绑定。旧四位候选不能读取槽位4／5，不应再用它打开已配置新增两位的数据。

M5：`config.json.reminders` 保存规范 UUID、title（最多80字）、HH:mm、system 时区策略、enabled、createdAt。`reminder-ledger.json` 以 reminderId／localDate 去重，先 claim 持久化再提交系统通知；submitted／deliveredAt 只表示 API 提交，acknowledgedAt 必须来自明确已读操作。保留近30个本地日，时钟回拨不删除未来日期的已领取事件。DST 重复时段取首次有效时间，缺失时段顺延到当日首个有效时刻，整个日期不存在则不造事件。

账户切换原子提交后，旧身份凭据／缓存若暂时清理失败，记录 `accountCleanup` 的 accountId／credentialRef，稍后重试；清理仅允许本应用非当前账号的引用。已提交新账户不会因旧引用清理失败而误报保存失败。

M6：`logs` 仅允许事件、平台、分类错误、时间、错误类型和末级文件名／行号，单文件256 KB并保留一次轮转；不记录异常正文、请求响应、密钥、文本或剪贴板。备份恢复必须显式执行，保存损坏的当前文件再替换，并拒绝覆盖更高 schemaVersion；不自动恢复或改动账本／凭据。

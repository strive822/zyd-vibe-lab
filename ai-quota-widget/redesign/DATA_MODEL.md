# 数据模型契约（本机配置与运行状态）

版本：2026-09-25。依据 [SPEC.md](SPEC.md) FR-02、FR-03、FR-05～FR-08、FR-12，[PLAN.md](PLAN.md) S1 / AC-02、AC-03、AC-12，以及 [DECISIONS.md](DECISIONS.md) ADR-002～ADR-005。本文描述现有 WinForms 应用；没有数据库、建表或服务端用户表。

## 1. 持久化范围和归属

唯一持久化的业务配置为应用目录的 `config.json`（实际路径由 `AppConfig.FindConfigPath()` 确定）。Codex 客户端的 `auth.json` 属于客户端，本应用只读。注册表中的当前用户开机自启项属于系统集成设置，不是业务数据库。额度、余额、错误、请求代次、冷却期限和请求状态仅在进程内，重启后重新查询。

下表的“缺失”表示 JSON 属性不存在；除特别说明外，字段可缺失而不可用 JSON `null` 表示有效值。加载旧配置时，字符串字段只接受字符串、布尔字段只接受布尔，否则使用默认值；整数字段沿用 `Convert.ToInt32` 的可转换输入（包括数字字符串、布尔值和按该方法取整的浮点数），转换失败才使用默认值，随后按字段范围限制。保存后的已知字段使用规范类型。**对象、数组或账号行**类型不匹配视为配置损坏，不得覆盖原文件。

| JSON 路径 | 类型、缺失时默认值 | 约束与归属 |
| --- | --- | --- |
| `refreshIntervalSeconds` | 整数，`10` | 加载和保存限制为 10～3600 秒；每账号独立到期。 |
| `zaiAuthorization` | 字符串，`raw` | 加载时仅 `bearer` 保留，其余归一为 `raw`；用于全部智谱账号的请求头。 |
| `warnThreshold` | 整数，`90` | 旧配置兼容字段；加载时限制为 5～100，当前 UI 不提供编辑，也不决定 25%/10% 色阶。 |
| `accounts.codex` | 对象，可缺失 | 单一配置槽位；对象中的未知字段保留。 |
| `accounts.codex.enabled` / `visible` | 布尔，均为 `true` | 前者决定是否纳入调度，后者决定是否显示和启动新查询。 |
| `accounts.codex.name` | 字符串，`OpenAI Codex` | 显示名称，不作为账号身份。 |
| `accounts.codex.authJsonPath` | 字符串，`""` | 空值表示使用客户端默认登录文件；绝不写该文件。 |
| `accounts.zhipu` | 对象数组，已存在配置中缺失时为 `[]` | 可有多个账号；首次**完全缺少配置文件**时，内存中预置一个空智谱账号供设置。每行必须为对象。 |
| `accounts.zhipu[].id` | 非空唯一字符串，旧行缺失时生成 | 持久身份。加载时仅在内存修复缺失、错型、空白和重复 ID；首次成功保存才写盘。同名、换 Key、删除或调序不转移 ID。 |
| `accounts.zhipu[].visible` | 布尔，`true` | 隐藏仅停止该账号的新请求。 |
| `accounts.zhipu[].name` | 字符串，`""` | 空名称显示为“智谱”“智谱 2”等；显示名不是身份。 |
| `accounts.zhipu[].apiKey` | 字符串，`""` | 本机明文配置；设置输入遮蔽，日志和报告不得输出。 |
| `accounts.deepseek` | 对象，可缺失 | 单一配置槽位；未知字段保留。 |
| `accounts.deepseek.enabled` / `visible` | 布尔，分别为 `false` / `true` | 分别控制启用和显示。 |
| `accounts.deepseek.name` / `apiKey` | 字符串，分别为 `DeepSeek` / `""` | 名称仅供显示；Key 本机明文保存。 |
| `ui.left` / `top` | 整数，均为 `-1` | `-1` 表示由窗口布局决定初始位置。 |
| `ui.topMost` | 布尔，`true` | 当前置顶偏好。 |
| `ui.designVersion` | 保存时为整数 `4` | UI 兼容标记；加载时不作为业务字段。旧 `ui.opacity`、`mode`、`collapsed`、`autoCollapseSeconds` 在保存时移除。 |

## 2. 内存模型和身份

`AppConfig.LoadError` 是加载来源错误标记，不序列化；设置草稿 `Clone()` 必须保留它。来源损坏后，即使用户在外部修复文件，旧草稿仍不可保存，须重新加载。`AppConfig.ConfigPath` 是进程内当前配置路径，不属于 JSON。

智谱每个账号的 `SourceFields` 深拷贝该**账号行**的未知嵌套字段；保存时以当前账号对象为单位合并已知字段。根、`accounts`、Codex、DeepSeek 与 `ui` 的未知字段从保存时重新读取的磁盘 JSON 合并。删除账号会删除该账号的扩展字段；调序、改名及换 Key 不会把扩展字段交给别的账号。

`AccountRequest` 是一次工作线程请求的不可变快照：`Key` 为 `codex`、`deepseek` 或 `zhipu:<id>`，并携带 Provider、Key/登录文件路径、智谱授权方式。`AccountState` 保存当前身份、额度/余额、有效性、最近成功与完成时间、下次到期、冷却期限及失败计数。结果只能在 UI 所有者线程、且账号键和请求代次仍有效时应用；换凭据或 Codex 实际账号后清除旧身份的缓存。

额度窗口使用 `WindowKind`、正整数 `DurationSeconds`、0～100 的有限 `UsedPercent` 和可空的秒级 Unix `ResetAt`。界面只转换一次为剩余百分比。余额按币种分别使用 `decimal Total` 和可空 `decimal Granted`；不相加、不换汇。未知重置时间与赠送余额保持未知，不伪造数值。

## 3. 校验、保存与失败边界

读取配置不改写磁盘。JSON 根必须是对象；已存在的 `accounts`、`accounts.codex`、`accounts.deepseek`、`ui` 必须是对象，`accounts.zhipu` 必须是对象数组。损坏时 `LoadError=true`，停止普通刷新与保存，保留原文件并提示修复后重启。首次缺文件可创建。

保存前重新读取并验证当前磁盘结构，在原对象上更新已知字段；先写同目录 `config.json.tmp`，已有配置使用替换并保留 `config.json.bak`，首次保存使用移动。只有替换/移动成功才报告保存成功；失败保留原配置和可编辑草稿，并尝试清理可能含 Key 的临时文件，不得在 UI 中宣称已持久化。没有跨多个文件或进程的数据库事务；备份与临时文件是本机文件保存边界。

凭据文件、Key、Token、原始响应与真实账号标识不能进入界面错误、日志、截图或测试报告。用户 A / B 的远程数据隔离由各 Provider 的凭据及本机账号身份绑定；本应用没有应用级多用户登录或授权系统。

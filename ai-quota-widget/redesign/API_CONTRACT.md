# 接口契约（内部调用与只读 Provider 查询）

版本：2026-09-25。依据 [SPEC.md](SPEC.md) FR-01～FR-08、FR-12，[PLAN.md](PLAN.md) S1～S3，以及 [DECISIONS.md](DECISIONS.md) ADR-002～ADR-005。本文记录当前源码的调用边界和归一化结果；第三方接口的可用性须另做在线验证。

## 1. 对外接口范围

本应用是本机单进程 WinForms 程序：**没有供前端或第三方调用的 Endpoint、HTTP Method、请求/响应 JSON、应用级 HTTP 状态码、会话认证或用户授权**。设置窗口直接调用本机配置层；刷新协调器通过 Provider 层发出只读请求。不得凭空增加服务端 API、双错误格式或兼容字段。

## 2. 本机内部调用

| 调用（等效于本机 Endpoint） | 方法、必需输入与可空项 | 输出及失败 | 认证/授权 |
| --- | --- | --- | --- |
| 加载配置 | `AppConfig.LoadFromPath(string path)`；路径必需 | `AppConfig`；缺文件返回可编辑默认配置，损坏返回 `LoadError=true`，不写盘 | 当前 Windows 用户的文件读取权限；无应用登录 |
| 保存设置 | `AppConfig.Save(AppConfig cfg)`；非空草稿必需 | `bool`：仅持久化成功为 `true`；损坏来源、当前磁盘结构错误或文件操作失败为 `false`，UI 保留草稿并提示未保存 | 当前 Windows 用户的文件写入权限；`LoadError` 来源禁止保存 |
| 对账与刷新 | `RefreshCoordinator.Reconcile(AppConfig)`、`RefreshDue()`、`RefreshNow([string key])`；配置必需，指定账号键可选 | 无 HTTP 响应；状态通过 `Accounts` 和变更回调提供，取消不计失败 | 仅启用且可见账号可启动；同账号至多一个在途请求；429 冷却不能手动绕过 |
| 工作线程查询 | `FetchProvider(AccountRequest request, CancellationToken cancellation)`；两个参数必需；请求中的 Key/Provider 必需，Key 或路径按 Provider 选用，未用项可为 `null` | `FetchResult`；取消、错误和成功经统一模型传回 UI 线程，旧代次结果丢弃 | 凭据取自不可变快照，Codex 登录文件只读；没有跨账号缓存复用 |
| 开机自启 | `AppConfig.SetAutostart(bool enable, string exePath)`；两个参数必需 | `bool`：写入调用未抛异常为 `true`，写入异常为 `false`；菜单另行读取并核对勾选状态，不因点击盲目翻转，失败时显示安全提示 | 仅正式模式可操作当前用户的 HKCU Run 项；预览禁用 |

`AccountRequest.Key` 使用 `codex`、`deepseek`、`zhipu:<稳定 id>`；`Provider` 为 `codex`、`zhipu` 或 `deepseek`。Codex 使用 `AuthJsonPath`，智谱/DeepSeek 使用 `ApiKey`，智谱另使用 `AuthorizationScheme=raw|bearer`。请求体均为空。设置保存不返回 HTTP 状态码；文件失败不能伪装为成功。

### 归一化响应类型

`FetchResult` 的 `Ok`、`Canceled`、`Stale`、`RequiresLogin` 为布尔；`StatusCode` 为整数（`0` 表示无 HTTP 响应），`Error`、`Warning`、`AccountIdentity` 为可空字符串，`RetryAfterUtc` 为可空 UTC 时间。`Windows`、`Balances` 为非空列表，元素分别是 `QuotaWindow` 和 `BalanceData`；`Balance` 是供旧调用方使用的可空首项。额度的 `ResetAt`、余额的 `Granted` 可空，其余有效数值须通过解析校验。`Error` 和 `Warning` 只能使用安全、可显示的文案，不传原始响应或异常内容。

| 结果情形 | 归一化行为 |
| --- | --- |
| 200 且有合法数据 | `Ok=true`；额度或余额填入对应列表；部分无效余额行可同时有 `Warning`。 |
| 200 但无可识别数据 | `Ok=false`，安全 `Error`；不以空列表伪装成功。 |
| 401 | Codex 仅在重读发现非空 Token，且 Token 或账号 ID 变化后最多重试一次；仍失败时 `RequiresLogin=true`。其他 Provider 返回安全的凭据错误。 |
| 403 | 安全的拒绝访问错误；Codex 不续期、不写登录文件。 |
| 429 | 提供 `StatusCode=429` 和可用的 `RetryAfterUtc`；智谱可识别的推算额度允许 `Ok=true, Stale=true, Warning`，仍须冷却。 |
| 网络/超时/其他 HTTP 失败 | `Ok=false`，安全 `Error`；同一账号已有合法数据保留并标过期。 |
| 取消 | `Canceled=true`，不计失败、不覆盖合法数据；删除、换凭据或退出后的旧代次结果不能回写。 |

## 3. 出站只读 HTTP 调用

下表的 Endpoint 和响应字段是**当前实现依赖的第三方形状**，不是本应用承诺的公共 API。三者均为 `GET`、无请求体；只从成功响应解析所需字段，不在日志或错误中输出响应原文。

| Provider / Endpoint | 请求认证与授权 | 成功响应中使用的字段、归一化输出 |
| --- | --- | --- |
| Codex `https://chatgpt.com/backend-api/wham/usage` | 从选定或默认 `auth.json` 只读 `access_token`，发送 `Authorization: Bearer <token>`；有账号 ID 时发送 `chatgpt-account-id`；`originator` 固定为 `codex-usage-widget`。远端权限由服务方判定。 | `rate_limit.primary_window` / `secondary_window` 中的 `limit_window_seconds`、`used_percent`、`reset_at` 或 `reset_after_seconds` → `QuotaWindow[]`；账号身份用于本机缓存归属。 |
| 智谱 `https://open.bigmodel.cn/api/monitor/usage/quota/limit` | `Authorization` 使用本机配置的 Key；`raw` 为原值，`bearer` 加 `Bearer ` 前缀。远端权限由服务方判定。 | `data.limits[]` 中的 `unit`、`number`、`percentage`、`nextResetTime` → `QuotaWindow[]`；可识别的 429 错误码和时间仅用于过期推算及冷却。 |
| DeepSeek `https://api.deepseek.com/user/balance` | `Authorization: Bearer <apiKey>`；远端权限由服务方判定。 | `is_available`、`balance_infos[]` 中的 `currency`、`total_balance`、可选 `granted_balance` → 逐币种 `BalanceData[]`；无效行跳过，合法行保留。 |

解析层对成功响应的**最低字段要求**如下；“必需”指一个条目要被接受所需的字段，不表示远端协议承诺必定提供。JSON 数字或可解析的数字字符串归一化为下列类型；`null`、非有限值和越界值不作为有效数值。

| Provider / 响应条目 | 接受该条目的必需字段（不可空） | 可选或可空字段 | 输出类型 |
| --- | --- | --- | --- |
| Codex `rate_limit.primary_window` / `secondary_window` | `limit_window_seconds`: 1～`int.MaxValue` 的有限数，向下取整；`used_percent`: 有限数，输出限制到 0～100 | `reset_at`: 有效时间戳，或 `reset_after_seconds`: 非负有限数；都无效时 `ResetAt=null` | `QuotaWindow`；至少一个合法窗口才算成功 |
| 智谱 `data.limits[]` | `unit`: 2、3 或 6；`number`: 正整数；`percentage`: 有限数，输出限制到 0～100 | `nextResetTime`: 有效时间戳；无效时 `ResetAt=null` | `QuotaWindow`；至少一个合法窗口才算成功 |
| DeepSeek `balance_infos[]` | `currency`: 非空字符串；`total_balance`: 可解析为 `decimal` 的金额 | `granted_balance`: 可空 `decimal`；`is_available`: 可选布尔，缺失时按可用处理 | `BalanceData`；至少一行合法余额才算成功 |

远端返回码原样进入 `FetchResult.StatusCode`；无响应为 `0`。当前只明确处理 200、401、403、429 与其余错误，任何服务返回的未知字段不进入公共模型。Key、Token、登录文件内容、实际账号 ID 和响应体不得出现在错误文案、日志或测试输出。开机自启、配置文件和预览模式不通过这些出站接口操作；预览不得发真实请求。

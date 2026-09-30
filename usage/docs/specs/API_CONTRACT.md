# 外部接口与适配契约

状态：M2 适配边界已实现；2026-09-30 三家本机官方只读查询与参考界面对照通过。应用名已按用户要求改为 usage。  
核验日期：2026-09-30。应用是本地工具，首版不对外提供 HTTP API。

## 1. 内部统一边界

每个 ProviderAdapter 只承担：连接状态、读取用量、映射领域快照、取消请求、返回可分类错误。

输入：Account 的安全凭据引用、刷新原因、超时/取消上下文。  
输出：UsageSnapshot 或 ProviderError。  
错误分类：未配置、需授权、无权限、网络不可达、超时、限流、服务故障、响应不兼容。

领域层不依赖 UI 对象，也不直接持有明文密钥。具体网络库、IPC 和 Windows 凭据实现留在适配层。数据类型见 [DATA_MODEL.md](DATA_MODEL.md)。

## 2. Codex 订阅

### 已有官方依据

官方 app-server 文档定义只读请求 account/rateLimits/read，返回额度窗口；还提供 account/rateLimits/updated 通知。首选本机可访问的官方 app-server 通道，按其当前协议完成初始化。

关键已公开字段：

| 字段 | 语义/处理 |
| --- | --- |
| rateLimitsByLimitId | 可选，多额度桶视图，优先使用 |
| rateLimits | 向后兼容的单桶视图 |
| primary / secondary | 可能为空，不能根据位置固定称为五小时/周 |
| usedPercent | 已消耗比例；有意义时转换为剩余 |
| windowDurationMins | 实际窗口长度；据此识别 300 分钟、10080 分钟或其他窗口 |
| resetsAt | Unix 秒时间戳；仅在已知语义下展示恢复时间 |
| limitId / limitName | 桶身份及可选展示名称 |

相同长度但不同桶的窗口不能盲目合并。用户套餐不返回五小时窗口时，显示“此账号未提供该窗口”，不画 0%。请求失败保留上次数据，更新状态单独标记。

### 实施前必须验证

- 用户 Windows/WSL/Codex 安装来源、可执行文件和认证上下文。
- 是否可复用官方已登录状态，app-server 的授权刷新生命周期是否有副作用。
- 当前版本协议、账号实际额度桶与需要展示的窗口。
- 缺少官方运行时、未登录或授权过期时的可恢复流程。

本产品不发起任务/推理、不消费重置奖励、不购买额度、不发送账户通知。应用内提供给聊天助手的额度工具不能当作独立软件可调用 API。

来源：[官方 app-server 文档](https://learn.chatgpt.com/docs/app-server)。

## 3. GLM Coding Plan 国内个人版

### 接入依据

官方“用量查询插件”明确支持个人版；其官方仓库脚本使用 GET 查询：

    https://open.bigmodel.cn/api/monitor/usage/quota/limit

官方脚本直接把 authToken 放入 Authorization 请求头；不是在该处自行添加 Bearer。首版按本机用户配置的国内个人版 API Key 进行接入验证，不把国际站或团队版差异混入默认方案。

核验的官方源码版本：
0446d0bb0bc537d97d3ab3664c4b8b9c4a0e1254

该版本脚本能证明查询路径以及对 data.limits 中 type / percentage 等字段的使用。但它仍把 TOKENS_LIMIT 简化标成五小时；不能用这个旧映射推断当前周额度、所有窗口类型或恢复时间。

### 2026-09-30 已核验的国内个人版映射

| 内容 | 当前证据 | M2 处理 |
| --- | --- | --- |
| 五小时窗口 | 官方个人用量页公开前端：CREDIT_LIMIT / unit 3；本账号 number 5 | 仅完整 type/unit/number 身份映射为300分钟 |
| 周窗口 | 同一官方前端：CREDIT_LIMIT / unit 6；本账号 number 1 | 仅完整身份映射为10080分钟；不按行顺序或总额猜测 |
| percentage 方向 | 官方组件标签“已使用”；用户官方页面两个窗口均0% | remainingPercent = 100 - percentage，异常范围拒绝 |
| nextResetTime | 官方组件直接格式化时间；本账号 Unix毫秒，周页面2026-10-07 13:25与响应一致 | 周为 fixed_reset；5h若提供则为 rolling_replenishment，缺失为 unknown，不造时刻 |
| 绝对积分总额 | 本账号 usage 为2000／10000，与官方页面一致 | 不按套餐硬编码，不用总额识别窗口；当前核心展示已验证比例 |

两个窗口可以拥有完全相同的 type。窗口 ID 使用 type/unit/number 组合，同身份重复拒绝，未知身份不伪装成熟悉窗口。只认识这一轮核验的个人版结构；旧 TOKENS_LIMIT、团队／国际版或未来单位变更仍需重新核验。

依据：[官方个人用量页](https://www.bigmodel.cn/coding-plan/personal/usage)、该页[窗口定义公开脚本](https://static.bigmodel.cn/wd-paas-front/js/claude-usage~glm-coding-ent-usage-member~glm-coding-ent-usage-stats~subscribe-overview.723f0998.js)和[百分比组件公开脚本](https://static.bigmodel.cn/wd-paas-front/js/claude-usage.8703690e.js)。读取公共脚本仅作静态分析，未执行网页脚本；哈希及脱敏本账号投影见 [M2 记录]（本机验收资料）。

不返回恢复时间时显示未知；不使用“现在 + 5 小时”造出时间。不能为展示周额度而把 MCP 月度次数当成周额度。

来源：[官方用量插件文档](https://docs.bigmodel.cn/cn/coding-plan/extension/usage-query-plugin)、[官方查询脚本固定版本](https://github.com/zai-org/zai-coding-plugins/blob/0446d0bb0bc537d97d3ab3664c4b8b9c4a0e1254/plugins/glm-plan-usage/skills/usage-query-skill/scripts/query-usage.mjs)、[现行套餐概览](https://docs.bigmodel.cn/cn/coding-plan/overview)。

资料读取说明：网页检索工具多次无法打开插件文档；通过直接读取官方 Markdown 成功获取内容，并查阅了其链接的官方仓库。未执行或安装该插件。

## 4. DeepSeek 官方余额

读取操作：

    GET https://api.deepseek.com/user/balance
    Authorization: Bearer <本机安全存储的 API Key>

已公开响应：

| 字段 | 处理 |
| --- | --- |
| is_available | 来源对账户可调用性的判断，独立于简单金额阈值 |
| balance_infos[] | 逐币种读取；不假设永远只返回 CNY |
| currency | 币种 |
| total_balance | 总可用余额，十进制字符串 |
| granted_balance | 有效赠送余额 |
| topped_up_balance | 充值余额 |

余额不得转换成五小时/周配额。多币种保持币种，不自行用汇率相加。空列表、结构损坏和金额零是不同状态。

来源：[官方余额接口](https://api-docs.deepseek.com/api/get-user-balance/)。

## 5. 常态时段规则接口

本地 RuleEngine 接受当前绝对时间、版本化 BenefitRule、所需节假日日历，输出：

- 当前为标准 / 优惠 / 不适用 / 待核验。
- 明确 benefitKind：GLM 模型积分消耗系数，DeepSeek 价格系数。
- nextTransitionAt（如可计算）。
- 适用时区、模型范围、数据来源和核验日期。

规则详见 SPEC 第 4.4 节。不每分钟抓官网；发布包随带经核验的规则快照，后续更新必须可追溯。日历覆盖不足或来源冲突时，受影响范围显示待核验，不能自信地显示“×2”。

## 6. 请求调度

初始设计值，需遵循来源实际限制：
- 展开 60 秒、收起 180 秒轮询；UI 倒计时本地计算。
- 启动有缓存先显示旧数据，再异步读取；不同平台可以并行。
- 同一账号 single-flight：自动/手动/展开触发合并。
- 单请求超时目标 10 秒；连续失败建议 30/60/120/300 秒退避并加少量抖动。
- 429 优先遵循 Retry-After，手动刷新不会重置冷却；鉴权错误暂停循环直到授权状态改变。
- 每次刷新有 generation ID；账号变化、退出、取消后的晚到响应不得覆盖新状态。
- lastAttemptAt 可以改变，lastSuccessAt 只有成功取得有效快照才改变。
- 到点后的状态为“待确认”，安排一次核验但不连续高频请求。

## 7. 接入完成的证据要求

每家至少留下：脱敏成功响应、缺字段响应、失效授权/网络错误结果、官方界面对应值与时间差记录。原始 Token、Key、Cookies、个人账户标识不得进入证据。

公开文档可读 ≠ 接口已对本账号验证；接口返回成功 ≠ 字段语义已验证。Codex 返回300／10080分钟，参考值及重置时刻一致；CLI 0.159.0只发初始化与额度读取。GLM 的两个窗口及周恢复时刻已与官方页面对照；具体账户值和时间只保留本机。DeepSeek 余额已与官方账户对照，具体账户值不公开。只保存白名单投影及无身份的额度截图，不保存原始响应或密钥。实测故障授权、另一套餐等边界与本地合成适配器检查区分，见 [M2 证据]（本机验收资料）。

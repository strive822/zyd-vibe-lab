# 测试计划

2026-09-25。对应 [SPEC.md](SPEC.md) FR-01～FR-12；当前独立复审运行结果为 **402 条断言全部通过**。

## 自动化入口

在 **Windows 命令提示符**执行根目录或本目录的 `build.bat --test-only`。脚本编译 `src/*.cs`、`tests/TestMain.cs` 和全部 `tests/*Regression.cs`，使用 `tests/fixtures/` 合成响应。

`build.bat --stage-only` 同时编译独立应用候选；无参数模式会在测试通过后尝试替换正式 EXE。截图诊断通过 `bin\QuotaTests.exe --render` 按需生成，不是日常测试门槛。

## 验收与测试对应

| 编号 / 需求 | 场景 | 主要自动化文件或验证方法 |
| --- | --- | --- |
| AC-01 / FR-01 | 百分比方向、缺失窗口、秒/毫秒重置、多币种独立显示 | TestMain、ProviderRegression、PixelUiRegression |
| AC-02 / FR-02 | 缺失或重复 ID、调序、删除、换 Key、扩展字段归属 | ConfigRegression |
| AC-03 / FR-03 | 缺配置、坏 JSON、错型结构、旧草稿、保存失败与备份 | ConfigRegression、UiRegression、ExpansionUiRegression |
| AC-04 / FR-04 | 非有限数、时间越界、decimal、部分坏行、旧透明字段移除 | ProviderRegression、ConfigRegression、EdgeRemovalRegression |
| AC-05 / FR-05 | 独立刷新、连续点击、外观变化、间隔重算 | CoordinatorRegression |
| AC-06 / FR-06 | 在途换凭据、隐藏恢复、删除重加、退出与迟到结果 | CoordinatorRegression、ProviderRegression |
| AC-07 / FR-07 | 普通失败退避、429、Retry-After、冷却边界和恢复 | CoordinatorRegression、ProviderRegression |
| AC-08 / FR-08 | 401 凭据不变/变化、第二次 401、403、账号变化失败、只读登录 | ProviderRegression、CoordinatorRegression |
| AC-09 / FR-09 | 状态、保存取消、长内容、顶部与短工作区、按钮边界、开机自启失败 | UiRegression、PixelUiRegression、ExpansionUiRegression、CompactUiRegression、ColorLanguageRegression、SettingsLayerRegression、AutostartRegression |
| AC-10 / FR-10 | 合成配置、独立实例、禁用真实自启操作 | UiRegression、PixelUiRegression |
| AC-11 / FR-11 | test-only、stage-only、默认模式、编译/测试失败、目标占用和无效参数 | 构建脚本；交付前在隔离目录检查退出码与目标文件 |
| AC-12 / FR-12 | 未知字段、脱敏、凭据保护、候选身份、各服务验证状态 | ConfigRegression、ProviderRegression、源码检查、UAT 记录 |

`AutostartRegression` 注入写入异常、返回成功但状态未变、成功重试，不访问真实注册表。窗口测试使用真实 HWND；1×/1.5×/2× 是诊断倍率，不等同于实际系统 DPI 切换。

## 实机与在线边界

当前候选的物理菜单操作、实机缩放/跨屏、托盘和目视确认记录在 [UAT.md](UAT.md)。`tests/LiveSmoke.cs` 是显式启用的只读连通性检查，不属于默认离线回归；各服务必须分别记录结果，不能仅以工具退出码表示所有接口通过。

数据库事务、数据库 migration、应用级角色授权不适用此本机项目；其对应风险由本机配置替换、账号状态隔离与 Provider 凭据测试覆盖。

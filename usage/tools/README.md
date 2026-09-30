# 维护工具

从项目根目录用 Windows Python 执行 `tools/<脚本名>`。工具通过 `_paths.py` 查找源码与证据，不依赖当前工作目录。

| 用途 | 工具 |
| --- | --- |
| 构建与包校验 | `build_portable.py`、`verify_portable.py` |
| 冻结视觉、布局、焦点与拖动 | `check_frozen_composition.py`、`check_m1.py`、`check_keyboard.py`、`check_drag.py`、`audit_layout.py`、`audit_live_layout.py` |
| 当前功能回归 | `verify_copy_slots.py`、`verify_countdown_motion.py`、`verify_collapse_native.py`、`verify_m3_native.py`、`verify_m4_native.py`、`verify_m5_native.py`、`verify_account_native.py`、`verify_window_native.py` |
| 只读数据校验 | `verify_m2_live.py`、`verify_provider.py` |
| 性能与驻留 | `measure_idle.py`、`measure_live.py`、`observe_stability.py` |
| 截图与实际操作取证 | `capture_live.py`、`capture_reminder_edges.py`、`record_live_uat.py`、`record_edge_uat.py`、`analyze_live_uat.py` |

默认输出位于 `docs/evidence`。可见原生测试先退出日常实例；测试后恢复，避免临时球与日常球同时出现。固定渲染、只读观察和真实用户操作的证据分别记录。

账户配置与修复入口在 `src/configure_accounts.py`、`src/repair_config.py`。构建输入缓存位于 `packaging/cache`，默认不上传。

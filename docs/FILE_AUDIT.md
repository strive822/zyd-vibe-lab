# 逐文件检查清单

由 `python scripts/check_repository.py --inventory docs/FILE_AUDIT.md` 生成。
列出静态检查覆盖，不表示已逐行证明所有业务逻辑无缺陷；项目验证与边界见 REPOSITORY_CLEANUP_REPORT.md。

| 文件（相对仓库根目录） | 已执行静态检查 |
| --- | --- |
| `.gitattributes` | secret patterns, UTF-8 |
| `.github/workflows/checks.yml` | secret patterns, UTF-8 |
| `.gitignore` | secret patterns, UTF-8 |
| `AGENTS.md` | secret patterns, UTF-8, local Markdown links |
| `INSTALL.md` | secret patterns, UTF-8, local Markdown links |
| `LibreTV/.gitignore` | secret patterns, UTF-8 |
| `LibreTV/AGENTS.md` | secret patterns, UTF-8, local Markdown links |
| `LibreTV/INSTALL.md` | secret patterns, UTF-8, local Markdown links |
| `LibreTV/README.md` | secret patterns, UTF-8, local Markdown links |
| `LibreTV/SECURITY_PATCHES.md` | secret patterns, UTF-8, local Markdown links |
| `LibreTV/THIRD_PARTY.md` | secret patterns, UTF-8, local Markdown links |
| `LibreTV/assets.json` | secret patterns, UTF-8, JSON |
| `LibreTV/delivery/FILES.json` | secret patterns, UTF-8, JSON |
| `LibreTV/delivery/LibreTV.zip` | secret patterns, ZIP CRC/paths, package/source SHA-256 |
| `LibreTV/delivery/SHA256SUMS.txt` | secret patterns, UTF-8 |
| `LibreTV/packages/libretv-files.json` | secret patterns, UTF-8, JSON |
| `LibreTV/packages/libretv-source.zip` | secret patterns, ZIP CRC/paths, package/source SHA-256 |
| `LibreTV/profile/LICENSE` | secret patterns, UTF-8 |
| `LibreTV/profile/defaults.json` | secret patterns, UTF-8, JSON |
| `LibreTV/profile/launcher.mjs` | secret patterns, UTF-8 |
| `LibreTV/profile/notify.vbs` | secret patterns, UTF-8 |
| `LibreTV/profile/open-browser.ps1` | secret patterns, UTF-8 |
| `LibreTV/profile/rebuild.cmd` | secret patterns, UTF-8 |
| `LibreTV/profile/start.vbs` | secret patterns, UTF-8 |
| `LibreTV/profile/stop.mjs` | secret patterns, UTF-8 |
| `LibreTV/profile/stop.vbs` | secret patterns, UTF-8 |
| `LibreTV/restore.py` | secret patterns, UTF-8, Python syntax |
| `README.md` | secret patterns, UTF-8, local Markdown links |
| `Windows-MCP/.gitignore` | secret patterns, UTF-8 |
| `Windows-MCP/AGENTS.md` | secret patterns, UTF-8, local Markdown links |
| `Windows-MCP/INSTALL.md` | secret patterns, UTF-8, local Markdown links |
| `Windows-MCP/README.md` | secret patterns, UTF-8, local Markdown links |
| `Windows-MCP/THIRD_PARTY.md` | secret patterns, UTF-8, local Markdown links |
| `Windows-MCP/assets.json` | secret patterns, UTF-8, JSON |
| `Windows-MCP/delivery/FILES.json` | secret patterns, UTF-8, JSON |
| `Windows-MCP/delivery/SHA256SUMS.txt` | secret patterns, UTF-8 |
| `Windows-MCP/delivery/Windows-MCP.zip` | secret patterns, ZIP CRC/paths, package/source SHA-256 |
| `Windows-MCP/profile/LICENSE.md` | secret patterns, UTF-8, local Markdown links |
| `Windows-MCP/profile/README.md` | secret patterns, UTF-8, local Markdown links |
| `Windows-MCP/profile/install.cmd` | secret patterns, UTF-8 |
| `Windows-MCP/profile/start.cmd` | secret patterns, UTF-8 |
| `Windows-MCP/restore.py` | secret patterns, UTF-8, Python syntax |
| `Winhance/.gitignore` | secret patterns, UTF-8 |
| `Winhance/AGENTS.md` | secret patterns, UTF-8, local Markdown links |
| `Winhance/INSTALL.md` | secret patterns, UTF-8, local Markdown links |
| `Winhance/README.md` | secret patterns, UTF-8, local Markdown links |
| `Winhance/THIRD_PARTY.md` | secret patterns, UTF-8, local Markdown links |
| `Winhance/assets.json` | secret patterns, UTF-8, JSON |
| `Winhance/delivery/FILES.json` | secret patterns, UTF-8, JSON |
| `Winhance/delivery/SHA256SUMS.txt` | secret patterns, UTF-8 |
| `Winhance/delivery/Winhance.zip` | secret patterns, ZIP CRC/paths, package/source SHA-256 |
| `Winhance/profile/README.md` | secret patterns, UTF-8, local Markdown links |
| `Winhance/restore.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/.github/ISSUE_TEMPLATE/bug.yml` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/.github/ISSUE_TEMPLATE/feature.yml` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/.github/workflows/checks.yml` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/.github/workflows/hd-materials.yml` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/.gitignore` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/AGENTS.md` | secret patterns, UTF-8, local Markdown links |
| `codex-bailong-desktop-pet/INSTALL.md` | secret patterns, UTF-8, local Markdown links |
| `codex-bailong-desktop-pet/NOTICE.md` | secret patterns, UTF-8, local Markdown links |
| `codex-bailong-desktop-pet/README.md` | secret patterns, UTF-8, local Markdown links |
| `codex-bailong-desktop-pet/Token入口精简/更新说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/Token图表更新/图表说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/app/activity_targets.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/app_updates.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/autostart.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/book_catalog.json` | secret patterns, UTF-8, JSON |
| `codex-bailong-desktop-pet/app/book_reference.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/card_motion.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/card_surface_probe.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/chart_curve.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/chart_reveal.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/chat_window.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/codex_connection.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/codex_live_status.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/codex_navigation.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/codex_startup.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/compact_bubble.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/completion_ledger.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/connection_health.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/connection_widgets.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/continuous_work.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/conversation_roster.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/daily_report.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/dashboard_cards.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/decode_runtime.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/deployment_state.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/desktop.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/desktop_core.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/desktop_services.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/desktop_settings.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/detail_sections.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/directory_deploy.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/enhanced.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/enhanced_core.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/firefox_video.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/fonts/ChakraPetch-Regular.ttf` | secret patterns, font/audio signature |
| `codex-bailong-desktop-pet/app/fonts/OFL.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/app/inline_confirmation.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/installer.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/interaction_probe.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/island_widgets.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/licenses/comtypes-LICENSE.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/app/licenses/msgspec-LICENSE.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/app/licenses/upstream-v0.4.1-assets.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/app/linked_report_motion.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/log_catalog.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/loop_cache.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/material_catalog.json` | secret patterns, UTF-8, JSON |
| `codex-bailong-desktop-pet/app/material_controller.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/material_probe.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/material_store.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/native_coordinates.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/optional_tools.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/panel_transition.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/performance_metrics.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/pet.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/prepare_assets.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/program_update_apply.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/program_updates.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/provider_accounts.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/provider_monitor.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/provider_tokens.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/provider_widgets.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/qa_bubble.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/qa_desktop.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/qa_stress.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/qa_window_order.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/quick_actions.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/quota.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/quota_summary.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/quota_summary_data.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/refresh_flow.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/refresh_indicator.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/reset_card.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/reset_presentation.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/reset_watch.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/ring_metrics.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/ring_widgets.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/selftest.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/session_read_state.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/settings_draft.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/shared_assets.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/silent_notify.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/sounds/Kenney-License.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/app/sounds/click.wav` | secret patterns, font/audio signature |
| `codex-bailong-desktop-pet/app/sounds/来源.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/app/spring_motion.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/status_indicator.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/status_motion.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/status_reactions.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/stream_player.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/surface_morph.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/sustained_assets.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/sustained_player.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/sustained_probe.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_animation_load.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_animation_quality.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_app_updates.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_book_reference.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_bubble_resize.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_card_motion.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_compact_bubble.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_connection_and_sessions.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_continuous_desktop.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_continuous_work.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_conversation_navigation.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_conversation_rows.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_daily_report.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_decoder_runtime.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_deployment_transaction.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_desktop.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_directory_deploy.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_enhanced_core.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_enhanced_ui.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_header_refresh.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_independent_cards.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_interaction_batch.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_island.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_linked_cards.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_live_compaction.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_loop_cache.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_material_controller.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_material_store.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_native_interactions.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_package_optimization.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_panel_transition.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_performance_paths.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_pet.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_program_updates.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_provider_accounts.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_provider_tokens.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_provider_ui.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_quick_deployment.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_quota.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_quota_summary.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_quota_summary_data.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_read_completion.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_refresh_flow.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_refresh_indicator.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_report_chart_response.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_report_transition.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_reset_card.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_reset_presentation.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_reset_watch.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_ring_legibility.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_ring_metrics.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_ring_widgets.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_second_batch.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_shortcuts_startup.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_shrink_landing.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_soft_curves_navigation.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_spring_motion.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_status_handoff.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_status_indicator.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_status_morph.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_status_reactions.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_subagent_notifications.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_surface_handoff.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_sustained_player.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_sustained_reactions.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_third_batch.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_token_calendar.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_token_charts.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_update_integration.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_video_fullscreen.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_waiting_status.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/test_work_actions.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/token_analytics.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/token_calendar.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/token_charts.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/typography.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/ui_theme.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/update_controller.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/update_widgets.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/version.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/video_fullscreen.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/app/video_yield.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/asset_pack.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/build_local.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/build_materials.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/build_program_update.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/build_release.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/check_bundle.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/delivery/FILES.json` | secret patterns, UTF-8, JSON |
| `codex-bailong-desktop-pet/delivery/SHA256SUMS.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/delivery/codex-bailong-desktop-pet.zip` | secret patterns, ZIP CRC/paths, package/source SHA-256 |
| `codex-bailong-desktop-pet/deploy_release.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/docs/DEVELOPMENT.md` | secret patterns, UTF-8, local Markdown links |
| `codex-bailong-desktop-pet/docs/media/cover.png` | secret patterns, image signature |
| `codex-bailong-desktop-pet/docs/media/curves-and-conversation-feedback.png` | secret patterns, image signature |
| `codex-bailong-desktop-pet/docs/media/in-app-updates.png` | secret patterns, image signature |
| `codex-bailong-desktop-pet/docs/media/work-actions.gif` | secret patterns, image signature |
| `codex-bailong-desktop-pet/docs/releases/v0.7.1.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/docs/releases/v0.7.2.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/docs/releases/v0.7.9-performance.json` | secret patterns, UTF-8, JSON |
| `codex-bailong-desktop-pet/docs/releases/v0.7.9.md` | secret patterns, UTF-8, local Markdown links |
| `codex-bailong-desktop-pet/docs/releases/v0.8.3.md` | secret patterns, UTF-8, local Markdown links |
| `codex-bailong-desktop-pet/docs/report/assets/单弧刷新-poster.png` | secret patterns, image signature |
| `codex-bailong-desktop-pet/docs/report/assets/单弧刷新.gif` | secret patterns, image signature |
| `codex-bailong-desktop-pet/docs/report/assets/原有招手动作-poster.png` | secret patterns, image signature |
| `codex-bailong-desktop-pet/docs/report/assets/原有招手动作.gif` | secret patterns, image signature |
| `codex-bailong-desktop-pet/docs/report/assets/周额度变色.png` | secret patterns, image signature |
| `codex-bailong-desktop-pet/docs/report/assets/完成提醒-poster.png` | secret patterns, image signature |
| `codex-bailong-desktop-pet/docs/report/assets/完成提醒.gif` | secret patterns, image signature |
| `codex-bailong-desktop-pet/docs/report/assets/日报展开收回-poster.png` | secret patterns, image signature |
| `codex-bailong-desktop-pet/docs/report/assets/日报展开收回.gif` | secret patterns, image signature |
| `codex-bailong-desktop-pet/docs/report/assets/日报概览.png` | secret patterns, image signature |
| `codex-bailong-desktop-pet/docs/report/assets/日报模型.png` | secret patterns, image signature |
| `codex-bailong-desktop-pet/docs/report/assets/曲线入场-poster.png` | secret patterns, image signature |
| `codex-bailong-desktop-pet/docs/report/assets/曲线入场.gif` | secret patterns, image signature |
| `codex-bailong-desktop-pet/docs/report/assets/柱图入场-poster.png` | secret patterns, image signature |
| `codex-bailong-desktop-pet/docs/report/assets/柱图入场.gif` | secret patterns, image signature |
| `codex-bailong-desktop-pet/docs/report/assets/正常收起胶囊-poster.png` | secret patterns, image signature |
| `codex-bailong-desktop-pet/docs/report/assets/正常收起胶囊.gif` | secret patterns, image signature |
| `codex-bailong-desktop-pet/docs/report/assets/正常面板.png` | secret patterns, image signature |
| `codex-bailong-desktop-pet/docs/report/assets/状态连续变形-poster.png` | secret patterns, image signature |
| `codex-bailong-desktop-pet/docs/report/assets/状态连续变形.gif` | secret patterns, image signature |
| `codex-bailong-desktop-pet/docs/report/assets/白龙形象.png` | secret patterns, image signature |
| `codex-bailong-desktop-pet/docs/report/assets/聊天.png` | secret patterns, image signature |
| `codex-bailong-desktop-pet/docs/report/assets/胶囊.png` | secret patterns, image signature |
| `codex-bailong-desktop-pet/docs/report/assets/胶囊展开正常-poster.png` | secret patterns, image signature |
| `codex-bailong-desktop-pet/docs/report/assets/胶囊展开正常.gif` | secret patterns, image signature |
| `codex-bailong-desktop-pet/docs/report/assets/视频全屏让位设置.png` | secret patterns, image signature |
| `codex-bailong-desktop-pet/docs/report/assets/设置.png` | secret patterns, image signature |
| `codex-bailong-desktop-pet/docs/report/assets/详情.png` | secret patterns, image signature |
| `codex-bailong-desktop-pet/docs/report/assets/详情展开-poster.png` | secret patterns, image signature |
| `codex-bailong-desktop-pet/docs/report/assets/详情展开.gif` | secret patterns, image signature |
| `codex-bailong-desktop-pet/docs/report/assets/详情收回-poster.png` | secret patterns, image signature |
| `codex-bailong-desktop-pet/docs/report/assets/详情收回.gif` | secret patterns, image signature |
| `codex-bailong-desktop-pet/docs/report/assets/项目模型Token用量.png` | secret patterns, image signature |
| `codex-bailong-desktop-pet/docs/report/index.html` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/docs/upstream/ASSETS-v0.4.1.md` | secret patterns, UTF-8, local Markdown links |
| `codex-bailong-desktop-pet/docs/upstream/ASSETS.md` | secret patterns, UTF-8, local Markdown links |
| `codex-bailong-desktop-pet/docs/upstream/README.md` | secret patterns, UTF-8, local Markdown links |
| `codex-bailong-desktop-pet/docs/upstream/VERSION.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/docs/多平台账号说明.md` | secret patterns, UTF-8, local Markdown links |
| `codex-bailong-desktop-pet/docs/快速部署说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/docs/新增功能说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/docs/迭代历史.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/outputs/白龙桌宠素材/素材清单.json` | secret patterns, UTF-8, JSON |
| `codex-bailong-desktop-pet/package_trim.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/quality_check.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/release_retention.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/release_version.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/requirements-enhanced.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/test_local_workflow.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/test_release_retention.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/test_release_version.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/tools/assemble_hd_release.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/tools/build_book_catalog.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/tools/import_installed_assets.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/tools/prepare_assets.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/tools/publish_hd_resource.py` | secret patterns, UTF-8, Python syntax |
| `codex-bailong-desktop-pet/一键部署更新/快速部署说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/三圆状态动画/更新说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/上下文压缩与会话跳转/更新说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/交互整理第一批/更新说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/交互整理第三批/更新说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/交互整理第二批/更新说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/动作尺寸修复/尺寸修复说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/动作质量修复/原始动作逻辑与质量基准.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/动画负载与日报优化/更新说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/包体优化/.gitkeep` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/包体优化/更新说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/卡片动效统一/更新说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/卡片独立与极简/更新说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/发布说明/快速部署说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/发布说明/版本编号规则.json` | secret patterns, UTF-8, JSON |
| `codex-bailong-desktop-pet/启动白龙.cmd` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/回弹过渡/更新说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/圆环辨识优化/更新说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/子会话完成提醒修复/更新说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/完成提醒确认/更新说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/导航标签清理/更新说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/已读提醒修复/修复说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/应用内更新/更新说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/开口弧额度环/更新说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/持续状态动画/更新说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/收回闪烁修复/更新说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/新增动作接入/更新说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/日报与圆环布局/更新说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/日报动画防闪烁/修复说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/日报图表响应修复/修复说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/日报概览完整展开/更新说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/日报防闪与自然循环/更新说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/本地实装/更新说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/气泡同步过渡/过渡说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/气泡高度过渡/过渡说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/灵动岛气泡更新/更新与质量检查说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/状态响应优化/更新说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/状态图标动画/更新说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/状态图标连续变形/更新说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/状态对话名更新/更新说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/状态联动更新/规则与验收说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/纯程序更新/更新说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/统一刷新与精简顶栏/更新说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/胶囊分段额度环/更新说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/胶囊双向过渡修复/更新说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/视频全屏修复/更新说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/视频全屏让位/更新说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/详情分类更新/详情分类说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/跨机器部署检查/快速部署说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/轻量与高清分离/更新说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/过渡收尾修复/更新说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/过渡闪烁修复/修复说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/通用底层优化/更新说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/配色与窗口过渡/更新说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/面板集成更新/集成说明.txt` | secret patterns, UTF-8 |
| `codex-bailong-desktop-pet/额度卡片重设计/更新说明.txt` | secret patterns, UTF-8 |
| `codex-usage/.gitignore` | secret patterns, UTF-8 |
| `codex-usage/INSTALL.md` | secret patterns, UTF-8, local Markdown links |
| `codex-usage/README.md` | secret patterns, UTF-8, local Markdown links |
| `codex-usage/delivery/FILES.json` | secret patterns, UTF-8, JSON |
| `codex-usage/delivery/SHA256SUMS.txt` | secret patterns, UTF-8 |
| `codex-usage/delivery/codex-usage.zip` | secret patterns, ZIP CRC/paths, package/source SHA-256 |
| `codex-usage/docs/IMPLEMENTATION.md` | secret patterns, UTF-8, local Markdown links |
| `codex-usage/docs/README.md` | secret patterns, UTF-8, local Markdown links |
| `codex-usage/docs/design/CONCEPT_PROMPT.md` | secret patterns, UTF-8, local Markdown links |
| `codex-usage/docs/design/COUNTDOWN_MOTION.md` | secret patterns, UTF-8, local Markdown links |
| `codex-usage/docs/design/fusion.png` | secret patterns, image signature |
| `codex-usage/docs/design/references/REFERENCE_NOTES.md` | secret patterns, UTF-8, local Markdown links |
| `codex-usage/docs/design/references/moonshot-desktop-1440.png` | secret patterns, image signature |
| `codex-usage/docs/evidence/m1-r4/frozen-source/countdown.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/docs/evidence/m1-r4/frozen-source/main.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/docs/evidence/m1-r4/frozen-source/palette_visual.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/docs/evidence/m1-r4/frozen-source/quota_visual.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/docs/evidence/m1-r4/frozen-source/requirements.txt` | secret patterns, UTF-8 |
| `codex-usage/docs/guides/GOTCHAS.md` | secret patterns, UTF-8, local Markdown links |
| `codex-usage/docs/guides/SOP.md` | secret patterns, UTF-8, local Markdown links |
| `codex-usage/docs/guides/THIRD_PARTY.md` | secret patterns, UTF-8, local Markdown links |
| `codex-usage/docs/guides/USAGE.md` | secret patterns, UTF-8, local Markdown links |
| `codex-usage/docs/history/CLEANUP.md` | secret patterns, UTF-8, local Markdown links |
| `codex-usage/docs/history/M1-FREEZE.md` | secret patterns, UTF-8, local Markdown links |
| `codex-usage/docs/history/M1-REPORT.md` | secret patterns, UTF-8, local Markdown links |
| `codex-usage/docs/specs/API_CONTRACT.md` | secret patterns, UTF-8, local Markdown links |
| `codex-usage/docs/specs/DATA_MODEL.md` | secret patterns, UTF-8, local Markdown links |
| `codex-usage/docs/specs/DECISIONS.md` | secret patterns, UTF-8, local Markdown links |
| `codex-usage/docs/specs/DESIGN.md` | secret patterns, UTF-8, local Markdown links |
| `codex-usage/docs/specs/PLAN.md` | secret patterns, UTF-8, local Markdown links |
| `codex-usage/docs/specs/SPEC.md` | secret patterns, UTF-8, local Markdown links |
| `codex-usage/docs/specs/TEST_PLAN.md` | secret patterns, UTF-8, local Markdown links |
| `codex-usage/docs/validation/DESIGN-AUDIT.md` | secret patterns, UTF-8, local Markdown links |
| `codex-usage/docs/validation/README.md` | secret patterns, UTF-8, local Markdown links |
| `codex-usage/docs/validation/countdown.gif` | secret patterns, image signature |
| `codex-usage/docs/validation/four-edges.png` | secret patterns, image signature |
| `codex-usage/docs/validation/sixth-error.png` | secret patterns, image signature |
| `codex-usage/docs/validation/sixth-focus.png` | secret patterns, image signature |
| `codex-usage/docs/validation/sixth-unconfigured.png` | secret patterns, image signature |
| `codex-usage/launch.cmd` | secret patterns, UTF-8 |
| `codex-usage/packages/SHA256SUMS.txt` | secret patterns, UTF-8 |
| `codex-usage/packages/usage-0.1.0-windows-x64.zip` | secret patterns, ZIP CRC/paths, package/source SHA-256 |
| `codex-usage/packaging/Launcher.cs` | secret patterns, UTF-8 |
| `codex-usage/packaging/README.md` | secret patterns, UTF-8, local Markdown links |
| `codex-usage/packaging/cache/pyside-license-index.json` | secret patterns, UTF-8, JSON |
| `codex-usage/packaging/cache/pyside-licenses/Apache-2.0.txt` | secret patterns, UTF-8 |
| `codex-usage/packaging/cache/pyside-licenses/BSD-3-Clause.txt` | secret patterns, UTF-8 |
| `codex-usage/packaging/cache/pyside-licenses/GFDL-1.3-no-invariants-only.txt` | secret patterns, UTF-8 |
| `codex-usage/packaging/cache/pyside-licenses/GPL-2.0-only.txt` | secret patterns, UTF-8 |
| `codex-usage/packaging/cache/pyside-licenses/GPL-3.0-only.txt` | secret patterns, UTF-8 |
| `codex-usage/packaging/cache/pyside-licenses/LGPL-3.0-only.txt` | secret patterns, UTF-8 |
| `codex-usage/packaging/cache/pyside-licenses/LicenseRef-Qt-Commercial.txt` | secret patterns, UTF-8 |
| `codex-usage/packaging/cache/pyside-licenses/Qt-GPL-exception-1.0.txt` | secret patterns, UTF-8 |
| `codex-usage/packaging/cache/python-3.12.10-embed-amd64.zip.sigstore.json` | secret patterns, UTF-8, JSON |
| `codex-usage/pyproject.toml` | secret patterns, UTF-8, TOML |
| `codex-usage/requirements-dev.txt` | secret patterns, UTF-8 |
| `codex-usage/requirements.txt` | secret patterns, UTF-8 |
| `codex-usage/src/configure_accounts.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/countdown.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/main.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/palette_visual.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/quota_visual.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/repair_config.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/run_app.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/__init__.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/account_ui.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/accounts.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/adapters.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/assets/check.svg` | secret patterns, UTF-8, SVG XML |
| `codex-usage/src/usage_app/assets/chevron-up.svg` | secret patterns, UTF-8, SVG XML |
| `codex-usage/src/usage_app/assets/chevron.svg` | secret patterns, UTF-8, SVG XML |
| `codex-usage/src/usage_app/autostart.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/clipboard.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/credentials.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/data_location.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/desktop.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/desktop_geometry.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/desktop_settings.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/diagnostics.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/icons.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/messages.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/models.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/parsers.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/presentation.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/recovery.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/refresh.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/reminder_service.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/reminder_ui.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/reminders.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/rules.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/runtime.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/snippet_service.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/snippets.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/source_evidence.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/startup_job.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/startup_registry.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/startup_ui.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/storage.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/text_ui.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/widget.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/window_ui.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/windows_monitors.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/windows_visibility.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tests/conftest.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tests/test_accounts.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tests/test_adapters.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tests/test_autostart.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tests/test_data_location.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tests/test_desktop_geometry.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tests/test_diagnostics.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tests/test_parsers.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tests/test_qt_adapters.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tests/test_recovery.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tests/test_refresh.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tests/test_reminder_service.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tests/test_reminders.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tests/test_rules.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tests/test_snippet_service.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tests/test_snippets.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tests/test_startup_job.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tests/test_startup_registry.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tests/test_storage.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tools/README.md` | secret patterns, UTF-8, local Markdown links |
| `codex-usage/tools/_paths.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tools/analyze_live_uat.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tools/audit_layout.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tools/audit_live_layout.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tools/build_portable.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tools/capture_live.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tools/capture_reminder_edges.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tools/check_drag.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tools/check_frozen_composition.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tools/check_keyboard.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tools/check_m1.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tools/clipboard_win.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tools/measure_idle.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tools/measure_live.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tools/observe_stability.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tools/record_edge_uat.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tools/record_live_uat.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tools/verify_account_native.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tools/verify_collapse_native.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tools/verify_copy_slots.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tools/verify_countdown_motion.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tools/verify_m2_live.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tools/verify_m3_native.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tools/verify_m4_native.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tools/verify_m5_native.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tools/verify_portable.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tools/verify_provider.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tools/verify_startup_identity.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tools/verify_visibility_native.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/tools/verify_window_native.py` | secret patterns, UTF-8, Python syntax |
| `dca-calculator/.gitattributes` | secret patterns, UTF-8 |
| `dca-calculator/.gitignore` | secret patterns, UTF-8 |
| `dca-calculator/CHANGELOG.md` | secret patterns, UTF-8, local Markdown links |
| `dca-calculator/DECISIONS.md` | secret patterns, UTF-8, local Markdown links |
| `dca-calculator/DEVLOG.md` | secret patterns, UTF-8, local Markdown links |
| `dca-calculator/GOTCHAS.md` | secret patterns, UTF-8, local Markdown links |
| `dca-calculator/INSTALL.md` | secret patterns, UTF-8, local Markdown links |
| `dca-calculator/LICENSE` | secret patterns, UTF-8 |
| `dca-calculator/PROJECT_KNOWLEDGE.md` | secret patterns, UTF-8, local Markdown links |
| `dca-calculator/README.md` | secret patterns, UTF-8, local Markdown links |
| `dca-calculator/README_Project.md` | secret patterns, UTF-8, local Markdown links |
| `dca-calculator/SOP.md` | secret patterns, UTF-8, local Markdown links |
| `dca-calculator/backend/app/__init__.py` | secret patterns, UTF-8, Python syntax |
| `dca-calculator/backend/app/config.py` | secret patterns, UTF-8, Python syntax |
| `dca-calculator/backend/app/data/__init__.py` | secret patterns, UTF-8, Python syntax |
| `dca-calculator/backend/app/data/market_data.py` | secret patterns, UTF-8, Python syntax |
| `dca-calculator/backend/app/main.py` | secret patterns, UTF-8, Python syntax |
| `dca-calculator/backend/app/models/__init__.py` | secret patterns, UTF-8, Python syntax |
| `dca-calculator/backend/app/models/c_model.py` | secret patterns, UTF-8, Python syntax |
| `dca-calculator/backend/app/models/rigorous_model.py` | secret patterns, UTF-8, Python syntax |
| `dca-calculator/backend/app/schemas/__init__.py` | secret patterns, UTF-8, Python syntax |
| `dca-calculator/backend/app/schemas/calculation.py` | secret patterns, UTF-8, Python syntax |
| `dca-calculator/backend/app/services/__init__.py` | secret patterns, UTF-8, Python syntax |
| `dca-calculator/backend/app/services/calculator.py` | secret patterns, UTF-8, Python syntax |
| `dca-calculator/backend/app/tests/__init__.py` | secret patterns, UTF-8, Python syntax |
| `dca-calculator/backend/app/tests/test_api.py` | secret patterns, UTF-8, Python syntax |
| `dca-calculator/backend/app/tests/test_c_model.py` | secret patterns, UTF-8, Python syntax |
| `dca-calculator/backend/app/tests/test_calculator.py` | secret patterns, UTF-8, Python syntax |
| `dca-calculator/backend/app/tests/test_rigorous_model.py` | secret patterns, UTF-8, Python syntax |
| `dca-calculator/backend/app/tests/test_source_failures.py` | secret patterns, UTF-8, Python syntax |
| `dca-calculator/backend/build_exe.spec` | secret patterns, UTF-8, Python syntax |
| `dca-calculator/backend/build_exe_entry.py` | secret patterns, UTF-8, Python syntax |
| `dca-calculator/backend/pytest.ini` | secret patterns, UTF-8 |
| `dca-calculator/backend/requirements-dev.txt` | secret patterns, UTF-8 |
| `dca-calculator/backend/requirements.txt` | secret patterns, UTF-8 |
| `dca-calculator/backend/tools/verify_data_sources.py` | secret patterns, UTF-8, Python syntax |
| `dca-calculator/delivery/FILES.json` | secret patterns, UTF-8, JSON |
| `dca-calculator/delivery/SHA256SUMS.txt` | secret patterns, UTF-8 |
| `dca-calculator/delivery/dca-calculator.zip` | secret patterns, ZIP CRC/paths, package/source SHA-256 |
| `dca-calculator/docs/使用说明.md` | secret patterns, UTF-8, local Markdown links |
| `dca-calculator/docs/数据源验证报告.md` | secret patterns, UTF-8, local Markdown links |
| `dca-calculator/docs/验收报告.md` | secret patterns, UTF-8, local Markdown links |
| `dca-calculator/frontend/app/globals.css` | secret patterns, UTF-8 |
| `dca-calculator/frontend/app/layout.tsx` | secret patterns, UTF-8 |
| `dca-calculator/frontend/app/page.tsx` | secret patterns, UTF-8 |
| `dca-calculator/frontend/lib/calculation.ts` | secret patterns, UTF-8 |
| `dca-calculator/frontend/lib/money.ts` | secret patterns, UTF-8 |
| `dca-calculator/frontend/next.config.ts` | secret patterns, UTF-8 |
| `dca-calculator/frontend/package-lock.json` | secret patterns, UTF-8, JSON |
| `dca-calculator/frontend/package.json` | secret patterns, UTF-8, JSON |
| `dca-calculator/frontend/postcss.config.mjs` | secret patterns, UTF-8 |
| `dca-calculator/frontend/tests/calculation.test.ts` | secret patterns, UTF-8 |
| `dca-calculator/frontend/tests/money.test.ts` | secret patterns, UTF-8 |
| `dca-calculator/frontend/tsconfig.json` | secret patterns, UTF-8, JSON |
| `dca-calculator/scripts/start_backend.bat` | secret patterns, UTF-8 |
| `dca-calculator/scripts/start_frontend.bat` | secret patterns, UTF-8 |
| `dca-calculator/tests/screenshots/e2e_evening_1234.56.png` | secret patterns, image signature |
| `dca-calculator/tests/screenshots/e2e_no_amount.png` | secret patterns, image signature |
| `dca-calculator/tests/screenshots/e2e_with_amount.png` | secret patterns, image signature |
| `docs/AGENT_DELIVERY_STANDARD.md` | secret patterns, UTF-8, local Markdown links |
| `docs/FILE_AUDIT.md` | secret patterns, UTF-8, local Markdown links |
| `docs/REPOSITORY_CLEANUP_REPORT.md` | secret patterns, UTF-8, local Markdown links |
| `docs/REPOSITORY_SYNC_2026-10-24.md` | secret patterns, UTF-8, local Markdown links |
| `docs/TOOL_PROFILE_HISTORY_2026-10-22.md` | secret patterns, UTF-8, local Markdown links |
| `graduation-thesis-workflow/.gitignore` | secret patterns, UTF-8 |
| `graduation-thesis-workflow/AGENTS.md` | secret patterns, UTF-8, local Markdown links |
| `graduation-thesis-workflow/CLAUDE.md` | secret patterns, UTF-8, local Markdown links |
| `graduation-thesis-workflow/DECISIONS.md` | secret patterns, UTF-8, local Markdown links |
| `graduation-thesis-workflow/DEVLOG.md` | secret patterns, UTF-8, local Markdown links |
| `graduation-thesis-workflow/GOTCHAS.md` | secret patterns, UTF-8, local Markdown links |
| `graduation-thesis-workflow/INSTALL.md` | secret patterns, UTF-8, local Markdown links |
| `graduation-thesis-workflow/LICENSE` | secret patterns, UTF-8 |
| `graduation-thesis-workflow/README.md` | secret patterns, UTF-8, local Markdown links |
| `graduation-thesis-workflow/SOP.md` | secret patterns, UTF-8, local Markdown links |
| `graduation-thesis-workflow/THIRD_PARTY_NOTICES.md` | secret patterns, UTF-8, local Markdown links |
| `graduation-thesis-workflow/delivery/FILES.json` | secret patterns, UTF-8, JSON |
| `graduation-thesis-workflow/delivery/SHA256SUMS.txt` | secret patterns, UTF-8 |
| `graduation-thesis-workflow/delivery/graduation-thesis-workflow.zip` | secret patterns, ZIP CRC/paths, package/source SHA-256 |
| `graduation-thesis-workflow/docs/COMPATIBILITY.md` | secret patterns, UTF-8, local Markdown links |
| `graduation-thesis-workflow/docs/INSTALL.md` | secret patterns, UTF-8, local Markdown links |
| `graduation-thesis-workflow/docs/RELEASE.md` | secret patterns, UTF-8, local Markdown links |
| `graduation-thesis-workflow/docs/UPSTREAM_REVIEW.md` | secret patterns, UTF-8, local Markdown links |
| `graduation-thesis-workflow/docs/VALIDATION.md` | secret patterns, UTF-8, local Markdown links |
| `graduation-thesis-workflow/packages/checksums.json` | secret patterns, UTF-8, JSON |
| `graduation-thesis-workflow/packages/graduation-thesis-claude-code.zip` | secret patterns, ZIP CRC/paths, package/source SHA-256 |
| `graduation-thesis-workflow/packages/graduation-thesis-codex.zip` | secret patterns, ZIP CRC/paths, package/source SHA-256 |
| `graduation-thesis-workflow/packages/graduation-thesis-workbuddy.zip` | secret patterns, ZIP CRC/paths, package/source SHA-256 |
| `graduation-thesis-workflow/scripts/install.ps1` | secret patterns, UTF-8 |
| `graduation-thesis-workflow/scripts/package.py` | secret patterns, UTF-8, Python syntax |
| `graduation-thesis-workflow/skills/graduation-thesis/SKILL.md` | secret patterns, UTF-8, local Markdown links |
| `graduation-thesis-workflow/skills/graduation-thesis/references/00-setup.md` | secret patterns, UTF-8, local Markdown links |
| `graduation-thesis-workflow/skills/graduation-thesis/references/01-grilling.md` | secret patterns, UTF-8, local Markdown links |
| `graduation-thesis-workflow/skills/graduation-thesis/references/02-design.md` | secret patterns, UTF-8, local Markdown links |
| `graduation-thesis-workflow/skills/graduation-thesis/references/03-literature.md` | secret patterns, UTF-8, local Markdown links |
| `graduation-thesis-workflow/skills/graduation-thesis/references/04-execution.md` | secret patterns, UTF-8, local Markdown links |
| `graduation-thesis-workflow/skills/graduation-thesis/references/05-writing.md` | secret patterns, UTF-8, local Markdown links |
| `graduation-thesis-workflow/skills/graduation-thesis/references/06-review.md` | secret patterns, UTF-8, local Markdown links |
| `graduation-thesis-workflow/skills/graduation-thesis/references/07-delivery.md` | secret patterns, UTF-8, local Markdown links |
| `graduation-thesis-workflow/skills/graduation-thesis/references/08-humanizer.md` | secret patterns, UTF-8, local Markdown links |
| `graduation-thesis-workflow/skills/graduation-thesis/references/09-accounting.md` | secret patterns, UTF-8, local Markdown links |
| `graduation-thesis-workflow/skills/graduation-thesis/references/contract.md` | secret patterns, UTF-8, local Markdown links |
| `graduation-thesis-workflow/skills/graduation-thesis/references/sources.md` | secret patterns, UTF-8, local Markdown links |
| `graduation-thesis-workflow/skills/graduation-thesis/references/vendor/humanizer/LICENSE` | secret patterns, UTF-8 |
| `graduation-thesis-workflow/skills/graduation-thesis/references/vendor/humanizer/SKILL.md` | secret patterns, UTF-8, local Markdown links |
| `graduation-thesis-workflow/skills/graduation-thesis/references/vendor/humanizer/UPSTREAM.json` | secret patterns, UTF-8, JSON |
| `graduation-thesis-workflow/skills/graduation-thesis/scripts/bootstrap-windows.ps1` | secret patterns, UTF-8 |
| `graduation-thesis-workflow/skills/graduation-thesis/scripts/literature.py` | secret patterns, UTF-8, Python syntax |
| `graduation-thesis-workflow/skills/graduation-thesis/scripts/polish_check.py` | secret patterns, UTF-8, Python syntax |
| `graduation-thesis-workflow/skills/graduation-thesis/scripts/project.py` | secret patterns, UTF-8, Python syntax |
| `graduation-thesis-workflow/tests/test_windows_setup.py` | secret patterns, UTF-8, Python syntax |
| `graduation-thesis-workflow/tests/test_workflow.py` | secret patterns, UTF-8, Python syntax |
| `rea/.gitignore` | secret patterns, UTF-8 |
| `rea/AGENTS.md` | secret patterns, UTF-8, local Markdown links |
| `rea/INSTALL.md` | secret patterns, UTF-8, local Markdown links |
| `rea/README.md` | secret patterns, UTF-8, local Markdown links |
| `rea/THIRD_PARTY.md` | secret patterns, UTF-8, local Markdown links |
| `rea/assets.json` | secret patterns, UTF-8, JSON |
| `rea/delivery/FILES.json` | secret patterns, UTF-8, JSON |
| `rea/delivery/SHA256SUMS.txt` | secret patterns, UTF-8 |
| `rea/delivery/rea.zip` | secret patterns, ZIP CRC/paths, package/source SHA-256 |
| `rea/profile/LICENSE` | secret patterns, UTF-8 |
| `rea/profile/README.md` | secret patterns, UTF-8, local Markdown links |
| `rea/restore.py` | secret patterns, UTF-8, Python syntax |
| `scripts/agent_entry_policy.py` | secret patterns, UTF-8, Python syntax |
| `scripts/check_repository.py` | secret patterns, UTF-8, Python syntax |
| `scripts/export_profile.py` | secret patterns, UTF-8, Python syntax |
| `scripts/package_projects.py` | secret patterns, UTF-8, Python syntax |
| `scripts/tests/test_packages.py` | secret patterns, UTF-8, Python syntax |
| `scripts/tests/test_pet_assets.py` | secret patterns, UTF-8, Python syntax |
| `scripts/tests/test_restore.py` | secret patterns, UTF-8, Python syntax |
| `scripts/verify_published.py` | secret patterns, UTF-8, Python syntax |
| `scripts/verify_runtime.py` | secret patterns, UTF-8, Python syntax |
| `today-todo/.gitignore` | secret patterns, UTF-8 |
| `today-todo/DESIGN.md` | secret patterns, UTF-8, local Markdown links |
| `today-todo/INSTALL.md` | secret patterns, UTF-8, local Markdown links |
| `today-todo/PLAN.md` | secret patterns, UTF-8, local Markdown links |
| `today-todo/README.md` | secret patterns, UTF-8, local Markdown links |
| `today-todo/SPEC.md` | secret patterns, UTF-8, local Markdown links |
| `today-todo/assets/app.ico` | secret patterns, ICO signature |
| `today-todo/delivery/FILES.json` | secret patterns, UTF-8, JSON |
| `today-todo/delivery/SHA256SUMS.txt` | secret patterns, UTF-8 |
| `today-todo/delivery/today-todo.zip` | secret patterns, ZIP CRC/paths, package/source SHA-256 |
| `today-todo/docs/VERIFY.md` | secret patterns, UTF-8, local Markdown links |
| `today-todo/docs/screenshots/composer-open.png` | secret patterns, image signature |
| `today-todo/docs/screenshots/desktop.png` | secret patterns, image signature |
| `today-todo/docs/screenshots/mobile.png` | secret patterns, image signature |
| `today-todo/package.json` | secret patterns, UTF-8, JSON |
| `today-todo/public/app.js` | secret patterns, UTF-8 |
| `today-todo/public/favicon.svg` | secret patterns, UTF-8, SVG XML |
| `today-todo/public/index.html` | secret patterns, UTF-8 |
| `today-todo/public/style.css` | secret patterns, UTF-8 |
| `today-todo/server.js` | secret patterns, UTF-8 |
| `today-todo/start.bat` | secret patterns, UTF-8 |
| `today-todo/stop.bat` | secret patterns, UTF-8 |
| `today-todo/test/api.test.js` | secret patterns, UTF-8 |
| `today-todo/tools/contrast.js` | secret patterns, UTF-8 |
| `today-todo/tools/make-icon.js` | secret patterns, UTF-8 |
| `today-todo/tools/shot.js` | secret patterns, UTF-8 |
| `yt-dlp/.gitignore` | secret patterns, UTF-8 |
| `yt-dlp/AGENTS.md` | secret patterns, UTF-8, local Markdown links |
| `yt-dlp/INSTALL.md` | secret patterns, UTF-8, local Markdown links |
| `yt-dlp/README.md` | secret patterns, UTF-8, local Markdown links |
| `yt-dlp/THIRD_PARTY.md` | secret patterns, UTF-8, local Markdown links |
| `yt-dlp/assets.json` | secret patterns, UTF-8, JSON |
| `yt-dlp/delivery/FILES.json` | secret patterns, UTF-8, JSON |
| `yt-dlp/delivery/SHA256SUMS.txt` | secret patterns, UTF-8 |
| `yt-dlp/delivery/yt-dlp.zip` | secret patterns, ZIP CRC/paths, package/source SHA-256 |
| `yt-dlp/profile/README.md` | secret patterns, UTF-8, local Markdown links |
| `yt-dlp/profile/download.cmd` | secret patterns, UTF-8 |
| `yt-dlp/restore.py` | secret patterns, UTF-8, Python syntax |

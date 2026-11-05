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
| `README.md` | secret patterns, UTF-8, local Markdown links |
| `daozai/.cargo/config.toml` | secret patterns, UTF-8, TOML |
| `daozai/.gitignore` | secret patterns, UTF-8 |
| `daozai/AGENTS.md` | secret patterns, UTF-8, local Markdown links |
| `daozai/CHANGELOG.md` | secret patterns, UTF-8, local Markdown links |
| `daozai/CONTRIBUTING.md` | secret patterns, UTF-8, local Markdown links |
| `daozai/Cargo.lock` | secret patterns, UTF-8 |
| `daozai/Cargo.toml` | secret patterns, UTF-8, TOML |
| `daozai/INSTALL.md` | secret patterns, UTF-8, local Markdown links |
| `daozai/LICENSE` | secret patterns, UTF-8 |
| `daozai/README.md` | secret patterns, UTF-8, local Markdown links |
| `daozai/SECURITY.md` | secret patterns, UTF-8, local Markdown links |
| `daozai/THIRD_PARTY.md` | secret patterns, UTF-8, local Markdown links |
| `daozai/THIRD_PARTY_NOTICES.txt` | secret patterns, UTF-8 |
| `daozai/app.rc` | secret patterns, UTF-8 |
| `daozai/assets.json` | secret patterns, UTF-8, JSON |
| `daozai/assets/ai-icons/README.md` | secret patterns, UTF-8, local Markdown links |
| `daozai/assets/ai-icons/claude.svg` | secret patterns, UTF-8, SVG XML |
| `daozai/assets/ai-icons/codex.svg` | secret patterns, UTF-8, SVG XML |
| `daozai/assets/ai-icons/deepseek.svg` | secret patterns, UTF-8, SVG XML |
| `daozai/assets/ai-icons/gemini.svg` | secret patterns, UTF-8, SVG XML |
| `daozai/assets/ai-icons/grokbot.svg` | secret patterns, UTF-8, SVG XML |
| `daozai/assets/ai-icons/kimi.svg` | secret patterns, UTF-8, SVG XML |
| `daozai/assets/ai-icons/lobe-icons-LICENSE.txt` | secret patterns, UTF-8 |
| `daozai/assets/ai-icons/workbuddy.svg` | secret patterns, UTF-8, SVG XML |
| `daozai/assets/ai-icons/zai.svg` | secret patterns, UTF-8, SVG XML |
| `daozai/assets/calendar/dingtalk.png` | secret patterns, image signature |
| `daozai/assets/calendar/feishu.svg` | secret patterns, UTF-8, SVG XML |
| `daozai/assets/calendar/mail.svg` | secret patterns, UTF-8, SVG XML |
| `daozai/assets/calendar/wecom.svg` | secret patterns, UTF-8, SVG XML |
| `daozai/assets/daozai-logo.png` | secret patterns, image signature |
| `daozai/assets/daozai.ico` | secret patterns, ICO signature |
| `daozai/assets/device-icons/LICENSE.txt` | secret patterns, UTF-8 |
| `daozai/assets/device-icons/bluetooth-linear.svg` | secret patterns, UTF-8, SVG XML |
| `daozai/assets/device-icons/gamepad-bold.svg` | secret patterns, UTF-8, SVG XML |
| `daozai/assets/device-icons/headphones-round-bold.svg` | secret patterns, UTF-8, SVG XML |
| `daozai/assets/device-icons/keyboard-bold.svg` | secret patterns, UTF-8, SVG XML |
| `daozai/assets/device-icons/mouse-bold.svg` | secret patterns, UTF-8, SVG XML |
| `daozai/assets/device-icons/smartphone-bold.svg` | secret patterns, UTF-8, SVG XML |
| `daozai/assets/device-icons/speaker-bold.svg` | secret patterns, UTF-8, SVG XML |
| `daozai/assets/settings-icons/LICENSE` | secret patterns, UTF-8 |
| `daozai/assets/settings-icons/calendar-days.svg` | secret patterns, UTF-8, SVG XML |
| `daozai/assets/settings-icons/folder-check.svg` | secret patterns, UTF-8, SVG XML |
| `daozai/assets/settings-icons/info.svg` | secret patterns, UTF-8, SVG XML |
| `daozai/assets/settings-icons/music-2.svg` | secret patterns, UTF-8, SVG XML |
| `daozai/assets/settings-icons/settings-2.svg` | secret patterns, UTF-8, SVG XML |
| `daozai/assets/settings-icons/system/about.svg` | secret patterns, UTF-8, SVG XML |
| `daozai/assets/settings-icons/system/focus.svg` | secret patterns, UTF-8, SVG XML |
| `daozai/assets/settings-icons/system/general.svg` | secret patterns, UTF-8, SVG XML |
| `daozai/assets/settings-icons/system/music.svg` | secret patterns, UTF-8, SVG XML |
| `daozai/assets/settings-icons/system/notifications.svg` | secret patterns, UTF-8, SVG XML |
| `daozai/assets/settings-icons/system/pages.svg` | secret patterns, UTF-8, SVG XML |
| `daozai/assets/settings-icons/system/quota.svg` | secret patterns, UTF-8, SVG XML |
| `daozai/assets/settings-icons/system/tasks.svg` | secret patterns, UTF-8, SVG XML |
| `daozai/assets/settings-icons/timer.svg` | secret patterns, UTF-8, SVG XML |
| `daozai/assets/support/daozai-coffee.svg` | secret patterns, UTF-8, SVG XML |
| `daozai/assets/support/support-alipay-original.jpg` | secret patterns, image signature |
| `daozai/assets/support/support-wechat-original.jpg` | secret patterns, image signature |
| `daozai/build.rs` | secret patterns, UTF-8 |
| `daozai/docs/DEPENDENCIES.md` | secret patterns, UTF-8, local Markdown links |
| `daozai/docs/PRIVACY.md` | secret patterns, UTF-8, local Markdown links |
| `daozai/docs/RELEASE-0.6.50-personal.md` | secret patterns, UTF-8, local Markdown links |
| `daozai/docs/USAGE.md` | secret patterns, UTF-8, local Markdown links |
| `daozai/docs/images/ai-quota.png` | secret patterns, image signature |
| `daozai/docs/images/calendar.png` | secret patterns, image signature |
| `daozai/docs/images/compact.png` | secret patterns, image signature |
| `daozai/docs/images/focus.png` | secret patterns, image signature |
| `daozai/docs/images/music.png` | secret patterns, image signature |
| `daozai/docs/images/reminder.png` | secret patterns, image signature |
| `daozai/docs/images/showcase-calendar.png` | secret patterns, image signature |
| `daozai/docs/images/showcase-daily.png` | secret patterns, image signature |
| `daozai/docs/images/showcase-hero.png` | secret patterns, image signature |
| `daozai/docs/images/showcase-work.png` | secret patterns, image signature |
| `daozai/docs/images/todo.png` | secret patterns, image signature |
| `daozai/docs/images/water.png` | secret patterns, image signature |
| `daozai/examples/background_soak.rs` | secret patterns, UTF-8 |
| `daozai/examples/lyrics_render_soak.rs` | secret patterns, UTF-8 |
| `daozai/examples/transparency_probe.rs` | secret patterns, UTF-8 |
| `daozai/examples/transparent_child_probe.rs` | secret patterns, UTF-8 |
| `daozai/installer/install.ps1` | secret patterns, UTF-8 |
| `daozai/installer/setup.nsi` | secret patterns, UTF-8 |
| `daozai/installer/uninstall.ps1` | secret patterns, UTF-8 |
| `daozai/installer/update.ps1` | secret patterns, UTF-8 |
| `daozai/packaging_tests/test_restore.py` | secret patterns, UTF-8, Python syntax |
| `daozai/profile/README.md` | secret patterns, UTF-8, local Markdown links |
| `daozai/restore.py` | secret patterns, UTF-8, Python syntax |
| `daozai/scripts/check-runtime.ps1` | secret patterns, UTF-8 |
| `daozai/scripts/get-nsis.ps1` | secret patterns, UTF-8 |
| `daozai/scripts/package.ps1` | secret patterns, UTF-8 |
| `daozai/src/anim.rs` | secret patterns, UTF-8 |
| `daozai/src/app.rs` | secret patterns, UTF-8 |
| `daozai/src/avoidance.rs` | secret patterns, UTF-8 |
| `daozai/src/bar_layout.rs` | secret patterns, UTF-8 |
| `daozai/src/bin/daozai-record/main.rs` | secret patterns, UTF-8 |
| `daozai/src/bin/daozai-record/raster.rs` | secret patterns, UTF-8 |
| `daozai/src/bt.rs` | secret patterns, UTF-8 |
| `daozai/src/calendar.rs` | secret patterns, UTF-8 |
| `daozai/src/calendar/exchange.rs` | secret patterns, UTF-8 |
| `daozai/src/calendar_editor.rs` | secret patterns, UTF-8 |
| `daozai/src/calendar_ui.rs` | secret patterns, UTF-8 |
| `daozai/src/claude_quota.rs` | secret patterns, UTF-8 |
| `daozai/src/collect.rs` | secret patterns, UTF-8 |
| `daozai/src/deepseek_quota.rs` | secret patterns, UTF-8 |
| `daozai/src/diagnostics.rs` | secret patterns, UTF-8 |
| `daozai/src/display_layout.rs` | secret patterns, UTF-8 |
| `daozai/src/extras.rs` | secret patterns, UTF-8 |
| `daozai/src/focus_bar.rs` | secret patterns, UTF-8 |
| `daozai/src/gemini_quota.rs` | secret patterns, UTF-8 |
| `daozai/src/glass.rs` | secret patterns, UTF-8 |
| `daozai/src/glm_quota.rs` | secret patterns, UTF-8 |
| `daozai/src/grok_quota.rs` | secret patterns, UTF-8 |
| `daozai/src/icons.rs` | secret patterns, UTF-8 |
| `daozai/src/input.rs` | secret patterns, UTF-8 |
| `daozai/src/kugou_cache.rs` | secret patterns, UTF-8 |
| `daozai/src/kugou_control.rs` | secret patterns, UTF-8 |
| `daozai/src/kugou_metadata.rs` | secret patterns, UTF-8 |
| `daozai/src/lib.rs` | secret patterns, UTF-8 |
| `daozai/src/local_calendar.rs` | secret patterns, UTF-8 |
| `daozai/src/lyrics.rs` | secret patterns, UTF-8 |
| `daozai/src/mail.rs` | secret patterns, UTF-8 |
| `daozai/src/mail_fetch.rs` | secret patterns, UTF-8 |
| `daozai/src/mail_privacy.rs` | secret patterns, UTF-8 |
| `daozai/src/mail_reader.rs` | secret patterns, UTF-8 |
| `daozai/src/main.rs` | secret patterns, UTF-8 |
| `daozai/src/model.rs` | secret patterns, UTF-8 |
| `daozai/src/native.rs` | secret patterns, UTF-8 |
| `daozai/src/native_auth.rs` | secret patterns, UTF-8 |
| `daozai/src/netease_playback.rs` | secret patterns, UTF-8 |
| `daozai/src/netease_timeline.rs` | secret patterns, UTF-8 |
| `daozai/src/otp.rs` | secret patterns, UTF-8 |
| `daozai/src/pages.rs` | secret patterns, UTF-8 |
| `daozai/src/paint.rs` | secret patterns, UTF-8 |
| `daozai/src/pet.rs` | secret patterns, UTF-8 |
| `daozai/src/player_seek.rs` | secret patterns, UTF-8 |
| `daozai/src/poll_clock.rs` | secret patterns, UTF-8 |
| `daozai/src/quota.rs` | secret patterns, UTF-8 |
| `daozai/src/quota_ui.rs` | secret patterns, UTF-8 |
| `daozai/src/resident_settings.rs` | secret patterns, UTF-8 |
| `daozai/src/settings_theme.rs` | secret patterns, UTF-8 |
| `daozai/src/shape.rs` | secret patterns, UTF-8 |
| `daozai/src/smtc.rs` | secret patterns, UTF-8 |
| `daozai/src/soda_cache.rs` | secret patterns, UTF-8 |
| `daozai/src/staging.rs` | secret patterns, UTF-8 |
| `daozai/src/system.rs` | secret patterns, UTF-8 |
| `daozai/src/task_picker.rs` | secret patterns, UTF-8 |
| `daozai/src/theme.rs` | secret patterns, UTF-8 |
| `daozai/src/tray.rs` | secret patterns, UTF-8 |
| `daozai/src/ui_tests.rs` | secret patterns, UTF-8 |
| `daozai/src/updates.rs` | secret patterns, UTF-8 |
| `daozai/src/workbuddy_quota.rs` | secret patterns, UTF-8 |
| `daozai/tests/black_skin.rs` | secret patterns, UTF-8 |
| `daozai/tests/calendar_credentials.rs` | secret patterns, UTF-8 |
| `daozai/tests/native_installer.ps1` | secret patterns, UTF-8 |
| `daozai/tests/performance.rs` | secret patterns, UTF-8 |
| `daozai/tests/update_installer.ps1` | secret patterns, UTF-8 |
| `daozai/vendor/eframe/Cargo.toml` | secret patterns, UTF-8, TOML |
| `daozai/vendor/eframe/Cargo.toml.orig` | secret patterns, UTF-8 |
| `daozai/vendor/eframe/LICENSE-APACHE` | secret patterns, UTF-8 |
| `daozai/vendor/eframe/LICENSE-MIT` | secret patterns, UTF-8 |
| `daozai/vendor/eframe/README.md` | secret patterns, UTF-8, local Markdown links |
| `daozai/vendor/eframe/data/icon.png` | secret patterns, image signature |
| `daozai/vendor/eframe/src/epi.rs` | secret patterns, UTF-8 |
| `daozai/vendor/eframe/src/icon_data.rs` | secret patterns, UTF-8 |
| `daozai/vendor/eframe/src/lib.rs` | secret patterns, UTF-8 |
| `daozai/vendor/eframe/src/native/app_icon.rs` | secret patterns, UTF-8 |
| `daozai/vendor/eframe/src/native/epi_integration.rs` | secret patterns, UTF-8 |
| `daozai/vendor/eframe/src/native/event_loop_context.rs` | secret patterns, UTF-8 |
| `daozai/vendor/eframe/src/native/file_storage.rs` | secret patterns, UTF-8 |
| `daozai/vendor/eframe/src/native/glow_integration.rs` | secret patterns, UTF-8 |
| `daozai/vendor/eframe/src/native/mod.rs` | secret patterns, UTF-8 |
| `daozai/vendor/eframe/src/native/run.rs` | secret patterns, UTF-8 |
| `daozai/vendor/eframe/src/native/wgpu_integration.rs` | secret patterns, UTF-8 |
| `daozai/vendor/eframe/src/native/winit_integration.rs` | secret patterns, UTF-8 |
| `daozai/vendor/eframe/src/stopwatch.rs` | secret patterns, UTF-8 |
| `daozai/vendor/eframe/src/web/app_runner.rs` | secret patterns, UTF-8 |
| `daozai/vendor/eframe/src/web/backend.rs` | secret patterns, UTF-8 |
| `daozai/vendor/eframe/src/web/events.rs` | secret patterns, UTF-8 |
| `daozai/vendor/eframe/src/web/input.rs` | secret patterns, UTF-8 |
| `daozai/vendor/eframe/src/web/mod.rs` | secret patterns, UTF-8 |
| `daozai/vendor/eframe/src/web/panic_handler.rs` | secret patterns, UTF-8 |
| `daozai/vendor/eframe/src/web/screen_reader.rs` | secret patterns, UTF-8 |
| `daozai/vendor/eframe/src/web/storage.rs` | secret patterns, UTF-8 |
| `daozai/vendor/eframe/src/web/text_agent.rs` | secret patterns, UTF-8 |
| `daozai/vendor/eframe/src/web/web_logger.rs` | secret patterns, UTF-8 |
| `daozai/vendor/eframe/src/web/web_painter.rs` | secret patterns, UTF-8 |
| `daozai/vendor/eframe/src/web/web_painter_glow.rs` | secret patterns, UTF-8 |
| `daozai/vendor/eframe/src/web/web_painter_wgpu.rs` | secret patterns, UTF-8 |
| `daozai/vendor/eframe/src/web/web_runner.rs` | secret patterns, UTF-8 |
| `daozai/vendor/imap-proto/Cargo.toml` | secret patterns, UTF-8, TOML |
| `daozai/vendor/imap-proto/Cargo.toml.orig` | secret patterns, UTF-8 |
| `daozai/vendor/imap-proto/src/body.rs` | secret patterns, UTF-8 |
| `daozai/vendor/imap-proto/src/body_structure.rs` | secret patterns, UTF-8 |
| `daozai/vendor/imap-proto/src/builders/command.rs` | secret patterns, UTF-8 |
| `daozai/vendor/imap-proto/src/builders/mod.rs` | secret patterns, UTF-8 |
| `daozai/vendor/imap-proto/src/core.rs` | secret patterns, UTF-8 |
| `daozai/vendor/imap-proto/src/lib.rs` | secret patterns, UTF-8 |
| `daozai/vendor/imap-proto/src/macros.rs` | secret patterns, UTF-8 |
| `daozai/vendor/imap-proto/src/parser/mod.rs` | secret patterns, UTF-8 |
| `daozai/vendor/imap-proto/src/parser/rfc3501.rs` | secret patterns, UTF-8 |
| `daozai/vendor/imap-proto/src/parser/rfc4551.rs` | secret patterns, UTF-8 |
| `daozai/vendor/imap-proto/src/parser/rfc5464.rs` | secret patterns, UTF-8 |
| `daozai/vendor/imap-proto/src/types.rs` | secret patterns, UTF-8 |
| `daozai/vendor/imap/.cirrus.yml` | secret patterns, UTF-8 |
| `daozai/vendor/imap/.gitignore` | secret patterns, UTF-8 |
| `daozai/vendor/imap/CHANGELOG.md` | secret patterns, UTF-8, local Markdown links |
| `daozai/vendor/imap/Cargo.toml` | secret patterns, UTF-8, TOML |
| `daozai/vendor/imap/Cargo.toml.orig` | secret patterns, UTF-8 |
| `daozai/vendor/imap/LICENSE-APACHE` | secret patterns, UTF-8 |
| `daozai/vendor/imap/LICENSE-MIT` | secret patterns, UTF-8 |
| `daozai/vendor/imap/README.md` | secret patterns, UTF-8, local Markdown links |
| `daozai/vendor/imap/README.tpl` | secret patterns, UTF-8 |
| `daozai/vendor/imap/azure-pipelines.yml` | secret patterns, UTF-8 |
| `daozai/vendor/imap/examples/README.md` | secret patterns, UTF-8, local Markdown links |
| `daozai/vendor/imap/examples/basic.rs` | secret patterns, UTF-8 |
| `daozai/vendor/imap/examples/gmail_oauth2.rs` | secret patterns, UTF-8 |
| `daozai/vendor/imap/examples/rustls.rs` | secret patterns, UTF-8 |
| `daozai/vendor/imap/examples/starttls.rs` | secret patterns, UTF-8 |
| `daozai/vendor/imap/examples/timeout.rs` | secret patterns, UTF-8 |
| `daozai/vendor/imap/src/authenticator.rs` | secret patterns, UTF-8 |
| `daozai/vendor/imap/src/client.rs` | secret patterns, UTF-8 |
| `daozai/vendor/imap/src/error.rs` | secret patterns, UTF-8 |
| `daozai/vendor/imap/src/extensions/idle.rs` | secret patterns, UTF-8 |
| `daozai/vendor/imap/src/extensions/mod.rs` | secret patterns, UTF-8 |
| `daozai/vendor/imap/src/lib.rs` | secret patterns, UTF-8 |
| `daozai/vendor/imap/src/mock_stream.rs` | secret patterns, UTF-8 |
| `daozai/vendor/imap/src/parse.rs` | secret patterns, UTF-8 |
| `daozai/vendor/imap/src/types/capabilities.rs` | secret patterns, UTF-8 |
| `daozai/vendor/imap/src/types/fetch.rs` | secret patterns, UTF-8 |
| `daozai/vendor/imap/src/types/mailbox.rs` | secret patterns, UTF-8 |
| `daozai/vendor/imap/src/types/mod.rs` | secret patterns, UTF-8 |
| `daozai/vendor/imap/src/types/name.rs` | secret patterns, UTF-8 |
| `daozai/vendor/imap/tests/imap_integration.rs` | secret patterns, UTF-8 |
| `dca-calculator/.gitattributes` | secret patterns, UTF-8 |
| `dca-calculator/.gitignore` | secret patterns, UTF-8 |
| `dca-calculator/AGENTS.md` | secret patterns, UTF-8, local Markdown links |
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
| `dca-calculator/backend/requirements-runtime.txt` | secret patterns, UTF-8 |
| `dca-calculator/backend/requirements.txt` | secret patterns, UTF-8 |
| `dca-calculator/backend/tools/verify_data_sources.py` | secret patterns, UTF-8, Python syntax |
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
| `dca-calculator/runtime/start.cmd` | secret patterns, UTF-8 |
| `dca-calculator/scripts/start_backend.bat` | secret patterns, UTF-8 |
| `dca-calculator/scripts/start_frontend.bat` | secret patterns, UTF-8 |
| `dca-calculator/tests/screenshots/e2e_evening_1234.56.png` | secret patterns, image signature |
| `dca-calculator/tests/screenshots/e2e_no_amount.png` | secret patterns, image signature |
| `dca-calculator/tests/screenshots/e2e_with_amount.png` | secret patterns, image signature |
| `docs/AGENT_DELIVERY_STANDARD.md` | secret patterns, UTF-8, local Markdown links |
| `docs/FILE_AUDIT.md` | secret patterns, UTF-8, local Markdown links |
| `docs/REPOSITORY_CLEANUP_REPORT.md` | secret patterns, UTF-8, local Markdown links |
| `docs/REPOSITORY_SYNC_2026-10-24.md` | secret patterns, UTF-8, local Markdown links |
| `docs/REPOSITORY_SYNC_2026-11-01.md` | secret patterns, UTF-8, local Markdown links |
| `docs/TOOL_PROFILE_HISTORY_2026-10-22.md` | secret patterns, UTF-8, local Markdown links |
| `docs/UPSTREAM_SYNC_2026-11-05.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/.gitattributes` | secret patterns, UTF-8 |
| `flyingmouse-format/.github/workflows/ci.yml` | secret patterns, UTF-8 |
| `flyingmouse-format/.github/workflows/prepare-macos-engines.yml` | secret patterns, UTF-8 |
| `flyingmouse-format/.github/workflows/release.yml` | secret patterns, UTF-8 |
| `flyingmouse-format/.gitignore` | secret patterns, UTF-8 |
| `flyingmouse-format/AGENTS.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/INSTALL.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/LICENSE` | secret patterns, UTF-8 |
| `flyingmouse-format/README.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/THIRD_PARTY.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/THIRD_PARTY_NOTICES.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/agent-skill-installer.js` | secret patterns, UTF-8 |
| `flyingmouse-format/agent-skill/flyingmouse-format/SKILL.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/agent-skill/flyingmouse-format/agents/openai.yaml` | secret patterns, UTF-8 |
| `flyingmouse-format/agent-skill/flyingmouse-format/scripts/flyingmouse-format.js` | secret patterns, UTF-8 |
| `flyingmouse-format/bin/avs3/THIRD_PARTY_NOTICE.txt` | secret patterns, UTF-8 |
| `flyingmouse-format/bin/avs3/model.bin` | secret patterns, binary blob |
| `flyingmouse-format/bmp-input.js` | secret patterns, UTF-8 |
| `flyingmouse-format/bmp-output.js` | secret patterns, UTF-8 |
| `flyingmouse-format/build/appx/Square150x150Logo.png` | secret patterns, image signature |
| `flyingmouse-format/build/appx/Square44x44Logo.png` | secret patterns, image signature |
| `flyingmouse-format/build/appx/StoreLogo.png` | secret patterns, image signature |
| `flyingmouse-format/build/appx/Wide310x150Logo.png` | secret patterns, image signature |
| `flyingmouse-format/build/icon.png` | secret patterns, image signature |
| `flyingmouse-format/build/license.txt` | secret patterns, UTF-8 |
| `flyingmouse-format/ci-engines-v1.json` | secret patterns, UTF-8, JSON |
| `flyingmouse-format/cli.js` | secret patterns, UTF-8 |
| `flyingmouse-format/config.js` | secret patterns, UTF-8 |
| `flyingmouse-format/conversion-cancellation.js` | secret patterns, UTF-8 |
| `flyingmouse-format/conversion-progress.js` | secret patterns, UTF-8 |
| `flyingmouse-format/design-export.js` | secret patterns, UTF-8 |
| `flyingmouse-format/desktop-recovery.js` | secret patterns, UTF-8 |
| `flyingmouse-format/desktop-shutdown.js` | secret patterns, UTF-8 |
| `flyingmouse-format/diagnostics.js` | secret patterns, UTF-8 |
| `flyingmouse-format/docs/ARCHITECTURE.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/AUDIT-PDF-20260928.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/HANDOFF.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/RELEASE.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/REPAIR-0.7.1.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/REPAIR-0.7.10.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/REPAIR-0.7.11.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/REPAIR-0.7.2.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/REPAIR-0.7.3.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/REPAIR-0.7.4.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/REPAIR-0.7.5.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/REPAIR-0.7.6.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/REPAIR-0.7.8.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/REPAIR-0.7.9.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/REPAIR-EXCEL-PRECISION-20260923.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/REPAIR-OFD-20261002.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/REPAIR-PDF-DOCX-20261015.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/REPAIR-PDF-FIDELITY-20260928.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/REPAIR-PDF-ILLUSTRATIONS-20260928.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/audit-070-fixes.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/privacy-policy.html` | secret patterns, UTF-8 |
| `flyingmouse-format/docs/release-notes-0.6.10.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/release-notes-039.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/release-notes-040.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/release-notes-041.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/release-notes-050.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/release-notes-051.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/release-notes-052.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/release-notes-060.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/release-notes-061.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/release-notes-062.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/release-notes-063.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/release-notes-064.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/release-notes-065.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/release-notes-067.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/release-notes-069.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/release-notes-070.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/release-notes-0710.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/release-notes-0711.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/release-notes-073.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/release-notes-078.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/release-notes-083.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/releases/v0.3.5.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/superpowers/plans/2026-08-08-win7-compat-release.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/superpowers/plans/2026-08-10-v0.3.4-conversion-macos-release.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/superpowers/plans/2026-08-10-v0.3.4-settings-office-reliability.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/superpowers/plans/2026-08-13-scanned-pdf-office-repair.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/superpowers/specs/2026-08-08-win7-compat-release-design.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/superpowers/specs/2026-08-10-v0.3.4-quality-macos-design.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/superpowers/specs/2026-08-13-scanned-pdf-office-design.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/v0.3.6-商店上传校验.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/v0.5.0-商店上传校验.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/上架材料包.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/分发与合规规范.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/微软商店上架清单.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/酷狗KGG密钥库手动指定教程.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docstructure-engine-lock.json` | secret patterns, UTF-8, JSON |
| `flyingmouse-format/ebook.js` | secret patterns, UTF-8 |
| `flyingmouse-format/electron-main.js` | secret patterns, UTF-8 |
| `flyingmouse-format/electron-security.js` | secret patterns, UTF-8 |
| `flyingmouse-format/engine-smoke-validator.js` | secret patterns, UTF-8 |
| `flyingmouse-format/ico-format.js` | secret patterns, UTF-8 |
| `flyingmouse-format/image-conversion.js` | secret patterns, UTF-8 |
| `flyingmouse-format/image.js` | secret patterns, UTF-8 |
| `flyingmouse-format/libraw-engine-lock.json` | secret patterns, UTF-8, JSON |
| `flyingmouse-format/logger.js` | secret patterns, UTF-8 |
| `flyingmouse-format/markdown-asset-references.js` | secret patterns, UTF-8 |
| `flyingmouse-format/markdown-document.js` | secret patterns, UTF-8 |
| `flyingmouse-format/markdown-math.js` | secret patterns, UTF-8 |
| `flyingmouse-format/media.js` | secret patterns, UTF-8 |
| `flyingmouse-format/native/build.cmd` | secret patterns, UTF-8 |
| `flyingmouse-format/native/launcher.cpp` | secret patterns, UTF-8 |
| `flyingmouse-format/native/startup-access.h` | secret patterns, UTF-8 |
| `flyingmouse-format/ocr.js` | secret patterns, UTF-8 |
| `flyingmouse-format/ofd-convert.js` | secret patterns, UTF-8 |
| `flyingmouse-format/ofd-renderer.js` | secret patterns, UTF-8 |
| `flyingmouse-format/office-convert.js` | secret patterns, UTF-8 |
| `flyingmouse-format/office-engine.js` | secret patterns, UTF-8 |
| `flyingmouse-format/office-process.js` | secret patterns, UTF-8 |
| `flyingmouse-format/office-quality.js` | secret patterns, UTF-8 |
| `flyingmouse-format/office-readiness.js` | secret patterns, UTF-8 |
| `flyingmouse-format/office-runtime.js` | secret patterns, UTF-8 |
| `flyingmouse-format/office-smoke-runner.js` | secret patterns, UTF-8 |
| `flyingmouse-format/owned-tasks.js` | secret patterns, UTF-8 |
| `flyingmouse-format/package-lock.json` | secret patterns, UTF-8, JSON |
| `flyingmouse-format/package.json` | secret patterns, UTF-8, JSON |
| `flyingmouse-format/pandoc-engine-lock.json` | secret patterns, UTF-8, JSON |
| `flyingmouse-format/pdf-classifier.js` | secret patterns, UTF-8 |
| `flyingmouse-format/pdf-inline-image-docx.js` | secret patterns, UTF-8 |
| `flyingmouse-format/pdf-inline-text-style.js` | secret patterns, UTF-8 |
| `flyingmouse-format/pdf-input.js` | secret patterns, UTF-8 |
| `flyingmouse-format/pdf-native-illustrations.js` | secret patterns, UTF-8 |
| `flyingmouse-format/pdf-native-math.js` | secret patterns, UTF-8 |
| `flyingmouse-format/pdf-ocr-regions.js` | secret patterns, UTF-8 |
| `flyingmouse-format/pdf-office-docx.js` | secret patterns, UTF-8 |
| `flyingmouse-format/pdf-office-xlsx.js` | secret patterns, UTF-8 |
| `flyingmouse-format/pdf-render-workspace.js` | secret patterns, UTF-8 |
| `flyingmouse-format/pdf-scan-columns.js` | secret patterns, UTF-8 |
| `flyingmouse-format/pdf-structure-contract.js` | secret patterns, UTF-8 |
| `flyingmouse-format/pdf-structure-engine.js` | secret patterns, UTF-8 |
| `flyingmouse-format/pdf-structure-score.js` | secret patterns, UTF-8 |
| `flyingmouse-format/pdf-table-extractor.js` | secret patterns, UTF-8 |
| `flyingmouse-format/pdf-table-runtime.js` | secret patterns, UTF-8 |
| `flyingmouse-format/pdf-table.js` | secret patterns, UTF-8 |
| `flyingmouse-format/pdf-text-render-style.js` | secret patterns, UTF-8 |
| `flyingmouse-format/pdf.js` | secret patterns, UTF-8 |
| `flyingmouse-format/pdfjs.js` | secret patterns, UTF-8 |
| `flyingmouse-format/pe-metadata.js` | secret patterns, UTF-8 |
| `flyingmouse-format/preload.js` | secret patterns, UTF-8 |
| `flyingmouse-format/public/app.js` | secret patterns, UTF-8 |
| `flyingmouse-format/public/assets/app-icon.svg` | secret patterns, UTF-8, SVG XML |
| `flyingmouse-format/public/assets/mouse-format/mouse-analyzing.png` | secret patterns, image signature |
| `flyingmouse-format/public/assets/mouse-format/mouse-batch.png` | secret patterns, image signature |
| `flyingmouse-format/public/assets/mouse-format/mouse-converting.png` | secret patterns, image signature |
| `flyingmouse-format/public/assets/mouse-format/mouse-error.png` | secret patterns, image signature |
| `flyingmouse-format/public/assets/mouse-format/mouse-idle.png` | secret patterns, image signature |
| `flyingmouse-format/public/assets/mouse-format/mouse-ocr.png` | secret patterns, image signature |
| `flyingmouse-format/public/assets/mouse-format/mouse-pdf-pages.png` | secret patterns, image signature |
| `flyingmouse-format/public/assets/mouse-format/mouse-success.png` | secret patterns, image signature |
| `flyingmouse-format/public/assets/mouse-format/mouse-upload.png` | secret patterns, image signature |
| `flyingmouse-format/public/assets/mouse-format/source-mouse-avatar.png` | secret patterns, image signature |
| `flyingmouse-format/public/assets/screenshots/home.png` | secret patterns, image signature |
| `flyingmouse-format/public/assets/sponsor-qr.jpg` | secret patterns, image signature |
| `flyingmouse-format/public/conversion-preferences.js` | secret patterns, UTF-8 |
| `flyingmouse-format/public/i18n.js` | secret patterns, UTF-8 |
| `flyingmouse-format/public/index.html` | secret patterns, UTF-8 |
| `flyingmouse-format/public/settings-sync.js` | secret patterns, UTF-8 |
| `flyingmouse-format/public/styles.css` | secret patterns, UTF-8 |
| `flyingmouse-format/public/theme.js` | secret patterns, UTF-8 |
| `flyingmouse-format/release-installer/install.cmd` | secret patterns, UTF-8 |
| `flyingmouse-format/release-installer/install.ps1` | secret patterns, UTF-8 |
| `flyingmouse-format/resource-policy.js` | secret patterns, UTF-8 |
| `flyingmouse-format/runtime-paths.js` | secret patterns, UTF-8 |
| `flyingmouse-format/save-converted-result.js` | secret patterns, UTF-8 |
| `flyingmouse-format/save-dialog.js` | secret patterns, UTF-8 |
| `flyingmouse-format/save-download.js` | secret patterns, UTF-8 |
| `flyingmouse-format/scripts/attach-windows-launcher.js` | secret patterns, UTF-8 |
| `flyingmouse-format/scripts/build-appx.ps1` | secret patterns, UTF-8 |
| `flyingmouse-format/scripts/build-docstructure-engine.ps1` | secret patterns, UTF-8 |
| `flyingmouse-format/scripts/build-engine-manifest.js` | secret patterns, UTF-8 |
| `flyingmouse-format/scripts/build-mouse-format-assets.js` | secret patterns, UTF-8 |
| `flyingmouse-format/scripts/build-win7.js` | secret patterns, UTF-8 |
| `flyingmouse-format/scripts/build-windows-lite.js` | secret patterns, UTF-8 |
| `flyingmouse-format/scripts/check-appx.py` | secret patterns, UTF-8, Python syntax |
| `flyingmouse-format/scripts/check-public-package.js` | secret patterns, UTF-8 |
| `flyingmouse-format/scripts/distribution-filters.js` | secret patterns, UTF-8 |
| `flyingmouse-format/scripts/fetch-runtime-asset.py` | secret patterns, UTF-8, Python syntax |
| `flyingmouse-format/scripts/fix-pe-dangling-cert.py` | secret patterns, UTF-8, Python syntax |
| `flyingmouse-format/scripts/gen-appx-logos.js` | secret patterns, UTF-8 |
| `flyingmouse-format/scripts/inspect-pe.js` | secret patterns, UTF-8 |
| `flyingmouse-format/scripts/lock-docstructure-engine.js` | secret patterns, UTF-8 |
| `flyingmouse-format/scripts/patch-dependency-compat.js` | secret patterns, UTF-8 |
| `flyingmouse-format/scripts/prepare-windows-package.js` | secret patterns, UTF-8 |
| `flyingmouse-format/scripts/release-update.sh` | secret patterns, UTF-8 |
| `flyingmouse-format/scripts/release-version-sync.js` | secret patterns, UTF-8 |
| `flyingmouse-format/scripts/rename-opc-reserved.py` | secret patterns, UTF-8, Python syntax |
| `flyingmouse-format/scripts/restore-ci-engines.ps1` | secret patterns, UTF-8 |
| `flyingmouse-format/scripts/restore-libraw.js` | secret patterns, UTF-8 |
| `flyingmouse-format/scripts/restore-pandoc.js` | secret patterns, UTF-8 |
| `flyingmouse-format/scripts/scan-pe-cert-dangling.py` | secret patterns, UTF-8, Python syntax |
| `flyingmouse-format/scripts/trim-qpdf-distribution.js` | secret patterns, UTF-8 |
| `flyingmouse-format/scripts/validate-ci-engines.js` | secret patterns, UTF-8 |
| `flyingmouse-format/server.js` | secret patterns, UTF-8 |
| `flyingmouse-format/settings-store.js` | secret patterns, UTF-8 |
| `flyingmouse-format/store-engine-cache.js` | secret patterns, UTF-8 |
| `flyingmouse-format/store-engine-worker.js` | secret patterns, UTF-8 |
| `flyingmouse-format/subtitles.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/agent-skill-installer.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/bmp-input.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/bmp-output.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/build-engine-manifest.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/capability-refresh.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/check_appx_test.py` | secret patterns, UTF-8, Python syntax |
| `flyingmouse-format/tests/ci-engine-release.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/cli-runtime-cleanup.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/cli.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/conversion-audit-regressions.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/conversion-integrity.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/conversion-preferences.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/conversion-progress-http.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/conversion-progress.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/conversion.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/dependency-compatibility.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/dependency-patch.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/desktop-entry-compat.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/desktop-recovery.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/desktop-shutdown.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/desktop-startup.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/diagnostics-export.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/diagnostics.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/distribution-footprint.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/download-release.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/ebook-integrity.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/ebook-large-text.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/ebook.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/electron-hardening-static.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/electron-security.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/fixtures/ofd/blank-image-declared-but-missing.ofd` | secret patterns, ZIP CRC/paths, package/source SHA-256 |
| `flyingmouse-format/tests/fixtures/ofd/blank-image-resource-baseloc.ofd` | secret patterns, ZIP CRC/paths, package/source SHA-256 |
| `flyingmouse-format/tests/fixtures/ofd/blank-page-different-namespace-prefix.ofd` | secret patterns, ZIP CRC/paths, package/source SHA-256 |
| `flyingmouse-format/tests/fixtures/ofd/blank-text-hidden-by-reordered-background.ofd` | secret patterns, ZIP CRC/paths, package/source SHA-256 |
| `flyingmouse-format/tests/fixtures/ofd/control-background-separate-layer.ofd` | secret patterns, ZIP CRC/paths, package/source SHA-256 |
| `flyingmouse-format/tests/fixtures/ofd/control-image-flat-path.ofd` | secret patterns, ZIP CRC/paths, package/source SHA-256 |
| `flyingmouse-format/tests/fixtures/ofd/control-text.ofd` | secret patterns, ZIP CRC/paths, package/source SHA-256 |
| `flyingmouse-format/tests/fixtures/ofd/missing-only-page-xml.ofd` | secret patterns, ZIP CRC/paths, package/source SHA-256 |
| `flyingmouse-format/tests/fixtures/structure-manifest-v1.json` | secret patterns, UTF-8, JSON |
| `flyingmouse-format/tests/helpers/office-processes.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/helpers/scanned-pdf-fixture.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/helpers/ui-page-harness.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/i18n.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/ico-format.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/image-conversion.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/image-merge-regressions.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/libraw-restore.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/logger.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/macos-packaging.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/markdown-document.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/media-codec.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/mouse-assets.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/ocr-merge.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/ocr-page-diagnostics.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/ocr-quality.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/ofd-boundary.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/ofd-convert.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/ofd-http-integrity.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/ofd-renderer.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/ofd-visible-output.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/office-crc-repair.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/office-engine.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/office-process-attribution.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/office-process.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/office-quality.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/office-readiness.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/office-wps-repair.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pandoc-engine.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf-classifier.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf-content-fidelity.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf-fidelity-integration.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf-form-fidelity.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf-form-layout.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf-inline-content-order.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf-inline-image-docx.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf-inline-image-routing.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf-inline-line-fidelity.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf-inline-text-style.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf-native-illustrations.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf-native-layout-regression.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf-native-math.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf-ocr-native-merge.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf-ocr-regions.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf-office-docx.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf-office-xlsx.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf-page-completeness.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf-request-cancellation.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf-scan-columns.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf-scanned-routing.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf-structure-contract.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf-structure-engine.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf-structure-score.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf-table-extractor.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf-table-runtime.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf-table-source-style.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf-table-writer.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf-text-render-style.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf2docx.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pe-metadata.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/preview.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/process-output.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/public-package.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/raw-input.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/release-version-sync-atomic.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/release-version-sync.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/resource-error-http.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/resource-policy.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/runtime-cleanup.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/runtime-paths.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/save-converted-result.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/save-dialog.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/save-download.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/settings-degrade-ui.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/settings-store.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/settings-sync.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/store-capabilities.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/store-engine-cache.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/subtitles.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/text-conversion-integration.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/text-conversion.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/text-encoding.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/text-fidelity-regression.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/tga-input.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/ui-error-recovery.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/ui-operation-lifecycle.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/ui-progress.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/ui-queue-lifecycle.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/ui-static.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/ui-text-encoding.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/upload-budget.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/utils.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/win7-build-profile.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/win7-build-script.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/windows-lite-profile.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/xlsx-normal-font.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/xml-json.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/zip-util.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/text-conversion.js` | secret patterns, UTF-8 |
| `flyingmouse-format/text-docx.js` | secret patterns, UTF-8 |
| `flyingmouse-format/text-encoding.js` | secret patterns, UTF-8 |
| `flyingmouse-format/third-party/dependency-patches/NOTICE.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/third-party/dependency-patches/exceljs-LICENSE` | secret patterns, UTF-8 |
| `flyingmouse-format/third-party/dependency-patches/exceljs-parse-sax-compat.json` | secret patterns, UTF-8, JSON |
| `flyingmouse-format/third-party/dependency-patches/exceljs-stream-buf-compat.json` | secret patterns, UTF-8, JSON |
| `flyingmouse-format/third-party/dependency-patches/exceljs-workbook-reader-compat.json` | secret patterns, UTF-8, JSON |
| `flyingmouse-format/third-party/dependency-patches/temp-LICENSE` | secret patterns, UTF-8 |
| `flyingmouse-format/third-party/dependency-patches/temp-rimraf-compat.json` | secret patterns, UTF-8, JSON |
| `flyingmouse-format/third-party/ofd-to-pdf/LICENSE` | secret patterns, UTF-8 |
| `flyingmouse-format/third-party/ofd-to-pdf/NOTICE.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/third_party/libraw/Microsoft-VC143-Redist.txt` | secret patterns, UTF-8 |
| `flyingmouse-format/third_party/pandoc/COPYING.rtf` | secret patterns, UTF-8 |
| `flyingmouse-format/third_party/pandoc/COPYRIGHT.txt` | secret patterns, UTF-8 |
| `flyingmouse-format/tools/docstructure-engine/docstructure-engine.spec` | secret patterns, UTF-8, Python syntax |
| `flyingmouse-format/tools/docstructure-engine/flyingmouse_docstructure/__init__.py` | secret patterns, UTF-8, Python syntax |
| `flyingmouse-format/tools/docstructure-engine/flyingmouse_docstructure/__main__.py` | secret patterns, UTF-8, Python syntax |
| `flyingmouse-format/tools/docstructure-engine/flyingmouse_docstructure/img2table_adapter.py` | secret patterns, UTF-8, Python syntax |
| `flyingmouse-format/tools/docstructure-engine/flyingmouse_docstructure/normalize.py` | secret patterns, UTF-8, Python syntax |
| `flyingmouse-format/tools/docstructure-engine/flyingmouse_docstructure/pipeline.py` | secret patterns, UTF-8, Python syntax |
| `flyingmouse-format/tools/docstructure-engine/requirements-build.in` | secret patterns, UTF-8 |
| `flyingmouse-format/tools/docstructure-engine/requirements-build.lock` | secret patterns, UTF-8 |
| `flyingmouse-format/tools/docstructure-engine/requirements-win-x64.in` | secret patterns, UTF-8 |
| `flyingmouse-format/tools/docstructure-engine/requirements-win-x64.lock` | secret patterns, UTF-8 |
| `flyingmouse-format/tools/docstructure-engine/tests/test_cli.py` | secret patterns, UTF-8, Python syntax |
| `flyingmouse-format/tools/docstructure-engine/tests/test_img2table_adapter.py` | secret patterns, UTF-8, Python syntax |
| `flyingmouse-format/tools/docstructure-engine/tests/test_normalize.py` | secret patterns, UTF-8, Python syntax |
| `flyingmouse-format/tools/docstructure-engine/tests/test_pipeline.py` | secret patterns, UTF-8, Python syntax |
| `flyingmouse-format/tools/docstructure-engine/tests/test_preflight.py` | secret patterns, UTF-8, Python syntax |
| `flyingmouse-format/tools/docstructure-engine/tests/test_spec.py` | secret patterns, UTF-8, Python syntax |
| `flyingmouse-format/tools/docstructure-engine/windows-utf8.manifest` | secret patterns, UTF-8 |
| `flyingmouse-format/upload-budget.js` | secret patterns, UTF-8 |
| `flyingmouse-format/utils.js` | secret patterns, UTF-8 |
| `flyingmouse-format/win7-build-profile.js` | secret patterns, UTF-8 |
| `flyingmouse-format/win7-package-lock.json` | secret patterns, UTF-8, JSON |
| `flyingmouse-format/windows-lite-profile.js` | secret patterns, UTF-8 |
| `flyingmouse-format/xlsx-normal-font.js` | secret patterns, UTF-8 |
| `flyingmouse-format/xml-json.js` | secret patterns, UTF-8 |
| `flyingmouse-format/zip-util.js` | secret patterns, UTF-8 |
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
| `graduation-thesis-workflow/docs/COMPATIBILITY.md` | secret patterns, UTF-8, local Markdown links |
| `graduation-thesis-workflow/docs/INSTALL.md` | secret patterns, UTF-8, local Markdown links |
| `graduation-thesis-workflow/docs/RELEASE.md` | secret patterns, UTF-8, local Markdown links |
| `graduation-thesis-workflow/docs/UPSTREAM_REVIEW.md` | secret patterns, UTF-8, local Markdown links |
| `graduation-thesis-workflow/docs/VALIDATION.md` | secret patterns, UTF-8, local Markdown links |
| `graduation-thesis-workflow/scripts/build_delivery.py` | secret patterns, UTF-8, Python syntax |
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
| `graduation-thesis-workflow/skills/graduation-thesis/references/vendor/humanizer-zh/LICENSE` | secret patterns, UTF-8 |
| `graduation-thesis-workflow/skills/graduation-thesis/references/vendor/humanizer-zh/SKILL.md` | secret patterns, UTF-8, local Markdown links |
| `graduation-thesis-workflow/skills/graduation-thesis/references/vendor/humanizer-zh/UPSTREAM.json` | secret patterns, UTF-8, JSON |
| `graduation-thesis-workflow/skills/graduation-thesis/scripts/bootstrap-windows.ps1` | secret patterns, UTF-8 |
| `graduation-thesis-workflow/skills/graduation-thesis/scripts/literature.py` | secret patterns, UTF-8, Python syntax |
| `graduation-thesis-workflow/skills/graduation-thesis/scripts/polish_check.py` | secret patterns, UTF-8, Python syntax |
| `graduation-thesis-workflow/skills/graduation-thesis/scripts/project.py` | secret patterns, UTF-8, Python syntax |
| `graduation-thesis-workflow/tests/test_windows_setup.py` | secret patterns, UTF-8, Python syntax |
| `graduation-thesis-workflow/tests/test_workflow.py` | secret patterns, UTF-8, Python syntax |
| `libretv/.gitignore` | secret patterns, UTF-8 |
| `libretv/AGENTS.md` | secret patterns, UTF-8, local Markdown links |
| `libretv/INSTALL.md` | secret patterns, UTF-8, local Markdown links |
| `libretv/README.md` | secret patterns, UTF-8, local Markdown links |
| `libretv/SECURITY_PATCHES.md` | secret patterns, UTF-8, local Markdown links |
| `libretv/THIRD_PARTY.md` | secret patterns, UTF-8, local Markdown links |
| `libretv/assets.json` | secret patterns, UTF-8, JSON |
| `libretv/profile/LICENSE` | secret patterns, UTF-8 |
| `libretv/profile/defaults.json` | secret patterns, UTF-8, JSON |
| `libretv/profile/launcher.mjs` | secret patterns, UTF-8 |
| `libretv/profile/notify.vbs` | secret patterns, UTF-8 |
| `libretv/profile/open-browser.ps1` | secret patterns, UTF-8 |
| `libretv/profile/rebuild.cmd` | secret patterns, UTF-8 |
| `libretv/profile/start.vbs` | secret patterns, UTF-8 |
| `libretv/profile/stop.mjs` | secret patterns, UTF-8 |
| `libretv/profile/stop.vbs` | secret patterns, UTF-8 |
| `libretv/restore.py` | secret patterns, UTF-8, Python syntax |
| `libretv/runtime/start.cmd` | secret patterns, UTF-8 |
| `libretv/runtime/start.mjs` | secret patterns, UTF-8 |
| `libretv/source-files.json` | secret patterns, UTF-8, JSON |
| `libretv/source/.dockerignore` | secret patterns, UTF-8 |
| `libretv/source/.env.example` | secret patterns, UTF-8 |
| `libretv/source/.github/workflows/docker-publish.yml` | secret patterns, UTF-8 |
| `libretv/source/.github/workflows/docker-sync-hub.yml` | secret patterns, UTF-8 |
| `libretv/source/.github/workflows/release-standalone.yml` | secret patterns, UTF-8 |
| `libretv/source/.gitignore` | secret patterns, UTF-8 |
| `libretv/source/Dockerfile` | secret patterns, UTF-8 |
| `libretv/source/LICENSE` | secret patterns, UTF-8 |
| `libretv/source/README.md` | secret patterns, UTF-8, local Markdown links |
| `libretv/source/docker-compose.yml` | secret patterns, UTF-8 |
| `libretv/source/eslint.config.mjs` | secret patterns, UTF-8 |
| `libretv/source/next.config.ts` | secret patterns, UTF-8 |
| `libretv/source/package-lock.json` | secret patterns, UTF-8, JSON |
| `libretv/source/package.json` | secret patterns, UTF-8, JSON |
| `libretv/source/postcss.config.mjs` | secret patterns, UTF-8 |
| `libretv/source/public/favicon.ico` | secret patterns, ICO signature |
| `libretv/source/public/icons/apple-touch-icon.png` | secret patterns, image signature |
| `libretv/source/public/icons/icon-144.png` | secret patterns, image signature |
| `libretv/source/public/icons/icon-192.png` | secret patterns, image signature |
| `libretv/source/public/icons/icon-48.png` | secret patterns, image signature |
| `libretv/source/public/icons/icon-512.png` | secret patterns, image signature |
| `libretv/source/public/icons/icon-96.png` | secret patterns, image signature |
| `libretv/source/public/player-poster.png` | secret patterns, image signature |
| `libretv/source/public/robots.txt` | secret patterns, UTF-8 |
| `libretv/source/src/app/about/page.tsx` | secret patterns, UTF-8 |
| `libretv/source/src/app/api/auth/route.ts` | secret patterns, UTF-8 |
| `libretv/source/src/app/api/bangumi/calendar/route.ts` | secret patterns, UTF-8 |
| `libretv/source/src/app/api/detail/route.ts` | secret patterns, UTF-8 |
| `libretv/source/src/app/api/douban/route.ts` | secret patterns, UTF-8 |
| `libretv/source/src/app/api/hot-list/route.ts` | secret patterns, UTF-8 |
| `libretv/source/src/app/api/live/epg/route.ts` | secret patterns, UTF-8 |
| `libretv/source/src/app/api/live/playlist/route.ts` | secret patterns, UTF-8 |
| `libretv/source/src/app/api/live/probe/route.test.ts` | secret patterns, UTF-8 |
| `libretv/source/src/app/api/live/probe/route.ts` | secret patterns, UTF-8 |
| `libretv/source/src/app/api/live/stream/[url]/route.ts` | secret patterns, UTF-8 |
| `libretv/source/src/app/api/live/stream/route.ts` | secret patterns, UTF-8 |
| `libretv/source/src/app/api/proxy/[url]/route.ts` | secret patterns, UTF-8 |
| `libretv/source/src/app/api/proxy/route.ts` | secret patterns, UTF-8 |
| `libretv/source/src/app/api/publish/route.test.ts` | secret patterns, UTF-8 |
| `libretv/source/src/app/api/publish/route.ts` | secret patterns, UTF-8 |
| `libretv/source/src/app/api/quality/route.test.ts` | secret patterns, UTF-8 |
| `libretv/source/src/app/api/quality/route.ts` | secret patterns, UTF-8 |
| `libretv/source/src/app/api/search/route.test.ts` | secret patterns, UTF-8 |
| `libretv/source/src/app/api/search/route.ts` | secret patterns, UTF-8 |
| `libretv/source/src/app/api/source-list/route.test.ts` | secret patterns, UTF-8 |
| `libretv/source/src/app/api/source-list/route.ts` | secret patterns, UTF-8 |
| `libretv/source/src/app/api/source/test/route.ts` | secret patterns, UTF-8 |
| `libretv/source/src/app/api/status/route.ts` | secret patterns, UTF-8 |
| `libretv/source/src/app/error.tsx` | secret patterns, UTF-8 |
| `libretv/source/src/app/global-error.tsx` | secret patterns, UTF-8 |
| `libretv/source/src/app/globals.css` | secret patterns, UTF-8 |
| `libretv/source/src/app/layout.tsx` | secret patterns, UTF-8 |
| `libretv/source/src/app/live/page.tsx` | secret patterns, UTF-8 |
| `libretv/source/src/app/manifest.ts` | secret patterns, UTF-8 |
| `libretv/source/src/app/page.tsx` | secret patterns, UTF-8 |
| `libretv/source/src/app/watch/page.tsx` | secret patterns, UTF-8 |
| `libretv/source/src/components/auth.tsx` | secret patterns, UTF-8 |
| `libretv/source/src/components/confirm-dialog.tsx` | secret patterns, UTF-8 |
| `libretv/source/src/components/detail-modal.tsx` | secret patterns, UTF-8 |
| `libretv/source/src/components/douban-section.tsx` | secret patterns, UTF-8 |
| `libretv/source/src/components/download-manager.tsx` | secret patterns, UTF-8 |
| `libretv/source/src/components/drawer.tsx` | secret patterns, UTF-8 |
| `libretv/source/src/components/dropdown.tsx` | secret patterns, UTF-8 |
| `libretv/source/src/components/header.tsx` | secret patterns, UTF-8 |
| `libretv/source/src/components/history-panel.tsx` | secret patterns, UTF-8 |
| `libretv/source/src/components/icon.tsx` | secret patterns, UTF-8 |
| `libretv/source/src/components/live-channel-list.tsx` | secret patterns, UTF-8 |
| `libretv/source/src/components/live-epg-panel.tsx` | secret patterns, UTF-8 |
| `libretv/source/src/components/live-player.tsx` | secret patterns, UTF-8 |
| `libretv/source/src/components/live-source-manager.tsx` | secret patterns, UTF-8 |
| `libretv/source/src/components/player-shell.tsx` | secret patterns, UTF-8 |
| `libretv/source/src/components/providers.tsx` | secret patterns, UTF-8 |
| `libretv/source/src/components/quality-badge.tsx` | secret patterns, UTF-8 |
| `libretv/source/src/components/search-history.tsx` | secret patterns, UTF-8 |
| `libretv/source/src/components/settings-shared.tsx` | secret patterns, UTF-8 |
| `libretv/source/src/components/site-footer.tsx` | secret patterns, UTF-8 |
| `libretv/source/src/components/skip-mark-panel.tsx` | secret patterns, UTF-8 |
| `libretv/source/src/components/smart-image.tsx` | secret patterns, UTF-8 |
| `libretv/source/src/components/source-manager.tsx` | secret patterns, UTF-8 |
| `libretv/source/src/components/states.tsx` | secret patterns, UTF-8 |
| `libretv/source/src/components/switch-source.tsx` | secret patterns, UTF-8 |
| `libretv/source/src/components/theme.tsx` | secret patterns, UTF-8 |
| `libretv/source/src/components/toast.tsx` | secret patterns, UTF-8 |
| `libretv/source/src/components/use-focus-trap.ts` | secret patterns, UTF-8 |
| `libretv/source/src/components/use-in-view.ts` | secret patterns, UTF-8 |
| `libretv/source/src/components/use-live-probe.ts` | secret patterns, UTF-8 |
| `libretv/source/src/components/use-quality-probe.ts` | secret patterns, UTF-8 |
| `libretv/source/src/components/use-source-probe.ts` | secret patterns, UTF-8 |
| `libretv/source/src/components/video-card.tsx` | secret patterns, UTF-8 |
| `libretv/source/src/lib/api-guard.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/auth.test.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/auth.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/bangumi.test.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/bangumi.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/client-api.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/clipboard.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/cms-parser.test.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/cms-parser.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/codec-parse.test.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/codec-parse.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/control-hide.test.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/control-hide.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/db.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/douban-weekly.test.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/douban-weekly.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/douban.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/download-saver.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/download-settings.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/env-image-mode.test.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/env-image-mode.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/env-live-sources.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/env-recommend-source.test.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/env-recommend-source.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/env-sources.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/env-subscriptions.test.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/env-subscriptions.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/fetch-utils.test.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/fetch-utils.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/hls-loader.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/host-gate.test.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/host-gate.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/live-cache.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/live-channel-filter.test.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/live-channel-filter.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/m3u-parser.test.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/m3u-parser.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/m3u8-downloader.test.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/m3u8-downloader.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/m3u8-parse.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/m3u8.test.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/m3u8.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/mp4-transmuxer.test.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/mp4-transmuxer.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/persist-storage.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/playback-recovery.test.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/playback-recovery.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/proxy-handlers.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/quality-probe-queue.test.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/quality-probe-queue.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/quality-probe.test.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/quality-probe.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/quality.test.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/quality.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/remarks.test.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/remarks.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/skip-marks.test.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/skip-marks.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/source-list-publish.test.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/source-list-publish.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/source-list.test.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/source-list.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/ssrf.test.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/ssrf.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/store.test.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/store.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/subscription-sync.test.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/subscription-sync.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/touch-pointer.test.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/touch-pointer.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/tvbox-parser.test.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/tvbox-parser.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/types.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/utils.test.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/utils.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/video-cache.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/video-prefetcher.test.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/video-prefetcher.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/xmltv.test.ts` | secret patterns, UTF-8 |
| `libretv/source/src/lib/xmltv.ts` | secret patterns, UTF-8 |
| `libretv/source/tailwind.config.ts` | secret patterns, UTF-8 |
| `libretv/source/tsconfig.json` | secret patterns, UTF-8, JSON |
| `libretv/source/vitest.config.ts` | secret patterns, UTF-8 |
| `pi-task-notify/.gitignore` | secret patterns, UTF-8 |
| `pi-task-notify/AGENTS.md` | secret patterns, UTF-8, local Markdown links |
| `pi-task-notify/INSTALL.md` | secret patterns, UTF-8, local Markdown links |
| `pi-task-notify/LICENSE` | secret patterns, UTF-8 |
| `pi-task-notify/README.md` | secret patterns, UTF-8, local Markdown links |
| `pi-task-notify/extensions/index.ts` | secret patterns, UTF-8 |
| `pi-task-notify/package.json` | secret patterns, UTF-8, JSON |
| `pi-task-notify/tsconfig.json` | secret patterns, UTF-8, JSON |
| `rea/.gitignore` | secret patterns, UTF-8 |
| `rea/AGENTS.md` | secret patterns, UTF-8, local Markdown links |
| `rea/INSTALL.md` | secret patterns, UTF-8, local Markdown links |
| `rea/README.md` | secret patterns, UTF-8, local Markdown links |
| `rea/THIRD_PARTY.md` | secret patterns, UTF-8, local Markdown links |
| `rea/assets.json` | secret patterns, UTF-8, JSON |
| `rea/prepare.cmd` | secret patterns, UTF-8 |
| `rea/profile/LICENSE` | secret patterns, UTF-8 |
| `rea/profile/README.md` | secret patterns, UTF-8, local Markdown links |
| `rea/restore.py` | secret patterns, UTF-8, Python syntax |
| `releases.json` | secret patterns, UTF-8, JSON |
| `scripts/agent_entry_policy.py` | secret patterns, UTF-8, Python syntax |
| `scripts/check_repository.py` | secret patterns, UTF-8, Python syntax |
| `scripts/export_profile.py` | secret patterns, UTF-8, Python syntax |
| `scripts/get_release.py` | secret patterns, UTF-8, Python syntax |
| `scripts/package_projects.py` | secret patterns, UTF-8, Python syntax |
| `scripts/tests/test_ofd_source_fixtures.py` | secret patterns, UTF-8, Python syntax |
| `scripts/tests/test_packages.py` | secret patterns, UTF-8, Python syntax |
| `scripts/tests/test_release_downloads.py` | secret patterns, UTF-8, Python syntax |
| `scripts/tests/test_restore.py` | secret patterns, UTF-8, Python syntax |
| `scripts/verify_published.py` | secret patterns, UTF-8, Python syntax |
| `scripts/verify_runtime.py` | secret patterns, UTF-8, Python syntax |
| `today-todo/.gitignore` | secret patterns, UTF-8 |
| `today-todo/AGENTS.md` | secret patterns, UTF-8, local Markdown links |
| `today-todo/DESIGN.md` | secret patterns, UTF-8, local Markdown links |
| `today-todo/INSTALL.md` | secret patterns, UTF-8, local Markdown links |
| `today-todo/LICENSE` | secret patterns, UTF-8 |
| `today-todo/PLAN.md` | secret patterns, UTF-8, local Markdown links |
| `today-todo/README.md` | secret patterns, UTF-8, local Markdown links |
| `today-todo/SPEC.md` | secret patterns, UTF-8, local Markdown links |
| `today-todo/assets/app.ico` | secret patterns, ICO signature |
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
| `windows-mcp/.gitignore` | secret patterns, UTF-8 |
| `windows-mcp/AGENTS.md` | secret patterns, UTF-8, local Markdown links |
| `windows-mcp/INSTALL.md` | secret patterns, UTF-8, local Markdown links |
| `windows-mcp/README.md` | secret patterns, UTF-8, local Markdown links |
| `windows-mcp/THIRD_PARTY.md` | secret patterns, UTF-8, local Markdown links |
| `windows-mcp/assets.json` | secret patterns, UTF-8, JSON |
| `windows-mcp/prepare.cmd` | secret patterns, UTF-8 |
| `windows-mcp/profile/LICENSE.md` | secret patterns, UTF-8, local Markdown links |
| `windows-mcp/profile/README.md` | secret patterns, UTF-8, local Markdown links |
| `windows-mcp/profile/install.cmd` | secret patterns, UTF-8 |
| `windows-mcp/profile/start.cmd` | secret patterns, UTF-8 |
| `windows-mcp/restore.py` | secret patterns, UTF-8, Python syntax |
| `yt-dlp/.gitignore` | secret patterns, UTF-8 |
| `yt-dlp/AGENTS.md` | secret patterns, UTF-8, local Markdown links |
| `yt-dlp/INSTALL.md` | secret patterns, UTF-8, local Markdown links |
| `yt-dlp/README.md` | secret patterns, UTF-8, local Markdown links |
| `yt-dlp/THIRD_PARTY.md` | secret patterns, UTF-8, local Markdown links |
| `yt-dlp/assets.json` | secret patterns, UTF-8, JSON |
| `yt-dlp/prepare.cmd` | secret patterns, UTF-8 |
| `yt-dlp/profile/README.md` | secret patterns, UTF-8, local Markdown links |
| `yt-dlp/profile/download.cmd` | secret patterns, UTF-8 |
| `yt-dlp/restore.py` | secret patterns, UTF-8, Python syntax |

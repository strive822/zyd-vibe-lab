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
| `codex-usage/.gitignore` | secret patterns, UTF-8 |
| `codex-usage/INSTALL.md` | secret patterns, UTF-8, local Markdown links |
| `codex-usage/README.md` | secret patterns, UTF-8, local Markdown links |
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
| `codex-usage/src/usage_app/startup_registry.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/startup_ui.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/storage.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/text_ui.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/widget.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/window_ui.py` | secret patterns, UTF-8, Python syntax |
| `codex-usage/src/usage_app/windows_monitors.py` | secret patterns, UTF-8, Python syntax |
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
| `docs/FILE_AUDIT.md` | secret patterns, UTF-8, local Markdown links |
| `docs/REPOSITORY_CLEANUP_REPORT.md` | secret patterns, UTF-8, local Markdown links |
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
| `scripts/check_repository.py` | secret patterns, UTF-8, Python syntax |

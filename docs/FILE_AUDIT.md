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
| `docs/REPOSITORY_SYNC_2026-11-01.md` | secret patterns, UTF-8, local Markdown links |
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
| `pi-task-notify/.gitignore` | secret patterns, UTF-8 |
| `pi-task-notify/INSTALL.md` | secret patterns, UTF-8, local Markdown links |
| `pi-task-notify/LICENSE` | secret patterns, UTF-8 |
| `pi-task-notify/README.md` | secret patterns, UTF-8, local Markdown links |
| `pi-task-notify/delivery/FILES.json` | secret patterns, UTF-8, JSON |
| `pi-task-notify/delivery/SHA256SUMS.txt` | secret patterns, UTF-8 |
| `pi-task-notify/delivery/pi-task-notify.zip` | secret patterns, ZIP CRC/paths, package/source SHA-256 |
| `pi-task-notify/extensions/index.ts` | secret patterns, UTF-8 |
| `pi-task-notify/package.json` | secret patterns, UTF-8, JSON |
| `pi-task-notify/tsconfig.json` | secret patterns, UTF-8, JSON |
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

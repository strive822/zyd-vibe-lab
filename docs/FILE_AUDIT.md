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
| `flyingmouse-format/bin/avs3/avs3RM0Decoder.exe` | secret patterns, binary blob |
| `flyingmouse-format/bin/avs3/model.bin` | secret patterns, binary blob |
| `flyingmouse-format/bmp-input.js` | secret patterns, UTF-8 |
| `flyingmouse-format/bmp-output.js` | secret patterns, UTF-8 |
| `flyingmouse-format/build/appx/Square150x150Logo.png` | secret patterns, image signature |
| `flyingmouse-format/build/appx/Square44x44Logo.png` | secret patterns, image signature |
| `flyingmouse-format/build/appx/StoreLogo.png` | secret patterns, image signature |
| `flyingmouse-format/build/appx/Wide310x150Logo.png` | secret patterns, image signature |
| `flyingmouse-format/build/icon.png` | secret patterns, image signature |
| `flyingmouse-format/ci-engines-v1.json` | secret patterns, UTF-8, JSON |
| `flyingmouse-format/cli.js` | secret patterns, UTF-8 |
| `flyingmouse-format/config.js` | secret patterns, UTF-8 |
| `flyingmouse-format/conversion-cancellation.js` | secret patterns, UTF-8 |
| `flyingmouse-format/conversion-progress.js` | secret patterns, UTF-8 |
| `flyingmouse-format/delivery/FILES.json` | secret patterns, UTF-8, JSON |
| `flyingmouse-format/delivery/SHA256SUMS.txt` | secret patterns, UTF-8 |
| `flyingmouse-format/delivery/flyingmouse-format.zip` | secret patterns, ZIP CRC/paths, package/source SHA-256 |
| `flyingmouse-format/design-export.js` | secret patterns, UTF-8 |
| `flyingmouse-format/desktop-recovery.js` | secret patterns, UTF-8 |
| `flyingmouse-format/desktop-shutdown.js` | secret patterns, UTF-8 |
| `flyingmouse-format/diagnostics.js` | secret patterns, UTF-8 |
| `flyingmouse-format/docs/ARCHITECTURE.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/HANDOFF.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/RELEASE.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/REPAIR-0.7.1.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/REPAIR-0.7.10.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/REPAIR-0.7.2.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/REPAIR-0.7.3.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/REPAIR-0.7.4.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/REPAIR-0.7.5.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/REPAIR-0.7.6.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/REPAIR-0.7.8.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/REPAIR-0.7.9.md` | secret patterns, UTF-8, local Markdown links |
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
| `flyingmouse-format/docs/release-notes-073.md` | secret patterns, UTF-8, local Markdown links |
| `flyingmouse-format/docs/release-notes-078.md` | secret patterns, UTF-8, local Markdown links |
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
| `flyingmouse-format/pdf-ocr-regions.js` | secret patterns, UTF-8 |
| `flyingmouse-format/pdf-office-docx.js` | secret patterns, UTF-8 |
| `flyingmouse-format/pdf-office-xlsx.js` | secret patterns, UTF-8 |
| `flyingmouse-format/pdf-structure-contract.js` | secret patterns, UTF-8 |
| `flyingmouse-format/pdf-structure-engine.js` | secret patterns, UTF-8 |
| `flyingmouse-format/pdf-structure-score.js` | secret patterns, UTF-8 |
| `flyingmouse-format/pdf-table-extractor.js` | secret patterns, UTF-8 |
| `flyingmouse-format/pdf-table-runtime.js` | secret patterns, UTF-8 |
| `flyingmouse-format/pdf-table.js` | secret patterns, UTF-8 |
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
| `flyingmouse-format/scripts/fix-pe-dangling-cert.py` | secret patterns, UTF-8, Python syntax |
| `flyingmouse-format/scripts/gen-appx-logos.js` | secret patterns, UTF-8 |
| `flyingmouse-format/scripts/inspect-pe.js` | secret patterns, UTF-8 |
| `flyingmouse-format/scripts/lock-docstructure-engine.js` | secret patterns, UTF-8 |
| `flyingmouse-format/scripts/prepare-windows-package.js` | secret patterns, UTF-8 |
| `flyingmouse-format/scripts/release-update.sh` | secret patterns, UTF-8 |
| `flyingmouse-format/scripts/release-version-sync.js` | secret patterns, UTF-8 |
| `flyingmouse-format/scripts/rename-opc-reserved.py` | secret patterns, UTF-8, Python syntax |
| `flyingmouse-format/scripts/restore-ci-engines.ps1` | secret patterns, UTF-8 |
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
| `flyingmouse-format/tests/helpers/office-processes.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/helpers/scanned-pdf-fixture.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/helpers/ui-page-harness.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/i18n.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/ico-format.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/image-conversion.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/image-merge-regressions.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/logger.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/macos-packaging.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/markdown-document.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/media-codec.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/mouse-assets.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/ocr-merge.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/ocr-page-diagnostics.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/ocr-quality.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/ofd-convert.test.js` | secret patterns, UTF-8 |
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
| `flyingmouse-format/tests/pdf-ocr-regions.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf-office-docx.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf-office-xlsx.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf-page-completeness.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf-scanned-routing.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf-structure-contract.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf-structure-engine.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf-structure-score.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf-table-extractor.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/pdf-table-runtime.test.js` | secret patterns, UTF-8 |
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
| `flyingmouse-format/tests/xml-json.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/tests/zip-util.test.js` | secret patterns, UTF-8 |
| `flyingmouse-format/text-conversion.js` | secret patterns, UTF-8 |
| `flyingmouse-format/text-docx.js` | secret patterns, UTF-8 |
| `flyingmouse-format/text-encoding.js` | secret patterns, UTF-8 |
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
| `graduation-thesis-workflow/packages/graduation-thesis-pi.zip` | secret patterns, ZIP CRC/paths, package/source SHA-256 |
| `graduation-thesis-workflow/packages/graduation-thesis-workbuddy.zip` | secret patterns, ZIP CRC/paths, package/source SHA-256 |
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
| `libretv/delivery/FILES.json` | secret patterns, UTF-8, JSON |
| `libretv/delivery/LibreTV.zip` | secret patterns, ZIP CRC/paths, package/source SHA-256 |
| `libretv/delivery/SHA256SUMS.txt` | secret patterns, UTF-8 |
| `libretv/packages/libretv-files.json` | secret patterns, UTF-8, JSON |
| `libretv/packages/libretv-source.zip` | secret patterns, ZIP CRC/paths, package/source SHA-256 |
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
| `pi-task-notify/.gitignore` | secret patterns, UTF-8 |
| `pi-task-notify/AGENTS.md` | secret patterns, UTF-8, local Markdown links |
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
| `today-todo/AGENTS.md` | secret patterns, UTF-8, local Markdown links |
| `today-todo/DESIGN.md` | secret patterns, UTF-8, local Markdown links |
| `today-todo/INSTALL.md` | secret patterns, UTF-8, local Markdown links |
| `today-todo/LICENSE` | secret patterns, UTF-8 |
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
| `windows-mcp/.gitignore` | secret patterns, UTF-8 |
| `windows-mcp/AGENTS.md` | secret patterns, UTF-8, local Markdown links |
| `windows-mcp/INSTALL.md` | secret patterns, UTF-8, local Markdown links |
| `windows-mcp/README.md` | secret patterns, UTF-8, local Markdown links |
| `windows-mcp/THIRD_PARTY.md` | secret patterns, UTF-8, local Markdown links |
| `windows-mcp/assets.json` | secret patterns, UTF-8, JSON |
| `windows-mcp/delivery/FILES.json` | secret patterns, UTF-8, JSON |
| `windows-mcp/delivery/SHA256SUMS.txt` | secret patterns, UTF-8 |
| `windows-mcp/delivery/Windows-MCP.zip` | secret patterns, ZIP CRC/paths, package/source SHA-256 |
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
| `yt-dlp/delivery/FILES.json` | secret patterns, UTF-8, JSON |
| `yt-dlp/delivery/SHA256SUMS.txt` | secret patterns, UTF-8 |
| `yt-dlp/delivery/yt-dlp.zip` | secret patterns, ZIP CRC/paths, package/source SHA-256 |
| `yt-dlp/profile/README.md` | secret patterns, UTF-8, local Markdown links |
| `yt-dlp/profile/download.cmd` | secret patterns, UTF-8 |
| `yt-dlp/restore.py` | secret patterns, UTF-8, Python syntax |

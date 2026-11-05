# Repository rules (authoritative)

This repository holds ten independent projects. Source, tests, licenses, templates and locked upstream references belong in Git. User-facing installers, runtime/launcher packages, skills and extensions belong in GitHub Releases. Never rewrite published history as part of routine cleanup.

## Repository map

- daozai: Rust/egui Windows app. `python -m unittest discover -s packaging_tests -v`; `cargo test --locked --all-targets --features record -- --test-threads=1`. Isolate test data; never real AppData/accounts. GLM uses zai.svg.
- dca-calculator: FastAPI + Next.js; no trading. Backend pytest; frontend typecheck, tests and static build with DCA_EXPORT=1.
- today-todo: zero-dependency Node service; `node --test test/api.test.js`, `node tools/contrast.js`. Never commit real data/todos.json.
- graduation-thesis-workflow: canonical skills/graduation-thesis; `python -m unittest discover -s tests -v`; four platform skill packages are built outside Git.
- pi-task-notify: Pi host extension; verify in Pi per INSTALL.md. Do not change unrelated Pi settings.
- libretv: expanded app source is source/, with source-files.json inventory. Run npm ci, typecheck, lint, test, build there. Existing profile and restore.py are developer recovery tools; users use the production Release.
- yt-dlp, windows-mcp, rea: own installers/profiles and pinned upstream references. Restore only into NEW directories; preserve upstream notices. Never equate preparation with host registration or actual device access. Root restore-boundary tests apply.
- flyingmouse-format: pinned upstream Windows app. Preserve its detailed AGENTS.md, branding, noncommercial license and original attribution. Users use the unchanged official installer; runtime/bootstrap only downloads and verifies it.
- docs/ and scripts/ support the repository; they are not projects.

## Required for every project

1. ASCII lowercase kebab-case directory; README.md, INSTALL.md, AGENTS.md, license and reproducible source/build instructions.
2. README heading `## 直接让 Agent 帮你使用` with a text prompt naming this repository, exact project directory and INSTALL.md.
3. INSTALL.md has `## 给人：` and `## 给 Agent：` sections: browser Release link, checksum, install/start/verify, plus copyable Agent prompt and execution constraints. Root INSTALL.md follows the same rule.
4. Register purpose and installation links in root README/INSTALL and a pinned Release in releases.json. Each published artifact has exact name, bytes, SHA-256 and a downloadable SHA256SUMS.txt.
5. Preserve original licenses/notices and pinned upstream commits. Original work uses MIT, Copyright (c) 2026 zhongyudi. The upstream download locks do not claim to include all third-party source locally.
6. Source-only Git: no delivery/, generated packages/, target/, node_modules/, virtualenvs or installers/archives. Binary source assets such as images, fonts and model data remain where required; prebuilt executables are downloaded from fixed sources for development.

## Build, verification and publishing

- Follow each project's AGENTS.md; no unrelated application refactors. Preserve existing uncommitted user work.
- `python scripts/agent_entry_policy.py`, `python -m unittest discover -s scripts/tests -v`, `python scripts/check_repository.py` are root checks. Published downloads: `python scripts/verify_published.py --ref <immutable commit>`.
- `python scripts/package_projects.py --output <outside-checkout-path>` builds typed runtime/installer packages, not another copy of the development tree. Web builds and a verified Daozai installer are explicit inputs. Details: docs/AGENT_DELIVERY_STANDARD.md.
- Update releases.json after final artifacts exist; do not change packaged inputs afterwards. Review the diff and validate artifacts before publishing. Bundled README/INSTALL byte-match source at that ref.
- Publish at a new `<project>-v<version>-rN` tag; upload only the typed program/installer/skill/extension files and SHA256SUMS.txt. Keep Git commits and tags. Keep only the current verified Release for each project listed in releases.json; never use the repository-wide Latest badge to prune other projects. Back up old release metadata and assets before removing superseded releases. Verify remote downloads before advancing main; see docs for the publishing sequence.
- CI covers source policy, package/restore boundaries and changed projects. A passing test is not native host, real account or physical device acceptance.

## Local data and cleanup

- .local-archives/ is a private, ignored preservation area for pre-migration user work. Never package, upload or use it as the canonical current source.
- Do not operate daily running instances or credentials during automated tests. Preserve installed apps, configurations, user data and needed rollback programs.
- Keep intermediate builds under the task's Codex temp directory. Remove recreatable caches and duplicate outputs after acceptance; keep final installers, checksums and necessary verification evidence outside Git. Verify absolute deletion/move bounds on Windows; never follow reparse points.

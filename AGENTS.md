# Repository map

This is a collection of three independent projects, not one application.

- For user installation requests, read INSTALL.md and then the named project's INSTALL.md. Download the full project or its documented portable bundle.
- dca-calculator: FastAPI backend and Next.js frontend. Follow README.md; backend tests use requirements-dev.txt, frontend dependencies use npm ci.
- graduation-thesis-workflow: read its AGENTS.md before maintenance. Keep skills/graduation-thesis canonical and rebuild platform ZIPs after bundle changes.
- codex-usage: Windows desktop application. Preserve docs/evidence/m1-r4/frozen-source as the visual regression fixture. Keep private evidence, user data and credentials outside Git.

For repository maintenance run python scripts/check_repository.py plus the changed project's checks. Preserve generated download ZIPs with their manifests and licenses; these are intentional delivery artifacts. Avoid modifying daily running instances or real accounts during automated checks.

Keep installation instructions, README links and download hashes consistent. Do not claim native client discovery, real account success or device acceptance based on a unit test. Publish only after checking staged changes and tests.

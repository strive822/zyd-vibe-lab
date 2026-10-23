# Repository map

This is a collection of independent projects and independent personal tools, not one application.

- For user installation requests, read INSTALL.md and then the named project's INSTALL.md. Download the full project or its documented portable bundle.
- dca-calculator: FastAPI backend and Next.js frontend. Follow README.md; backend tests use requirements-dev.txt, frontend dependencies use npm ci.
- graduation-thesis-workflow: read its AGENTS.md before maintenance. Keep skills/graduation-thesis canonical and rebuild platform ZIPs after bundle changes.
- codex-usage: Windows desktop application. Preserve docs/evidence/m1-r4/frozen-source as the visual regression fixture. Keep private evidence, user data and credentials outside Git.
- LibreTV, yt-dlp, Windows-MCP, rea, Winhance: each has independent INSTALL.md, AGENTS.md, assets.json, profile/ and restore.py. No shared toolbox is required. Preserve usage profiles, licenses and locked assets. Restore only into new directories. Run python -m unittest discover -s scripts/tests -v after restore changes.

For repository maintenance run python scripts/check_repository.py plus the changed project's checks. Preserve generated download ZIPs with their manifests and licenses; these are intentional delivery artifacts. Avoid modifying daily running instances or real accounts during automated checks.

Keep installation instructions, README links and download hashes consistent. Do not claim native client discovery, real account success or device acceptance based on a unit test. Publish only after checking staged changes and tests.

## Required for every future project upload

Every new project must be in its own subdirectory, with no shared toolbox wrapper.
Its README.md must contain exactly the heading `## 直接让 Agent 帮你使用`, a fenced
`text` prompt that names the repository URL, project directory and INSTALL.md,
and a working link to its own INSTALL.md. The root README must include the same
copyable prompt and an installation link. INSTALL.md must cover complete download,
integrity checks, isolated environments, actual use/verification and permission
boundaries. Preserve the distinction between downloading, installing and running.
Follow docs/AGENT_DELIVERY_STANDARD.md. Run python scripts/agent_entry_policy.py
and python scripts/package_projects.py before uploading; verify bundles and hashes.
Do not describe local-only files or guessed URLs as published downloads.

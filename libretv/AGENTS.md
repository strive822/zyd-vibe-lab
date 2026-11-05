# LibreTV

This project is independent. Read INSTALL.md before downloading or restoring.
Use this directory's assets.json and restore.py; no sibling project is required.
Preserve locked versions, upstream notices and profiles. Restore only into a NEW
directory. Do not change existing running instances or global Agent settings.
Downloads are not installations. Do not launch installers, register MCP, run REA
setup or change system settings unless the user requested those actions.
For source changes run the root repository check and scripts/tests checks.
Expanded app source lives in source/; source-files.json locks the recovery copy.
Run npm ci, typecheck, lint, test and build there. Production Releases use the
existing DOCKER_BUILD=1 standalone target; no npm build is needed by users.
Runtime launchers live in runtime/ and generate private .env.local only on first
start. Keep default sources and the private password out of public data.

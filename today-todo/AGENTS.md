# today-todo

Zero-dependency Node HTTP service plus a static frontend: a today-only
checklist shared by one computer and one phone on the same LAN. No cloud, no
accounts, no `npm install`.

Checks (from this directory): `node --test test/api.test.js` and
`node tools/contrast.js`; both run in CI.

Boundaries: runtime data lives in the git-ignored `data/todos.json` — never
commit it and never overwrite an existing data file during install; start the
service with Node and verify http://localhost:3000. Build runtime artifacts with
the root scripts/package_projects.py into an outside-checkout directory; upload
programs and checksums to Release, never delivery ZIPs to Git (root AGENTS.md).

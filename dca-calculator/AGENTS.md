# dca-calculator

Two-model DCA weight calculator for Nasdaq 100 / CSI 500 / gold based on
SMA800: FastAPI backend plus Next.js frontend. It computes weights and amounts
only — no trading, no accounts, no backtesting, no scheduled jobs. Never
present it as a trading system.

Backend checks (inside `backend/`): `pip install -r requirements-dev.txt && python -m pytest`.
Frontend checks (inside `frontend/`): `npm ci`, `npm run typecheck`, `npm test`, `npm run build`.
CI runs both; run them before delivery.

Boundaries: never commit real user data, credentials or `.env` files; keep the
frontend static export flow intact; after any file change rebuild `delivery/`
with the root `scripts/package_projects.py` (see root AGENTS.md).

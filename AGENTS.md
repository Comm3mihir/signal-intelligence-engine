# SIGNAL development instructions

Preserve the FastAPI APIs, Next.js interface, and existing news, risk, and enterprise workflows.
Run `python -m pytest -q` and run `npm ci` followed by `npm run build` in `frontend` before shipping
cross-stack changes. Use an isolated database for tests. Generated Next.js files and local database
files are runtime artifacts.

IntelMap input is untrusted. Keep provider endpoints and model routing server-side. Validate every
generated source identifier against the supplied archive records. Keep original forecasts, probability
revisions, and resolutions append-only. Score only objectively resolved forecasts. Do not infer
non-occurrence from missing coverage or manufacture historical rates.

Keep production workers bounded, idempotent, and resumable. Use only explicitly eligible free
provider accounts and routes. Document configuration, compatibility changes, and validation results
in the IntelMap documentation.

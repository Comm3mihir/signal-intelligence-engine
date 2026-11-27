# Deploy SIGNAL on Vercel and Render

## Frontend

Keep the existing Vercel project rooted at `frontend/`. Set `NEXT_PUBLIC_API_URL` to
`https://signal-intelligence-engine.onrender.com` for Production and Preview as appropriate.
The hosted fallback is the same public API origin. For an isolated preview, aim this variable
at a separate Render staging backend running the same revision and redeploy the preview.
The production frontend never needs an AI key or database credentials.

## Render API

Keep the existing Docker Web Service. The build context is the repository root and the Dockerfile
is `backend/Dockerfile`. The container listens on Render's `PORT`, or 8000 for local Docker.
The public health path is `/`. Start with the values in `.env.example`.

| Render setting | Purpose |
| --- | --- |
| `DATABASE_URL` | Hosted PostgreSQL connection with TLS. Required for protected IntelMap and Assistant endpoints. |
| `SIGNAL_ENV=production` | Explicit production mode. Render is also detected automatically. |
| `SIGNAL_RUN_MIGRATIONS=1` | Bootstrap additive tables and vector extension on startup. The database role must have the required privileges. Remove after the first successful migration if migrating separately. |
| `SIGNAL_ANALYST_TOKEN` | Strong random shared analyst credential. Enter it in the app's Analyst access control. |
| `SIGNAL_SCHEDULER_SECRET` | Different strong random token for the scheduler. |
| `SIGNAL_CORS_ORIGINS` | Comma-separated production and approved preview origins. |
| `LLM_PROVIDER=groq`, `LLM_API_KEY`, `LLM_FREE_TIER_CONFIRMED=1` | Hosted inference account and opt-in. Confirm the actual upstream account eligibility before setting the flag. |
| `ASSISTANT_MODEL=openai/gpt-oss-20b`, `FORECAST_MODEL=openai/gpt-oss-120b` | Optional task-specific overrides for Groq. |
| `GROQ_DAILY_TOKEN_BUDGET`, `SIGNAL_ASSISTANT_PER_HOUR`, `SIGNAL_FORECAST_PER_HOUR`, `SIGNAL_EVIDENCE_PER_HOUR` | Optional workspace limits. |

Start the backend before rolling out the new frontend, then test Overview and OSINT from Vercel.
If the service currently has no cloud database, public legacy reads and writes can still use
their existing SQLite configuration. Protected AI operations return an explicit configuration
error until PostgreSQL is available. Do not depend on Render's ephemeral SQLite disk for
production records. Export or migrate any existing SQLite data before replacing its connection.

## Database and scheduler

1. Reuse a hosted PostgreSQL database if it is available. Otherwise provision Supabase or Neon
   with the vector extension and a TLS connection. A Supabase session pooler is suitable when
   the runner cannot use IPv6. Use a dedicated backend role that owns the SIGNAL tables.
2. For the first deploy use the Render migration option above, or run
   `python -m backend.intelmap.migrate` from a trusted CI runner against the direct/session URL.
   This adds tables, PostgreSQL history guards and row-level security. Verify the actual deployment
   before enabling traffic. No migration removes enterprise records.
3. Enable Supabase Cron and pg_net. In Supabase Vault, create `signal_backend_url` and
   `signal_scheduler_secret`, then run `data/migrations/supabase_schedule.sql`. It makes signed
   HTTP requests every minute to process an eligible stage and refreshes news every 15 minutes.
   For Neon, configure an external scheduler to POST to the same workflow URL with
   `Authorization: Bearer <scheduler-secret>`. Use the configured cloud scheduler, never a local loop.
4. Verify successful scheduler calls and watch a generation job progress while the website is
   closed. The queue persists stages, leases, retry times, and deduplication IDs. Cold starts and
   missed invocations delay processing. Analysts record binary outcomes from matched evidence.

Render Free can spin down during inactivity and has limits. Frequent scheduler calls consume
included compute and other allowances, and a paid always-on service may be appropriate for
production uptime. This implementation does not enable a paid plan. Check current usage and
terms in the service dashboard. [Render free-instance limits](https://render.com/docs/free) ·
[Render Docker deployments](https://render.com/docs/docker) ·
[Supabase Cron](https://supabase.com/docs/guides/cron)

## Security and verification

Provider keys and the scheduler secret stay on Render or in the scheduled job's secret vault.
The shared analyst token is scoped to authorized workspace users and stored in their tab's
session storage. It is separate from provider credentials. Shared workspace conversations are
visible to holders of that token. Using separate per-user or team identities requires an
additional identity layer.

Confirm the current website carries the right public backend origin, the protected endpoints return
401 without credentials after configuration, and a genuine provider round-trip returns a cited
answer. Set preview origins in Render CORS before testing browser requests.

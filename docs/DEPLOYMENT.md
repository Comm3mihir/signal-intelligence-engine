# Deploy SIGNAL

## Accounts and secrets

Use a Supabase project with PostgreSQL, pgvector and Supabase Cron, two Vercel projects attached
to the SIGNAL repository, and at least one eligible free-tier inference account.
Use the configuration keys in `.env.example`. Store keys in Vercel's server-side environment
only. Keep the scheduler token and workspace password different. Use a database role intended for
the application and protect its connection string.

## Database and backend

1. Enable pgvector in the hosted database. Choose the Supabase session pooler if the runner does
   not have IPv6 connectivity. Use a TLS connection string.
2. From a trusted runner with the database connection configured, install
   `backend/requirements.txt` and run `python -m backend.intelmap.migrate`. Run migrations on
   the direct or session connection. Migrations are additive and can be rerun.
3. Import the repository in Vercel. Set the project root to the repository root and select FastAPI.
   The entry point is `app.py`. Set `DATABASE_URL`, `SIGNAL_ENV=production`,
   `SIGNAL_WORKSPACE_USER`, `SIGNAL_WORKSPACE_PASSWORD`, `SIGNAL_SCHEDULER_SECRET` and provider
   secrets. Configure Vercel's own deployment protection so the scheduler and application can
   reach the backend. SIGNAL authenticates the API separately.
4. Confirm the backend root responds. An unauthenticated request to `/api/intelmap/catalog`
   should receive HTTP 401. Use the workspace credentials for the authorized check.

## Frontend

Create a second Vercel Next.js project rooted at `frontend`. Set `SIGNAL_ENV=production`,
`SIGNAL_WORKSPACE_USER`, `SIGNAL_WORKSPACE_PASSWORD`, and `SIGNAL_BACKEND_URL` to the HTTPS
backend origin before building. Use the same workspace credentials on both projects. Visit the
frontend over HTTPS, sign in, and check that the same-origin catalog request succeeds. The workspace
uses one shared analyst account. Keep it private to the intended analysts.

## Scheduled monitoring

Enable Supabase Cron and pg_net. In Supabase Vault, create `signal_backend_url` (the backend HTTPS
origin) and `signal_scheduler_secret` (same value as on the backend). Run
`data/migrations/supabase_schedule.sql` as a trusted operator. The schedule invokes one bounded
worker stage per minute and refreshes news approximately every 15 minutes. To reduce usage,
change the cron expression. Check the job history and HTTP response in Supabase, then confirm
that articles are fresh and the generation queue advances. No visit to the frontend is required.

The forecast tracker evaluates deadlines against UTC. The outcome view computes performance from
persisted records, so it does not need a separate weekly job. Vercel Hobby's native cron minimum is
daily, which is why the setup uses Supabase Cron. No paid plan is required by this design, but
availability, included usage, and project policies must be confirmed in each actual account.

## Local development

Use the existing README instructions. Export provider variables before starting the backend when
testing real inference. SQLite and the background worker are supported locally only. In production,
there is no loop inside a Vercel function or reliance on a personal computer. Verify production
operation by observing scheduled runs and completed jobs while the site is closed.

[Vercel FastAPI support](https://vercel.com/docs/frameworks/backend/fastapi) ·
[Vercel cron limits](https://vercel.com/docs/schedules/cron-jobs/usage-and-pricing) ·
[Supabase Cron](https://supabase.com/docs/guides/cron)

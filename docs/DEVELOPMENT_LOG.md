# IntelMap development log

## Repository assessment

The starting branch included the existing enterprise graph, public news/markets, an SQLite-backed
snapshot, rule-based scenario archive, and single-process refresh worker. There was no configured
PostgreSQL deployment, vector schema, durable scheduler or inference provider in the repository.

## Implementation

- Added the IntelMap route and linked it to existing news cards. Kept the legacy enterprise graph.
- Added cloud inference contracts, bounded fallback, durable budgets/cache and provider telemetry.
- Added normalized forecast persistence, optional pgvector embeddings, indexed evidence matching,
  append-only revisions and source-backed manual outcomes.
- Added original/lead-time evaluation and a Vercel/Supabase deployment configuration.

## Verification

Eight backend tests pass, including a rate-limited provider fallback, article-to-forecast
matching, an append-only probability revision, evidence-required analyst resolution, and
insufficient-data metric handling. The production Next.js build compiled with the upgraded
dependencies. Chromium exercised article handoff, queued graph generation, graph navigation,
evidence expansion, tracking, and evaluation with controlled inference responses. The dependency
audit returned zero vulnerabilities at the time of verification.

## Open validation and follow-up

A live Vercel deployment, scheduled Supabase invocation, production cloud PostgreSQL migration and
real eligible provider calls require account credentials. Hosted billing, quota and global region
availability must be checked in those accounts. Use a controlled analyst cohort before interpreting
any performance statistics. Baseline curves, trained calibration, full account-level RBAC, and
stronger story-level syndication detection are follow-up items.

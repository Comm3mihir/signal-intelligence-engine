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


## Render workstation restructuring

The workstation incorporates the draft IntelMap and risk-workspace changes and integrates
the merged API URL resolver. Overview and OSINT still use the public legacy endpoints. The
tab sequence is Overview, OSINT Ingestion, IntelMap, Assistant. Enterprise Graph, AI
Transformation, and Risk & Traceability remain accessible by their existing routes.

IntelMap supports public HTTPS article retrieval, saved OSINT and manual inputs, versioned
regeneration, and collapsible scenario branches. The Assistant now calls the hosted provider
with database-backed history, bounded retrieval, and validated source IDs. It uses complete
structured responses to validate citations before display. This release does not stream partial
LLM responses.

The production build and 11 backend tests passed. Chromium verified the article-to-map flow,
branch controls, regeneration history, OSINT ingestion, and cited multi-turn chat. Test inference
uses controlled responses. The deployed Vercel shell and current Render feed responded.
A Docker smoke image used the workspace trust bundle for package installation and successfully
served health on Render's port 10000. The live publisher parser was tested against downloaded
HTML. Direct DNS-pinned publisher requests were restricted by this workspace network and still
need a Render staging check.

Actual hosted credentials, scheduler and Vercel Preview are not established by this change.
The shared workspace token grants access to the conversation list. Full per-user history
isolation would require a separate identity system.

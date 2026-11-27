# SIGNAL Technical Architecture

## Overview
SIGNAL (Strategic Intelligence & Geopolitical Risk Analysis Engine) is an enterprise strategic intelligence platform that connects external OSINT events, geopolitical developments, export control policy updates, and supply chain disruptions directly to internal enterprise business dependencies, products, core operational processes, transparent risk scoring, and AI transformation priorities.

```text
┌────────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (Next.js 14)                         │
│  Executive Dashboard │ Enterprise Graph │ OSINT Ingest & Surprise Test │
│  Risk & Traceability Matrix │ AI Transformation Roadmap │ AI Chat      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / REST APIs
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          BACKEND (FastAPI 0.110+)                      │
│  /api/organisations │ /api/signals │ /api/risks │ /api/transformation  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        INTELLIGENCE & RISK LAYER                       │
│  - Bi-directional Graph Engine (traversal: Event -> Supplier -> Risk) │
│  - Transparent Risk Scoring Engine (Likelihood*Impact*Exposure*...)   │
│  - Dynamic NLP Entity & Relation Extractor ("Surprise Record Test")    │
│  - Evidence Traceability Engine (Finding -> Snippet -> Source -> Date) │
│  - Strategic AI Transformation & Mitigation Initiative Generator        │
│  - RAG Semantic Evidence Vector Retrieval & Natural Language Q&A       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                           DATA & STORAGE LAYER                         │
│  SQLite / PostgreSQL + pgvector │ Seed Data Engine                     │
└────────────────────────────────────────────────────────────────────────┘
```

## Data Model Lineage
Relationships are modelled bi-directionally:
`Organisation -> Country -> Supplier -> Dependency -> Product/Tech -> Process -> External Signal -> Evidence -> Risk Assessment -> Transformation Opportunity -> Initiative`

## Dynamic Processing ("Surprise Record Test")
When a new external signal or hypothetical scenario is ingested:
1. **NLP Entity Extraction**: Identifies mentioned countries, technologies, supplier names, policy types, and severity keywords.
2. **Graph Dependency Traversal**: Traces affected suppliers, micro-components, and operational processes across the enterprise graph.
3. **Deterministic Risk Scoring**: Evaluates likelihood, impact, exposure, dependency weight, and evidence confidence.
4. **Traceable Evidence Storage**: Stores full line-by-line evidence citations.
5. **AI Transformation Options**: Generates mitigation strategies (e.g. supplier diversification, inventory buffers, local technology substitution).

## IntelMap and cloud runtime

The frontend runs as a Next.js Vercel project rooted at `frontend/`. Its browser uses
`NEXT_PUBLIC_API_URL` to reach the Render Docker FastAPI service over HTTPS. Public Overview and
OSINT endpoints preserve the existing request shape. A shared analyst bearer token protects AI
and conversation routes. A separate secret guards the schedule. The saved enterprise graph and
risk routes remain available for compatibility.
The scheduler calls a bounded HTTP function. Each invocation can refresh the source snapshot when
it is due, archive articles, and claim one eligible job. Jobs use a persisted lease, retry schedule,
checkpointed stages, and stable idempotency keys. PostgreSQL advisory locks serialize job claims and
news refreshes across instances. There are no production lifespan workers.

News snapshots remain in the existing intelligence store. IntelMap uses separate tables for immutable
maps, forecast nodes, evidence, revisions, outcomes, embeddings, budgets, inference attempts, conversation history, and jobs. Forecast parent references encode causal edges. Scenario group identifiers are kept with the
original statements. Evaluation derives scores from immutable originals, dated revisions, and verified
outcomes on request. `python -m backend.intelmap.migrate` installs the tables and PostgreSQL history
protection triggers. These additions do not migrate legacy SQLite data to a new cloud database.

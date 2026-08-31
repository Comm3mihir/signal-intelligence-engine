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

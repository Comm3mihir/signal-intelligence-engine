# IntelMap specification

IntelMap is the predictive workspace in SIGNAL. The enterprise graph remains at `/dependency-map`.
The overview opens IntelMap with an article already selected. Generate also supports a cluster or up
to eight archive articles. It deduplicates generation by canonical sorted article IDs and pipeline version.

- **Generate** chooses evidence, submits a job, and shows stage and capacity status.
- **Explore** lays out forecasts and causal links in React Flow with Dagre. It provides zoom, pan,
  fullscreen, status filters, collapsible branches, and selectable evidence nodes. Regeneration stores a linked version without replacing an earlier map. The assessment displays actors, source
  excerpts, assumptions, adverse evidence, precedents, resolution criteria, and dated revisions.
- **Track** lists recent forecasts, deadlines, material evidence, statuses, and revisions. A forecast
  opens directly in its map for analyst review. Analysts can archive primary-source metadata and excerpts, then cite the archived record in a resolution.
- **Evaluate** compares originals and fixed-lead revisions. It shows denominator and sample
  sufficiency for each Brier score and calibration curve.
- **Infrastructure** shows configured providers, actual request results, reported token usage,
  local budget, cache hits, failed jobs, and queue depth. Provider quotas and expenditure remain
  unavailable unless reliably measured.

## Analysis contract

Event extraction supplies reported developments, actors, regions, dates, classification, and
unverified claims. Historical retrieval uses a bounded older archive and compatible embeddings
when present. The forecasting stage produces three to five first-order predictions and optional
secondary and tertiary consequences with a hard three-level limit. An adversarial stage checks causal support,
alternatives, missing evidence, and objective resolution criteria before publication. Provisional
probabilities include an explicit marginal or conditional interpretation and supporting article IDs.

The matching stage evaluates only bounded candidates from active forecast terms, dates and available
vectors. An LLM may classify and propose a material revision. An analyst records terminal truth
values against the original criteria. For individual forecast definitions and evaluation, see
[Forecasting methodology](FORECASTING_METHODOLOGY.md).

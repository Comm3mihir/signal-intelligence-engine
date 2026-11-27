# Forecasting methodology

Each original statement contains a deadline and predicates for confirmation and refutation.
Initial probabilities are explicitly uncalibrated estimates. First-order probabilities estimate
the chance of the event within its window. A downstream estimate is conditional on its parent.
The product of the root marginal and every conditional estimate along the branch gives the displayed joint pathway.
Exclusive siblings cannot initially exceed a total of one. Other forecasts may overlap.

The matching weights default to 30% semantic, 25% actor/entity, 25% action, 10% temporal and 10%
geographic relevance. They are heuristics. An indexed term and forecast-window query bounds the
candidate set before scoring. PostgreSQL can also retrieve nearby forecast vectors. Available weights are renormalized for missing vectors and optional
cloud embeddings enrich the score. Exact normalized headline fingerprints limit obvious duplicates
across publishers. Syndication with different headlines can still evade this heuristic.

The verifier labels evidence by stance and can propose a revision only for material supporting,
contradictory, or partial evidence. Revisions are appended with their source, provider, model,
time and rationale. The worker does not independently revise exclusive groups because a justified
change may require reviewing the whole group. Bayesian updating is available as a deterministic
odds calculation for externally justified inputs. An analyst can record a Bayesian update after selecting a linked source and documenting the likelihood ratio. The system does not derive likelihood ratios or
base-rate benchmarks from unrestricted model output.

Only an analyst can record a confirmed or refuted outcome. Compare evidence against the original
scope, actors, geography, and deadline. Prefer a dated primary source. Supply the archived article,
the resolution rationale, and an explanation of source credibility. If the event was not observed,
this does not establish non-occurrence. Elapsed deadlines are inconclusive unless documented evidence
satisfies the criteria. Confirmed and refuted store truth values of one and zero respectively;
inconclusive results remain null.

The Brier score is the mean squared error between the estimated probability and binary outcome.
The UI suppresses Brier scores below ten eligible observations and calibration bins below three.
It evaluates child estimates only when the parent was confirmed. Original scores and revisions are
separate. The revised slice uses the last revision recorded at least 24 hours before the earliest of
the deadline, the resolution report, or analyst review. This timing is an approximation when the
actual observed event time precedes the report. Benchmarks remain unavailable until comparable,
documented historical cohorts exist. Fit any future calibration model on an earlier cohort and
evaluate on a disjoint later cohort.

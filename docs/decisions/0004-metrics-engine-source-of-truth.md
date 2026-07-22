# 0004 — Metrics computed by a deterministic engine; the LLM never does math

**Status:** Accepted · 2026-07-22

## Context
Sharpe, Sortino, Calmar, drawdown, alpha/beta and friends are the memo's
credibility. LLMs are unreliable at arithmetic and at the subtle, easy-to-get-
wrong conventions here: annualization from the series' frequency, the risk-free
rate source, downside-deviation targets, handling of short or gappy series. A
wrong Sharpe silently poisons the whole recommendation.

## Decision
All metrics are computed by a **deterministic, pure-Python engine** with explicit
conventions and **golden-value unit tests**. The LLM only *reports* pre-computed,
validated numbers via typed tools; it never calculates a metric and never sees a
path to do so. Each `MetricResult` records its inputs reference and a `formula_id`
so it is fully traceable.

## Consequences
- Numbers are correct, reproducible, and testable — the foundation the audit
  trail and the memo rest on.
- Metric conventions (annualization factor, risk-free source, MAR) are explicit
  config, documented and tested, not implicit.
- Requires disciplined tool design so the agent literally cannot compute — the
  allow-list only exposes "fetch a computed metric," never "evaluate this."

## Alternatives considered
- **Let the LLM compute or "sanity-check" metrics:** rejected — introduces
  non-determinism and error into the one place that must be exact.
- **Third-party metrics lib as the sole source:** fine to use internally, but we
  still wrap and unit-test conventions so behavior is pinned and auditable.

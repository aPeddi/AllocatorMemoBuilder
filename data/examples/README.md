# EQUI — Test CSV Pack

A set of sample inputs for exercising the AllocatorMemoBuilder app end-to-end: the
two input formats (monthly returns **or** summary statistics), fee / liquidity
("service rate") handling, peer- and benchmark-correlation, and the data-quality
validation path. All files are synthetic and deterministic (fixed random seed).

## How to load

In the running app, use the **upload** control (the CSV/source button) and pick one
file. The app auto-detects the shape; if it asks you to confirm a column mapping,
review it and run. Each upload re-screens and re-scores the universe live, fetches
the benchmark, and rebuilds the audit — so everything (scatter, shortlist, memo,
downloadable PDF) reflects the file you loaded.

Load them one at a time — each file is its own fund universe.

## The files

**01_monthly_returns_full.csv** — the everything file.
Eight funds across eight strategies, 24 monthly returns each, with full metadata:
name, strategy, management fee, redemption frequency, lockup, notice, and notes.
Exercises the widest range: full metric engine (return, vol, Sharpe, Sortino,
Calmar, max drawdown), **peer correlation** across the universe, **benchmark
correlation / beta / alpha**, net-of-fee return, notes surfacing, and the mandate
screen (one fund is illiquid enough to be cut). Good file for trying the mandate
editor — strategy preferences/exclusions, vol and drawdown limits — and for the
1–2 page PDF with per-fund shortlist rationale.

**02_summary_statistics.csv** — the summary-statistics input mode.
Six funds given as *precomputed* metrics with no return series: ann. return,
vol, Sharpe, Sortino, Calmar, max drawdown, plus fee, liquidity and notes. Values
are intentionally mixed between percent strings ("14.2%") and decimals (0.088) to
show the percent-or-decimal tolerance, and one fund's `max_drawdown` is given as a
positive number to confirm it is normalised to negative. Funds are ranked directly
from the provided statistics; the audit traces each figure back to its source cell.

**03_wide_returns.csv** — the wide layout.
One date column plus one column per fund (five funds, 18 months). Confirms the app
detects a wide return matrix and computes the same metrics and correlations as the
long layout.

**04_edge_cases.csv** — data-quality validation.
A deliberately messy long file: a clean fund, a short-history fund (inconsistent
date range), a fund whose good series is peppered with bad rows (missing date,
unparseable date, missing return, an "N/A" cell), a row with a missing fund id, and
an id with stray casing/whitespace. Use it to see the quarantine reveal — five rows
are set aside with specific reasons while 21 valid rows load and the surviving funds
are still scored.

**05_correlation_showcase.csv** — peer correlation, made legible.
Four funds loaded on a common equity factor (a crowded book) plus one true
diversifier that moves against them. Peer correlation is the average pairwise
correlation to the rest of the universe, so the four cluster funds land around
+0.46 while the diversifier lands near **−0.95** — a clear read on which position
actually hedges the others.

## Notes

- Dates are `YYYY-MM-01`; returns are monthly decimals (0.01 = +1%).
- Recognised column synonyms include: id (`fund_id`/`fund`/`ticker`/`symbol`/`id`),
  return (`monthly_return`/`return`/`ret`/`performance`), date (`date`/`period`/
  `month`/`as_of`), plus `strategy`/`style`, `mgmt_fee_pct`/`fee`,
  `redemption_freq`/`liquidity`, `lockup_months`, `notice_days`, `notes`, and for
  the stats layout `ann_return`, `ann_vol`, `sharpe`, `sortino`, `calmar`,
  `max_drawdown`.
- Benchmark correlation is computed against the live index the app fetches at load
  time, so those figures depend on the benchmark in effect when you upload.

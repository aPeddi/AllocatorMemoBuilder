# AllocatorMemoBuilder — Product & Architecture Spec

> Canonical, tracked spec. It supersedes `Inspo.md` (the untracked brainstorm).
> Where this document departs from the brainstorm, the reasoning is recorded as
> an ADR under `docs/decisions/`. Section 12 lists every deliberate deviation.

## 1. Goal

Turn a messy fund-universe CSV plus mandate constraints into a professional,
**fully auditable** Investment Committee (IC) memo: a ranked shortlist and a
written recommendation where **every quantitative claim traces back to the exact
source row and formula that produced it.**

The build is optimized as a take-home for the Applied-AI founding-engineer role
at Equi: it should read as production-minded (clean seams, tests, guardrails)
while shipping one narrow path done *excellently* rather than ten done halfway.
It runs entirely locally — one command to set up, one command to demo.

## 2. Scope — phased, honest about 7 days

The brainstorm lists ~15 capabilities that together are 4–6 weeks of work. The
winning move is a razor-thin vertical slice that is correct and demoable, with
the rest scoped as designed-for-but-deferred. Priorities use MoSCoW.

**Phase 1 — the spine (Must).** CSV ingest + normalization → deterministic
metrics engine (unit-tested) → mandate-aware scoring → ranked shortlist →
structured, sourced IC memo → audit trail (claim ↔ source) → Markdown/JSON
export. Driven and demoed entirely through `./amb`.

**Phase 2 — the deliverables (Should).** Rich local exports over the same core: a
styled, Equi-branded HTML memo (print-to-PDF ready) and a formatted XLSX workbook
(shortlist · all-fund metrics · audit trail). No web server — the CLI is the
surface (ADR-0009).

**Phase 3 — the flourish (Could).** What-if mandate simulations; smart model
routing + caching; text RAG over fund notes; feedback capture.

**Non-goals (Won't, this cut).** Multi-tenant auth, real-time market feeds in the
demo path, pgvector over numeric data, self-improving training loop, white-label
theming. Each is name-checked in the architecture as an extension point so the
"built to extend" story is real without building it.

## 3. Product flow

1. Provide one or more CSVs (fund details, returns, notes).
2. Define the mandate in a simple, config-driven form (constraints + weights).
3. The system normalizes data, attaches benchmarks, computes metrics, and runs
   the agentic analysis.
4. It returns a ranked shortlist and a full IC memo whose every figure is a
   clickable link to its source data and formula.
5. Reviewer iterates (adjust mandate, re-rank) and exports.

## 4. Architecture

Layered, with one hard rule that shapes everything: **the LLM orchestrates and
narrates; it never computes a number and never touches storage directly.**

```
CLI (./amb)  +  file exports (md · json · html · xlsx)   ── product surface
    │
Orchestrator (pipeline): validate → metrics → shortlist → draft → risk-review
    │
Retrieval layer (typed) — the ONLY way the memo reaches numbers
    │
Core (amb_core): ingest · metrics · scoring · retrieval · memo · export
    │
Storage (SQLite local, optional)   ·   External adapters (benchmarks, snapshotted)
```

`amb_core` is a plain Python package usable with zero web/agent layers — that is
what `./amb` exercises directly, and what the unit tests target.

## 5. Subsystems

### 5.1 Ingestion & normalization
Accept single or multiple CSVs. Auto-detect columns (fund id/name, dates,
returns, AUM, fees, notes), infer return frequency, coerce locale quirks
(European decimals, `%` strings, thousands separators), and quarantine
unparseable rows rather than silently dropping them. Persist **raw** and
**cleaned** versions with a content hash so every downstream number can name its
input. Missing/inconsistent data is surfaced, not hidden.

### 5.2 Metrics engine — the source of truth
Deterministic, pure-Python, unit-tested against hand-checked golden values.
Computes allocator-grade metrics: annualized return, volatility, **Sharpe,
Sortino, Calmar**, max drawdown, downside deviation, alpha/beta vs. benchmark,
correlation, tracking error, hit rate. Explicit and tested handling of:
annualization from detected frequency, the **risk-free rate source** (FRED), and
short/patchy series. This engine is the ground truth; the memo only ever *reports*
its outputs. (ADR-0004.)

### 5.3 Retrieval — deterministic first, RAG only for text
Numbers are retrieved by **typed tool calls over SQL/pandas** — exact,
inspectable, auditable. Semantic vector search is reserved for *unstructured*
text (fund notes, strategy blurbs) and only if such a corpus exists. No pgvector
over numeric tables; that is an anti-pattern that also breaks auditability.
(ADR-0002.)

### 5.4 Agentic memo generation — structured claims, not prose-first
A LangGraph flow: **validate → compute metrics → build shortlist → draft →
risk-review**. Generation is **claim-first**: the model emits a list of typed,
Pydantic-validated `Claim` objects, each already carrying its provenance
(source ids + formula/metric ref + value); prose is *rendered from* claims, not
linked to them after the fact. This is what makes "click any sentence → see the
source" actually sound instead of decorative. (ADR-0003.)

### 5.5 Audit trail & provenance
Every `Claim` references: the cleaned dataset hash, the specific source rows, the
metric/formula id, and the computed value. The memo renderer emits, alongside the
human text, a machine artifact (JSON) mapping each sentence → claim → sources.
The UI later turns that into click-through; in Phase 1 it is inspectable via
`./amb` and the exported JSON.

### 5.6 Export
Phase 1: Markdown + JSON (memo + audit map). Phase 2: PDF (HTML template →
WeasyPrint) and XLSX (openpyxl) with Equi-inspired styling.

## 6. Core data model (sketch)

```
Fund(id, name, strategy, aum, inception, fee, source_row_ref)
ReturnSeries(fund_id, freq, points[date, value], source_hash)
Benchmark(id, name, as_of, series, source)          # snapshotted
Mandate(constraints[], weights{}, risk_free_ref)
MetricResult(fund_id, metric, value, inputs_ref, formula_id)   # deterministic
Claim(text, value, metric_ref, source_refs[], confidence)      # LLM-emitted, validated
Memo(sections[], claims[], shortlist[], audit_map, version)
```

## 7. Tech stack (local-first)

- **Core/backend:** Python 3.12, Pydantic v2, pandas/numpy, SQLAlchemy 2.
- **Agent:** LangGraph + structured outputs; OpenRouter for provider-agnostic
  model access (smart routing: cheap model for extraction/validation, strong for
  drafting/risk).
- **Storage:** SQLite by default (`data/local/amb.sqlite`); Postgres optional via
  `AMB_DATABASE_URL`. (ADR-0007.)
- **Exports (Phase 2):** self-contained HTML (Equi-styled, print-to-PDF) + XLSX (openpyxl).
- **Tooling:** pytest, ruff, mypy — all wired through `./amb`.

## 8. Security & guardrails (right-sized)

Demonstrate the *shape* of production safety without building an auth platform:
a real **tool allow-list** (the agent can only call approved, typed tools — no
free-form DB/LLM access), input sanitization on ingest, and an **audit log of
every LLM/tool call** with correlation ids, cost, and latency. Auth, PII
redaction, and rate limiting are present as clearly-marked seams, scoped to
what's demonstrable.

## 9. Testing strategy

Unit-first, because correctness lives in the metrics engine. Golden-value unit
tests for every metric; contract tests for tool schemas; a prompt/JSON-shape
regression test for memo structure; one end-to-end test through `./amb demo` on
bundled sample data. Live external calls are never in the test path (snapshots).

## 10. Repository structure (target)

```
AllocatorMemoBuilder/
├── amb                     # local control CLI (the test harness)
├── requirements.txt
├── .env.example
├── backend/
│   └── amb_core/           # ingest · metrics · scoring · retrieval · memo · export
├── data/
│   ├── samples/            # bundled demo CSVs (committed)
│   └── local/              # runtime DB / scratch (git-ignored)
├── tests/
└── docs/
    ├── SPEC.md             # this file
    └── decisions/          # ADRs
```
Only `amb`, config, and `docs/` exist today (rails stage). Feature directories
land as their phases begin.

## 11. Deliverables

Clean documented repo; one-command local setup (`./amb setup`) and demo
(`./amb demo`); a README with setup + decisions + extensibility; a short screen
recording (HUD first, then architecture). Decisions are captured as ADRs so the
"why" is legible without a call.

## 12. Deliberate deviations from the brainstorm (`Inspo.md`)

1. **No RAG/pgvector over numeric fund data.** Deterministic tool retrieval;
   vector search only over text. (ADR-0002)
2. **Claim-first memo generation**, not prose-then-link — required for a real
   audit trail. (ADR-0003)
3. **LLM never computes metrics.** Deterministic, unit-tested engine is the
   source of truth. (ADR-0004)
4. **Benchmarks are snapshotted as-of a date** by default; live pull is an opt-in
   adapter — for reproducibility and auditability. (ADR-0005)
5. **SQLite local-first**, Postgres optional (brainstorm had it reversed).
   (ADR-0007)
6. **Phased scope** — one excellent vertical slice over fifteen partial features.
7. **CLI-first delivery.** `./amb` is the primary harness. (ADR-0001)
8. **No web server / HUD.** Product surface is the CLI + file exports
   (Markdown/JSON/HTML/XLSX); FastAPI + Next.js were dropped. (ADR-0009)

## 13. Open questions

- Sample data: synthesize a realistic fund universe, or do you have a CSV to
  target the schema at?
- Memo depth for the demo: one deeply-sourced recommendation, or a shortlist of
  3–5 each with a paragraph?
- Model access: is the OpenRouter key the intended path, and any preferred
  fast/strong model pair?

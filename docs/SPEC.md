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
It runs entirely locally — `./launch` sets up on first run, builds the memo, and
opens it in a browser (with a real live FRED call); `./test` runs the suite.

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
(shortlist · all-fund metrics · audit trail), plus a minimal localhost server so
the browser can make a *live* FRED call and open the memo (ADR-0009 → ADR-0010).

**Phase 3 — the flourish (Could).** What-if mandate re-scoring in the browser;
AI-assisted CSV column mapping for arbitrary uploads; text RAG over fund notes.
The first two shipped; RAG remains a marked seam.

**Non-goals (Won't, this cut).** Multi-tenant auth, real-time market feeds in the
demo path, pgvector over numeric data, self-improving training loop, white-label
theming. Each is name-checked in the architecture as an extension point so the
"built to extend" story is real without building it.

## 3. Product flow

1. Provide a combined fund CSV (or an arbitrary one — the app maps its columns).
2. Define the mandate in a simple, config-driven form (constraints + weights).
3. The system normalizes data, attaches the benchmark, computes metrics, screens
   and scores against the mandate, and drafts a sourced memo.
4. It returns a ranked shortlist and a full IC memo whose every figure traces to
   its source data and formula.
5. Reviewer iterates in the HUD (adjust the mandate, drop a metric, re-score) and
   exports.

## 4. Architecture

Layered, with one hard rule that shapes everything: **the LLM orchestrates and
narrates; it never computes a number and never touches storage directly.**

```
CLI (./amb) + file exports (md · json · html · xlsx) + a localhost HUD  ── product surface
    │
Orchestrator (pipeline.py): ingest → metrics → screen → score → draft → verify
    │
Retrieval layer (typed AnalysisContext) — the ONLY way the memo reaches numbers
    │
Core (amb_core): ingest · metrics · scoring · retrieval · memo · export · serve
    │
External adapters (FRED benchmark, snapshotted by default; live via a localhost proxy)
```

`amb_core` is a plain Python package usable with zero web/agent layers — that is
what `./amb` exercises directly, and what the unit tests target.

## 5. Subsystems

### 5.1 Ingestion & normalization
A **single combined CSV is canonical** (long: date, fund id, return, plus optional
per-fund metadata). Arbitrary/messy CSVs are handled too: the client detects the
shape (long vs wide matrix), infers column roles and value units, and — in served
mode — an LLM *proposes* a column mapping the user confirms (structure only, never
values; see §5.7). Frequency is inferred, locale quirks coerced (European decimals,
`%` strings, thousands separators), and unparseable rows are **quarantined with a
specific reason** (bad date / missing id / unparseable return), never silently
dropped. A content hash on the series ties every downstream number to its input.

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

### 5.4 Memo generation — structured claims, engine-authoritative
A plain deterministic Python pipeline (`pipeline.py`), not a graph framework:
**ingest → metrics → screen → score → draft → verify**. Only the *draft* step
calls a model, and it does so once, through a single structured tool call.
Generation is **claim-first**: the model emits typed, Pydantic-validated `Claim`
objects that name a `(fund, metric)`; the **value shown is taken from the metrics
engine, never from the model**, and a claim citing a metric the engine can't
produce is dropped. So the memo is verified *by construction* for any model — a
fast model can't corrupt a number it never supplies — and "every figure traces to
its formula" is structural, not decorative. (ADR-0003, ADR-0004.)

### 5.5 Audit trail & provenance
Every `Claim` references: the cleaned dataset hash, the specific source rows, the
metric/formula id, and the computed value. The memo renderer emits, alongside the
human text, a machine artifact (JSON) mapping each sentence → claim → sources.
The UI later turns that into click-through; in Phase 1 it is inspectable via
`./amb` and the exported JSON.

### 5.6 Export
Markdown + JSON (memo + audit map), a self-contained Equi-styled **HTML** memo
(the browser HUD; print-to-PDF anywhere), and a formatted **XLSX** workbook
(shortlist · all-fund metrics · audit trail). The HTML inlines versioned CSS/JS
assets, so `export.py` stays a thin assembler.

### 5.7 AI-assisted CSV mapping (served mode)
When a user uploads an unfamiliar CSV, the deterministic detector proposes a
column mapping first; if a model is configured, `/api/map-columns` asks it to
*refine* that proposal — **structure only** (which column is the date / id /
return, the value unit), from the header plus a few sample rows, never the full
file and never a computed value. The user always confirms the mapping before it
runs. This is the same discipline as §5.4: the model organizes, the deterministic
engine computes. (See `docs/AI.md`.)

## 6. Core data model (sketch)

```
Fund(id, name, strategy, aum, inception, fee, source_row_ref)
ReturnSeries(fund_id, freq, points[date, value], source_hash)
Benchmark(id, name, as_of, series, source)          # snapshotted
Mandate(constraints[], weights{}, risk_free_ref)
MetricResult(fund_id, metric, value, inputs_ref, formula_id)   # deterministic truth
Claim(text, metric, fund_id, value, source_refs[], verified)   # value filled from the engine
Memo(sections[], claims[], shortlist[], audit_map, version)
```

## 7. Tech stack (local-first)

- **Core/backend:** Python 3.10+, Pydantic v2 (+ pydantic-settings), pandas.
- **LLM:** provider-agnostic seam (`llm.py`) selected from config —
  **Anthropic direct** with native tool-use by default (ADR-0008), OpenAI as an
  alternate, and an offline deterministic template when no key is set. One
  structured tool call for the draft; a fast model is the default (it only
  narrates — see §5.4). No agent framework.
- **Live data:** a minimal FastAPI server (`serve.py`, localhost) proxies FRED so
  the browser sees a real call without ever holding the key (ADR-0010).
- **Exports:** self-contained HTML (Equi-styled, print-to-PDF) + XLSX (openpyxl) +
  Markdown + JSON audit map.
- **Storage:** file-based today; `AMB_DATABASE_URL` is a config seam for a future
  SQLite/Postgres store (not yet wired — ADR-0007).
- **Tooling:** pytest, ruff, mypy (strict on core) — all wired through `./amb`.

## 8. Security & guardrails (right-sized)

Demonstrate the *shape* of production safety without building an auth platform:
a real **tool allow-list** (the agent can only call approved, typed tools — no
free-form DB/LLM access), input sanitization on ingest, and an **audit log of
every LLM/tool call** with correlation ids, cost, and latency. Auth, PII
redaction, and rate limiting are present as clearly-marked seams, scoped to
what's demonstrable.

## 9. Testing strategy

Unit-first, because correctness lives in the metrics engine. Golden-value unit
tests for every metric; a structure-only contract test for the mapping tool;
regression tests for the classes of bug that have actually bitten (engine value
overrides a wrong model value, quarantine reasons stay specific, the scatter axis
survives an outlier, the benchmark line passes through its marker); and an
end-to-end pass through the pipeline on bundled sample data via `./test`. Live
external calls are never in the test path (snapshots).

## 10. Repository structure (target)

```
AllocatorMemoBuilder/
├── amb  · launch · test    # control CLI + the two operator entrypoints
├── requirements.txt · .env.example
├── backend/
│   └── amb_core/           # ingest · coercion · metrics · scoring · retrieval ·
│                           #   memo · llm · export · serve · marketdata · readiness
│       └── assets/         # versioned memo CSS/JS (the HUD); export.py assembles them
├── data/
│   ├── samples/            # bundled sample dataset.csv (committed, single file)
│   ├── benchmarks/         # as-of FRED snapshot (committed)
│   └── mandates/           # default mandate (constraints + weights)
├── tests/
└── docs/
    ├── SPEC.md             # this file
    ├── AI.md               # how AI is used in the workflow (patterns + guardrails)
    └── decisions/          # ADRs
```

## 11. Deliverables

Clean documented repo; one-command build-and-open (`./launch`) and test (`./test`);
a README with setup + decisions + extensibility; ADRs for the "why" and `docs/AI.md`
for the AI patterns. A short screen recording (HUD first, then architecture).

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
7. **CLI-first delivery.** `./amb` (via `./launch`/`./test`) is the primary
   harness. (ADR-0001)
8. **Web tier: dropped, then right-sized.** The full FastAPI+Next.js tier was cut
   (ADR-0009); a *minimal* localhost server was later re-introduced purely to make
   a live FRED call from the browser and serve the self-contained HUD (ADR-0010).
   No Next.js, no auth tier — the HUD is one self-contained HTML file.

## 13. Resolved questions

- **Sample data:** a realistic 9-fund universe is synthesized deterministically
  (`data/samples/generate.py`) into one combined `dataset.csv`, with a few
  deliberately messy rows to exercise quarantine.
- **Memo depth:** a shortlist of five, each with an analytical paragraph, and one
  clearly-marked leader as the recommendation.
- **Model access:** Anthropic direct (ADR-0008); the drafting default is the fast
  model since the LLM only narrates and every figure is re-derived from the engine.

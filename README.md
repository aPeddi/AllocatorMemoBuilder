# AllocatorMemoBuilder

Turn a messy fund-universe CSV + mandate constraints into a professional, **fully
auditable** Investment Committee memo — a ranked shortlist and a written
recommendation where every number links back to the exact source row and formula
that produced it.

## Quickstart (local)

```bash
./amb setup     # create .venv, install deps, seed .env from template
./amb doctor    # confirm the environment is ready
./amb demo      # run the full pipeline on bundled sample data
```

Add your `OPENROUTER_API_KEY` to `.env` before generating a memo. Run `./amb`
with no arguments for the interactive menu, or `./amb -h` for every command.

## How it's built

- **Deterministic metrics engine is the source of truth.** Sharpe, Sortino,
  Calmar, drawdown and friends are computed by unit-tested Python; the LLM
  narrates them, it never does the math.
- **Retrieval over structured data is exact and typed** — no vector search over
  numbers. (That keeps the audit trail honest.)
- **Memos are assembled from typed, sourced claims**, so "click any sentence →
  see the source" is real, not decorative.
- **Benchmarks are snapshotted as-of a date** — a memo is reproducible.
- **Local-first:** SQLite, one-command setup, no external services to stand up.

## Docs

- [`docs/SPEC.md`](docs/SPEC.md) — canonical product + architecture spec
- [`docs/decisions/`](docs/decisions/) — Architecture Decision Records (the "why")
- [`BRANCHING.md`](BRANCHING.md) — git workflow, encoded in `./amb`

## Status

Rails stage: the `./amb` harness, the spec, the decision log, and the branching
model are in place. The pipeline lands phase by phase — see `docs/SPEC.md` §2.

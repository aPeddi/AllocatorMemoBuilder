# AllocatorMemoBuilder

Turn a messy fund-universe CSV + mandate constraints into a professional, **fully
auditable** Investment Committee memo — a ranked shortlist and a written
recommendation where every number links back to the exact source row and formula
that produced it.

## Run it

```bash
./amb
```

That's the whole thing. On first run it sets up a virtualenv and installs
dependencies, then builds the memo from the bundled sample data and opens it in
your browser. With an `ANTHROPIC_API_KEY` in `.env` it writes a live LLM memo;
without one it falls back to a deterministic offline memo — either way every
figure is verified against the metrics engine.

Other commands: `./amb test` (run the suite) · `./amb setup` (reinstall deps).

## How it's built

- **Deterministic metrics engine is the source of truth** — Sharpe, Sortino,
  Calmar, drawdown and friends are unit-tested Python; the LLM narrates them, it
  never does the math.
- **Retrieval over structured data is exact and typed** — no vector search over numbers.
- **Memos are assembled from typed, sourced claims**, so every sentence traces to its data.
- **Exports:** Markdown, JSON (audit map), self-contained HTML (print-to-PDF), and XLSX.
- **Local-first:** no server, one command, nothing external to stand up.

## Docs

- [`docs/SPEC.md`](docs/SPEC.md) — product + architecture spec
- [`docs/decisions/`](docs/decisions/) — Architecture Decision Records (the "why")
- [`BRANCHING.md`](BRANCHING.md) — git workflow

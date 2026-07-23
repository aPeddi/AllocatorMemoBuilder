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

## Live market data (real API call in the browser)

```bash
./amb serve        # then open http://127.0.0.1:8000
```

`./amb serve` runs a tiny local API and serves the memo. On load the page makes a
real call to `/api/market`, and the server fetches live data from the **FRED API**
(S&P 500 + 3-month T-bill) and returns it — the page flips to **LIVE · FRED** and
the trajectory redraws against the real index.

Why a server at all? FRED sends no CORS header, so a browser can't call it
directly; the local proxy is the standard way around that. It also means the
`FRED_API_KEY` stays **server-side only** and is never shipped to the browser.
Put your free key in `.env` (git-ignored):

```
FRED_API_KEY=your_fred_api_key
```

Opened as a plain file (no server) or with no key, the app falls back to the
committed benchmark snapshot, so it always works offline.

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

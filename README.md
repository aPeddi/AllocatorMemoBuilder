# AllocatorMemoBuilder

Turns a fund-universe CSV + a mandate into a fully auditable Investment Committee
memo — a ranked shortlist and a written recommendation where every number traces
back to the source row and formula that produced it.

## Setup & run

```bash
./launch     # one command: venv + deps + build the memo + serve + open in browser
./test       # run the test suite
```

`./launch` is self-setting-up on first run (creates a virtualenv, installs
dependencies, installs `backend/` as the editable `amb_core` package). It then
builds the memo from the bundled sample data, starts a local server, and opens the
app — which makes a **real market-data API call** (S&P 500 + 3-month T-bill) and
renders against the live index. `Ctrl+C` to stop.

### Configuration — `.env` (git-ignored)

```
AMB_BENCHMARK_PROVIDER=auto  # auto | fred | yahoo  (auto tries both; page lets you pick)
FRED_API_KEY=...             # optional — the keyed FRED API (keyless CSV works without it)
AMB_YAHOO_API_KEY=...        # optional — only for a gated Yahoo gateway; Yahoo is keyless by default
AMB_LLM_PROVIDER=anthropic   # anthropic | openai | none   (none = offline template)
ANTHROPIC_API_KEY=...        # when provider = anthropic
OPENAI_API_KEY=...           # when provider = openai
```

Two live benchmark sources are supported: **FRED** (price-return index levels) and
**Yahoo Finance** (dividend-adjusted / total-return levels, keyless). With
`AMB_BENCHMARK_PROVIDER=auto` the server pulls both and, when both return data, the
page asks which reference index you want (and lets you switch from the market-data
chip); pin one with `fred` or `yahoo`. With no keys the app still runs fully offline:
committed benchmark snapshot + a deterministic template memo. Either way, **every
figure is verified against the metrics engine** before it reaches the page.

## How it's built (and why)

- **The deterministic metrics engine is the source of truth.** Sharpe, Sortino,
  Calmar, drawdown and friends are unit-tested Python; the LLM only *narrates*.
  Every figure shown is taken from the engine, not the model — a claim citing a
  metric the engine can't produce is dropped — so the memo is verified by
  construction, and even a fast model can't put a wrong number on the page.
- **Model-agnostic LLM.** The memo writer is a pluggable provider (Anthropic /
  OpenAI / offline template) selected from config; adding a provider is one branch.
  Fund data is treated as untrusted input (fenced, data-only system prompt) to
  resist prompt injection.
- **Secrets stay server-side.** The browser can't call FRED directly (no CORS), so
  a tiny local proxy holds the key and the page fetches `/api/market`; the key is
  never shipped to the client. Data embedded in the page is escaped to be XSS-safe,
  and the server binds to localhost with conservative headers.
- **Modular rendering.** The memo's CSS/JS live as versioned assets under
  `backend/amb_core/assets/`; `export.py` is a thin assembler.
- **Local-first.** One command, nothing external to stand up. Exports: Markdown,
  JSON audit map, self-contained HTML (print-to-PDF), and XLSX.

## Docs

- [`docs/SPEC.md`](docs/SPEC.md) — product + architecture spec
- [`docs/AI.md`](docs/AI.md) — how AI is used in the workflow (patterns + guardrails)
- [`docs/decisions/`](docs/decisions/) — Architecture Decision Records (the "why")
- [`BRANCHING.md`](BRANCHING.md) — git workflow

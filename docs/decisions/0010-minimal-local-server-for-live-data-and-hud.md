# 0010 — A minimal local server for live market data + the decision HUD

**Status:** Accepted · 2026-07-26 · supersedes [ADR-0009](0009-local-first-surface.md)

## Context
ADR-0009 dropped the web tier: for a single-user local tool, a server was pure
overhead. Two things changed that calculus:

1. **Live market data.** The memo is far more convincing when the benchmark is a
   *real* FRED call made live, in front of the reviewer — not a committed
   snapshot. But a browser can't call FRED directly (no CORS header), and the API
   key must never ship in client code.
2. **The decision HUD.** The self-contained HTML export grew into a cinematic
   "decision" view (ingest → screen → score → recommend) that reviewers open in a
   browser. Serving it locally makes `./launch` a single "build + open" step.

Both need exactly one thing ADR-0009 removed: a tiny local process that can hold a
secret and answer `fetch()`.

## Decision
Re-introduce a **minimal** FastAPI server (`serve.py`), bound to `127.0.0.1`, that
does two jobs and nothing else: (1) proxy live FRED calls so the key stays
server-side and the browser sees a real network request, and (2) serve the built
HTML memo. `./launch` builds the memo, starts this server, and opens the page.
The file exports (Markdown, JSON audit map, HTML, XLSX) from ADR-0009 remain the
portable deliverables; the server is a convenience layer over them, not a
replacement.

It stays local-first: single-user, localhost-only, no auth tier, no framework on
the client (the HUD is one self-contained HTML file). Endpoints take no
client-supplied input beyond a whitelisted mode, so the injection surface is
essentially nil.

## Consequences
- The demo makes a genuine, observable live API call — the strongest possible
  signal that the data path is real.
- One process to run, but only on `./launch`; `./test` and the core stay
  server-free, and everything still runs offline (snapshot fallback) with no key.
- `fastapi`/`uvicorn` are dependencies again — the honest cost of the above.

## Alternatives considered
- **Stay serverless (ADR-0009 as-is):** keeps things lean, but the benchmark can
  only ever be a snapshot and the HUD can't make a live call — losing the single
  most credible moment of the demo.
- **Ship the FRED key to the browser:** unacceptable; a secret in client code.
- **Pre-fetch FRED at build time:** works, but it's no longer *live* in front of
  the reviewer, which was the whole point.

# 0011 — A second live benchmark provider (Yahoo Finance) + a source chooser

**Status:** Accepted · 2026-07-27 · refines [ADR-0005](0005-benchmark-snapshotting.md), [ADR-0010](0010-minimal-local-server-for-live-data-and-hud.md)

## Context
ADR-0010 made the benchmark a *live* call, proxied server-side. That call was
FRED-only. Two limitations surfaced:

1. **FRED's index series are price-return** (dividends excluded unless keyed), and
   FRED can be unreachable behind some networks — leaving only the committed
   snapshot with no second live option.
2. The take-home brief names "a public market-data API (e.g. Yahoo Finance, FRED)."
   Supporting a single provider met the letter but not the spirit of a data layer
   that isn't tied to one vendor.

## Decision
Add **Yahoo Finance** as a second live benchmark provider alongside FRED, behind a
small provider abstraction:

- `marketdata.py` gains `fetch_benchmark_yahoo` / `_read_yahoo` (the keyless public
  chart endpoint — dividend-adjusted, i.e. total-return, monthly levels), a
  `_PROVIDERS` registry, and `resolve_providers()` which probes every provider.
- `resolve_benchmark(..., provider=…)` honors `AMB_BENCHMARK_PROVIDER = auto | fred
  | yahoo`; `auto` tries FRED then Yahoo, then cache, then snapshot.
- `serve.py`'s `/api/market` returns a per-provider availability map. When **more
  than one source is live**, the page presents a one-time chooser (which reference
  index to measure against), remembers the choice for the session, and lets the
  user switch from the market-data chip. Keys (FRED, and an optional gated-Yahoo
  key) are read server-side only and never shipped to the browser.

This does not reverse ADR-0005 (snapshot-by-default, live opt-in) or ADR-0010
(server holds the secret, browser sees a real call) — it broadens the live path
from one vendor to two and puts the choice in the user's hands.

## Consequences
- The data layer is no longer single-vendor; if one provider is down or blocked,
  the other still gives a live curve before falling back to the snapshot.
- Yahoo's adjusted close is a truer (total-return) benchmark than FRED's price index;
  the two can differ by a few points a year, so the source is labeled everywhere it
  shows and the user can pick.
- Minor added surface: a provider registry, a probe path, and a client chooser —
  covered by tests (provider parsing, order/selection, the probe, and the chooser).

## Alternatives considered
- **Stay FRED-only:** simplest, but tied to one vendor and to price-return indices,
  and only half-answers the brief's "Yahoo/FRED."
- **Silently prefer one provider:** loses the reviewer-facing point that the data
  layer is pluggable and that price vs. total-return is a real, surfaced choice.
- **Add Yahoo but pick automatically, no UI:** simpler, but the difference between
  the two indices is exactly the kind of thing an allocator should see and control.

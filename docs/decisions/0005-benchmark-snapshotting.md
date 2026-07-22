# 0005 — Benchmarks snapshotted as-of a date; live pull is opt-in

**Status:** Accepted · 2026-07-22

## Context
The brainstorm pulls live benchmarks (Yahoo Finance, FRED) at runtime. Live calls
are rate-limited, occasionally down, and — worse for this product —
**non-deterministic**: the same memo generated twice would cite different numbers,
which is incoherent with an audit trail and impossible to test against. It also
makes a live demo fragile.

## Decision
Default `AMB_BENCHMARK_MODE=snapshot`: benchmark and risk-free series are cached
**as-of an explicit date** into committed fixtures, and every memo records the
as-of date it used. A `live` mode behind the same adapter interface can refresh
snapshots on demand, but it is opt-in and never on the test or demo path.

## Consequences
- Reproducible, auditable numbers; a memo is a stable artifact.
- The demo runs offline and never flakes on a third-party outage.
- Tests exercise real code paths without network dependence.
- Snapshots must be refreshed deliberately; the as-of date is visible in output
  so staleness is never silent.

## Alternatives considered
- **Live-only:** rejected — non-deterministic, flaky, and untestable.
- **Mock the adapter in tests but live in the app:** leaves the demo fragile and
  the app's numbers unreproducible; snapshotting fixes both with one mechanism.

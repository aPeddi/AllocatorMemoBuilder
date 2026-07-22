# 0001 — `./amb` CLI as the primary dev & test harness

**Status:** Accepted · 2026-07-22

## Context
The product's real substance is a data → metrics → memo pipeline. A front-end is
needed for the demo, but building UI-first would gate every correctness check
behind a browser and slow the core loop. The brainstorm also asks for
"one-command local setup" and an easy way to "test stuff out" locally.

## Decision
Build a single bash entrypoint, `./amb`, that is the canonical way to set up,
run, and test the system: `setup`, `doctor`, `ingest`, `metrics`, `memo`,
`demo`, `test`, `serve`, `ui`, plus git-workflow helpers. `amb_core` stays
importable and runnable with no web or agent layers, so the pipeline can be
exercised and unit-tested directly. The HUD is a presentation layer over the same
core, built last.

## Consequences
- Fast, deterministic inner loop; correctness never waits on the UI.
- "One-command setup/demo" is a first-class, testable deliverable, not an
  afterthought.
- The CLI must degrade gracefully before the backend exists (it reports
  "not wired up yet" instead of crashing) so it is runnable from day one.
- Slight duplication of entrypoints (CLI + API) — acceptable; both are thin over
  `amb_core`.

## Alternatives considered
- **UI-first / full-stack from day one:** better demo earlier, but couples
  correctness work to front-end plumbing and slows iteration.
- **Makefile / raw scripts:** works, but a menu-driven CLI matches the operator's
  existing conventions and is friendlier to demo live.

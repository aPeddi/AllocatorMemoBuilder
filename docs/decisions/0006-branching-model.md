# 0006 — Trimmed main/develop/feature/release/hotfix model

**Status:** Accepted · 2026-07-22

## Context
The project needs a branching strategy that keeps `main` always-demoable and
produces a clean, reviewable history, without the overhead a large team or a
deploy pipeline would demand. A reference model on hand (GRID) is richer than
needed — it carries a self-modify "evolution" lane and Vercel deploy-authorization
rules that don't apply to a local-only take-home.

## Decision
Adopt a right-sized model: **`main`** (always green/demoable) ← release merges
and hotfixes only; **`develop`** integration line; **`feature/*`** short-lived
work; **`release/vX.Y`** to stabilize a cut; **`hotfix/*`** from `main`.
Conventional Commits; squash features into `develop`, merge-commit releases into
`main` and tag `vX.Y`; rollback via tags. `./amb feature|release|hotfix|st`
encodes the flow. Full detail in `BRANCHING.md`.

## Consequences
- There is always one commit (`main`) that builds and demos cleanly.
- History is greppable and a changelog is derivable at release time.
- Discipline is manual (no CI gate locally) — the CLI helpers and this record are
  what keep it consistent.

## Alternatives considered
- **Trunk-based / commit-straight-to-main:** too easy to leave the demo line
  broken mid-iteration.
- **Full GRID model (evolution lane, deploy-auth rules):** unnecessary ceremony
  for a local solo build; dropped the parts that don't apply.

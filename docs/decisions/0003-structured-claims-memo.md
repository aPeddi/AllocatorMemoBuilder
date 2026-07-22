# 0003 — Claim-first memo generation, not prose-then-link

**Status:** Accepted · 2026-07-22

## Context
The signature feature is "click any memo sentence → see the exact source
data/formula." If the model writes free prose and we try to link citations back
afterward, the mapping is fuzzy and fragile: sentences blend multiple facts,
numbers get paraphrased, and provenance becomes a guess. Auditability has to be
built into generation, not bolted on.

## Decision
Generate **claims first**. The agent emits a list of typed, Pydantic-validated
`Claim` objects — each carrying its text, the value asserted, the metric/formula
id, and the source row references — and the human-readable memo is **rendered
from** those claims. Alongside the prose, the renderer emits a machine audit map
(sentence → claim → sources). Structured output is enforced at the tool-call
layer so malformed claims are rejected and retried.

## Consequences
- The audit trail is exact and mechanical, not heuristic.
- Every asserted value is validated against the deterministic metric engine
  before it can enter the memo (ties into ADR-0004).
- Slightly more constrained prose than free generation; worth it for
  trustworthiness. A light "polish" pass can improve flow *without* touching
  numbers.
- Testable: memo structure and claim/source integrity can be asserted in CI.

## Alternatives considered
- **Prose-first + post-hoc citation linking:** simpler prompt, but produces an
  audit trail that looks real and isn't — the opposite of the goal.
- **Templated memo with slotted numbers, no LLM narrative:** maximally auditable
  but loses the analytical writing that makes the memo valuable.

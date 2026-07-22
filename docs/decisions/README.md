# Architecture Decision Records

This is the project's decision log — the "why" behind the foundational calls, so
the reasoning survives past the moment it was made and a reviewer can follow the
thinking without a walkthrough.

Each record uses a lightweight [MADR](https://adr.github.io/madr/)-style format:
**Context → Decision → Consequences → Alternatives considered.** Records are
immutable once **Accepted**; to change a decision, add a new ADR that
**Supersedes** (or refines) the old one rather than editing history.

| ADR | Decision | Status |
|-----|----------|--------|
| [0001](0001-cli-first-development.md) | `./amb` CLI is the primary dev + test harness | Accepted |
| [0002](0002-deterministic-retrieval-over-rag.md) | Deterministic retrieval over structured data; RAG for text only | Accepted |
| [0003](0003-structured-claims-memo.md) | Claim-first memo generation, not prose-then-link | Accepted |
| [0004](0004-metrics-engine-source-of-truth.md) | Metrics computed by deterministic engine; LLM never does math | Accepted |
| [0005](0005-benchmark-snapshotting.md) | Benchmarks snapshotted as-of a date; live pull is opt-in | Accepted |
| [0006](0006-branching-model.md) | Trimmed main/develop/feature/release/hotfix model | Accepted |
| [0007](0007-local-first-storage-sqlite.md) | SQLite local-first; Postgres optional | Accepted |
| [0008](0008-anthropic-direct-model-access.md) | Anthropic direct (native tool-use) over OpenRouter | Accepted |
| [0009](0009-local-first-surface.md) | Local-first surface: CLI + file exports, no web server | Accepted |

New ADRs: copy the shape of an existing one, take the next number, start at
**Proposed**, move to **Accepted** when the direction is locked.

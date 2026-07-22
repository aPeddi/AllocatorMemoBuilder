# 0007 — SQLite local-first; Postgres optional

**Status:** Accepted · 2026-07-22

## Context
The brainstorm specifies PostgreSQL + pgvector with SQLite as a fallback. But the
whole build is local and single-user, pgvector was dropped for numeric data
(ADR-0002), and a "one-command setup" shouldn't require standing up a database
server. Optimizing for a frictionless local demo points the other way.

## Decision
**SQLite is the default** (`AMB_DATABASE_URL=sqlite:///./data/local/amb.sqlite`),
accessed through SQLAlchemy 2 so the storage layer is engine-agnostic. Postgres is
supported by pointing `AMB_DATABASE_URL` at it — no code change. The local DB file
lives under the git-ignored `data/local/`.

## Consequences
- `./amb setup` needs no external services; the demo is truly one command.
- The SQLAlchemy seam keeps a Postgres upgrade path open for a real deployment.
- No vector-store dependency, consistent with deterministic retrieval.

## Alternatives considered
- **Postgres + pgvector as primary:** operational overhead with no local benefit,
  and pgvector isn't used for numeric data anyway.
- **Files/JSON only, no DB:** simplest, but a real schema with versioning and
  provenance is part of the production-mindedness the take-home is showing.

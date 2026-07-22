# 0002 — Deterministic retrieval over structured data; RAG for text only

**Status:** Accepted · 2026-07-22

## Context
The brainstorm calls for RAG over "cleaned data + metrics" with pgvector. But the
inputs are **structured numeric tables**. Embedding numbers and retrieving them
by semantic similarity is imprecise, non-reproducible, and — critically —
**breaks auditability**, which is the product's headline feature. Vector recall
can also silently miss or blend rows, which is unacceptable for figures that go
into an investment recommendation.

## Decision
Numbers are retrieved by **typed, deterministic tool calls over SQL/pandas** —
exact, inspectable, and traceable to specific rows. Semantic vector search is
reserved for **unstructured text** (fund notes, strategy descriptions,
prospectus blurbs) and only introduced if such a corpus actually exists
(Phase 3). No pgvector over numeric data in any phase.

## Consequences
- Every number in the memo can name the exact rows and formula it came from.
- Results are reproducible run-to-run — a prerequisite for a trustworthy audit
  trail and for tests.
- We forgo the "RAG everywhere" narrative in favor of a stronger one: knowing
  when *not* to use RAG.
- If a real text corpus appears, a text-only retrieval module slots in behind the
  same tool interface.

## Alternatives considered
- **Full RAG/pgvector as specified:** rejected — wrong tool for numeric data,
  and directly undermines auditability.
- **No vectors at all, ever:** viable for the core, but leaves genuine
  unstructured-text search on the table; keep it as a scoped Phase-3 option.

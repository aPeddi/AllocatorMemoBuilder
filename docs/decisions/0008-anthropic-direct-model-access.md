# 0008 — Anthropic direct for model access

**Status:** Accepted · 2026-07-22 · refines the stack in SPEC §7

## Context
The brainstorm named OpenRouter for provider-agnostic access. In practice the
operator already has a working Anthropic API key and standardizes on Anthropic
models elsewhere (`claude-sonnet-4-6`, `claude-haiku-4-5-*`). For a local
take-home, routing through an aggregator adds a hop and an account for no benefit,
and Anthropic's native tool-use gives first-class structured output — which the
claim-first memo (ADR-0003) depends on.

## Decision
Call the **Anthropic API directly** via the official SDK. Keep smart routing:
`AMB_MODEL_FAST` (haiku-class) for extraction/validation, `AMB_MODEL_STRONG`
(sonnet-class) for drafting + risk review. Structured output is enforced with
Anthropic tool-use (forced `tool_choice`). The key lives in the git-ignored
`.env` as `ANTHROPIC_API_KEY`; it is never committed. The LLM call sits behind a
thin `llm.py` seam so a different provider (incl. OpenRouter) could slot in later.

## Consequences
- Native structured output → reliable, validated `Claim` objects.
- One less dependency and account; simpler local setup.
- Provider-specific code is quarantined in `llm.py`; the rest of the core is
  provider-agnostic, preserving the extension point.

## Alternatives considered
- **OpenRouter (as specified):** fine, but an extra hop/account with no local
  upside and weaker structured-output ergonomics for this use.
- **Multi-provider abstraction now:** premature; the `llm.py` seam is enough
  until a second provider is actually needed.

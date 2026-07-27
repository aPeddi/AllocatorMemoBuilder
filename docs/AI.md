# AI in the workflow

This project uses an LLM where language models are genuinely good — turning verified
numbers into clear, allocator-grade prose, and reading the shape of a messy CSV — and
keeps it well away from anything where a wrong answer would be silent and expensive.
The organizing principle is one sentence:

> **The model organizes and narrates; the deterministic engine computes and verifies.**

Everything below is how that principle is enforced in code, not an aspiration. The
two places AI actually runs are memo drafting (`llm.py` + `memo.py`) and AI-assisted
CSV column mapping (`llm.py` + `serve.py`). Both follow the same discipline.

## 1. Narrate, don't compute — and verify by construction

The memo is generated *claim-first*. The model is handed the funds' already-computed
metrics and asked for a structured payload: a summary, a recommendation, one paragraph
per shortlisted fund, and a set of typed `Claim`s. Crucially, each claim only names a
`(fund, metric)` — it does **not** get to decide the number.

When the claims come back, `memo._mk_claims` looks each one up in the deterministic
metrics engine and fills in the *engine's* value. A claim that cites a metric the
engine can't produce is dropped rather than shown. So:

- The displayed figure is always the engine's, never the model's.
- A weaker/faster model cannot put a wrong number on the page — it never supplies one.
- "Every figure traces to its formula" is true by construction, not by after-the-fact
  checking. The audit map (`audit.py`) records the source rows and formula id per claim.

This is why we can default to a *fast* model for drafting (see §4) without any
correctness cost: quality of prose scales with the model; correctness does not depend
on it at all. The regression test `test_engine_value_overrides_model_and_drops_unresolvable`
pins this behaviour.

## 2. One structured call, forced schema

Drafting is a single tool call, not a multi-step agent graph. The provider forces the
model to answer by calling one tool (`submit_memo`) whose `input_schema` is the memo
shape, so we get validated JSON back or nothing — no free-form parsing, no "please
respond in JSON" and hope. The same pattern is used for mapping (`submit_mapping`).
Keeping it to one deterministic pipeline with one model call at a known step makes the
whole flow easy to reason about, cheap, and trivial to test.

## 3. Untrusted input, prompt-injection hardening

Fund data is treated as hostile. It is fenced inside `<fund_data>` markers, and the
system prompt tells the model to treat everything between them strictly as data, never
as instructions — even if it looks like a command. The mapping assist goes further: it
only ever sees the header row plus a few sample rows (never the whole file, never a
value it could smuggle through), and it returns *column indices and a unit*, never a
parsed number. `test_llm_is_model_agnostic_with_injection_guardrail` and
`test_propose_mapping_is_structure_only_and_bounded` guard these.

Downstream, anything model- or CSV-derived that reaches the HTML is escaped
(`export._json_for_script`, `esc()` in the client) so a fund named `</script>` can't
break out — verified by `test_script_embedding_is_xss_safe`.

## 4. Model-agnostic, with graceful degradation

`select_claims_provider()` is a small composition root: it reads config once and binds
a ready `AnalysisContext -> payload` callable. Providers are Anthropic (default, native
tool-use — see ADR-0008), OpenAI, or — when no key is set — a deterministic offline
template that assembles real prose from the real engine numbers. Adding a provider is
one function and one branch.

Model *routing* is deliberate: the drafting default is the **fast** model, because §1
means the model only narrates. A **strong** model is available via `AMB_MODEL_FAST` /
`AMB_MODEL_STRONG` for anyone who wants a heavier draft, but it buys prose polish, not
correctness. The offline template means the whole app — and the entire test suite —
runs with no key and no network.

## 5. AI-assisted CSV mapping (structure only)

When a reviewer uploads an unfamiliar CSV, a deterministic client-side detector guesses
the mapping first (which column is the date / id / return, long vs wide matrix, the
value unit). In served mode, `/api/map-columns` then asks a model to *refine* that guess
— header + a few sample rows in, column indices + unit out — and the user always
confirms the mapping before anything runs. The model helps read the file's *shape*; the
engine still does every computation. If no model is configured, the deterministic guess
stands on its own.

## 6. Observability

Every model call is logged to `exports/llm_calls.jsonl` with provider, model, latency,
token usage, and a correlation id. Because the call is a single structured step, the log
is a clean, greppable record of exactly what the model was asked and what it returned —
useful for cost tracking and for debugging a bad draft without re-running the app.

## 7. What we deliberately did *not* do

- **No RAG / vector store over the numbers.** Numeric retrieval is exact, typed, and
  auditable; semantic search is the wrong tool for a metrics table and would break the
  audit trail (ADR-0002).
- **No agent framework.** A single structured call inside a deterministic pipeline is
  simpler, cheaper, and easier to test than a graph of model calls for this task.
- **No model-computed math, ever.** The one rule that shapes everything (ADR-0004).

## Where to look

| Concern | Code | Test |
|---|---|---|
| Narrate-not-compute, engine-authoritative claims | `memo._mk_claims`, `memo._resolve` | `test_memo.py`, `test_regressions.py` |
| Structured tool call + provider seam | `llm.py` (`_MEMO_TOOL`, `select_claims_provider`) | `test_phase3.py` |
| Prompt-injection fencing | `llm._SYSTEM`, `llm._build_prompt` | `test_phase3.py` |
| CSV mapping assist (structure only) | `llm.propose_mapping`, `serve.py` `/api/map-columns` | `test_phase3.py` |
| XSS-safe embedding | `export._json_for_script` | `test_phase3.py` |

See also the reusable capability specs in [`docs/skills/`](skills/).

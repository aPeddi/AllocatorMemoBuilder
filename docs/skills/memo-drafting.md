# Skill · memo-drafting

Turn a set of **already-verified** fund metrics into a clear, allocator-grade
Investment Committee memo — without letting the model touch a single number.

## When to use
A ranked shortlist exists and its metrics are computed by the deterministic engine.
You want readable prose (summary, recommendation, per-fund analysis, key risks) that
stays perfectly consistent with those numbers.

## When *not* to use
- To compute or estimate a metric — that's the engine's job, always.
- To make a ranking/selection decision — scoring is deterministic and mandate-driven.

## Input surface (what the model may see)
The shortlist's facts only, fenced as untrusted data:

```
<fund_data>
fund_id,name,strategy,ann_return,ann_vol,sharpe,sortino,calmar,max_drawdown,beta,...
...one row per shortlisted fund...
</fund_data>
```

Never: raw return series, other funds, secrets, or free-form file contents.

## Output contract (forced schema)
The model must answer by calling `submit_memo`; free-form text is rejected. Shape:

```jsonc
{
  "summary": "string",
  "recommendation": "string",
  "funds": [{ "fund_id": "string", "paragraph": "string",
              "claims": [{ "text": "string", "metric": "sharpe", "fund_id": "EQ-LS" }] }],
  "key_risks": { "body": "string",
                 "claims": [{ "text": "string", "metric": "max_drawdown", "fund_id": "MAC" }] }
}
```

Each claim names a `(fund, metric)`. A `value` may be included but is **ignored** — the
value shown is filled from the engine.

## Guardrails
- **Engine-authoritative values.** `memo._mk_claims` replaces every claim's value with
  the engine's `MetricResult`; a claim citing a metric the engine can't produce is
  dropped. The memo is verified by construction.
- **Injection-fenced.** The system prompt treats `<fund_data>` strictly as data.
- **Qualitative prose.** The prompt asks the model to name metrics and directions, not
  to type digits — the verified figure is rendered beside the claim.
- **XSS-safe.** Model prose is escaped before it enters the HTML.

## Verification
`test_memo.py::test_wrong_value_is_reconciled_to_engine` and
`test_regressions.py::test_engine_value_overrides_model_and_drops_unresolvable`:
a bogus model value (999.0) never reaches the memo, and an unresolvable metric is
dropped, with `verified_count == claim_count`.

## Degradation
No API key → a deterministic offline template produces the same memo shape from the
same engine numbers, so the workflow (and the tests) run fully offline.

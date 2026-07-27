# Skill · csv-column-mapping

Read the *shape* of an unfamiliar fund CSV — which column is the date, the fund id, the
return; long rows vs a dates×funds matrix; how returns are expressed — so it can be
ingested. The model reads structure; it never parses a value.

## When to use
A user uploads a CSV whose layout isn't the canonical one, and the deterministic
detector isn't confident. A model can disambiguate headers like `As Of`, `Ticker`,
`Perf Net (Monthly)` that keyword rules miss.

## When *not* to use
- To read, clean, or convert the actual return values — coercion is deterministic.
- On the canonical dataset, or when the deterministic detector is already confident
  (the model call is skipped — no reason to spend it).

## Input surface (what the model may see)
Only the header row and a handful of sample rows, fenced as untrusted data — never the
full file:

```
<csv>
As Of,Ticker,Perf Net (Monthly),Desk
2024-01-01,ORV,1.2%,Macro
...(≤5 rows)...
</csv>
```

## Output contract (forced schema)
The model answers by calling `submit_mapping` with **0-based column indices** and a
unit — never a value:

```jsonc
{
  "unit": "decimal | percent | bps",
  "date_order": "mdy | dmy",              // only if dates are ambiguous
  "map":     { "date": 0, "id": 1, "ret": 2, "name": 3, "strategy": 4 },  // long files
  "exclude": [5, 6]                        // wide matrix: non-fund columns (totals, benchmarks)
}
```

`_normalize_mapping` drops any out-of-range or wrong-shape field before it's used.

## Guardrails
- **Structure only.** The tool schema has no field for a return value; the model
  literally cannot emit one.
- **Bounded input.** Header + a few rows, not the file.
- **Injection-fenced.** System prompt treats `<csv>` as data, never instructions.
- **Human-in-the-loop.** The proposal is always shown in a confirmation modal; nothing
  runs until the user approves the mapping.
- **Deterministic floor.** With no model, the rule-based detector's proposal stands.

## Verification
`test_phase3.py::test_propose_mapping_is_structure_only_and_bounded`: the CSV is fenced,
the guardrail text is present, and out-of-range / wrong-shape fields the model returns
are stripped.

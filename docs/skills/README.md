# Skills — reusable AI capabilities

Each file here packages one AI capability the way we'd hand it to a teammate (or a
skills-aware runtime): a crisp contract — when to use it, what goes in, what comes
out, and the guardrails that make it safe — decoupled from the call site so it can be
lifted into another workflow unchanged.

The shared discipline across every skill mirrors [`../AI.md`](../AI.md): the model
**organizes and narrates; it never computes and never sees more than it needs.** Each
skill states its input surface (what the model is allowed to see), its output contract
(a forced schema), and how the result is verified downstream.

| Skill | What it does | Model sees | Model returns |
|---|---|---|---|
| [memo-drafting](memo-drafting.md) | Turn verified metrics into an IC memo | shortlist facts (fenced) | typed claims (`(fund, metric)` + prose) |
| [csv-column-mapping](csv-column-mapping.md) | Read a messy CSV's shape | header + a few sample rows | column indices + value unit |

Both are implemented in `backend/amb_core/llm.py` and exercised by `tests/`.

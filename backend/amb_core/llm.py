"""Anthropic access (ADR-0008). Provider-specific code is quarantined here.

Exposes a `claims_provider` callable: AnalysisContext -> structured memo payload.
Structured output is forced via Anthropic tool-use, so the model must return
validated JSON. Every call is logged (model, latency, usage, correlation id).
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Optional

from .config import get_settings
from .retrieval import AnalysisContext

_MEMO_TOOL = {
    "name": "submit_memo",
    "description": "Return the IC memo as structured, individually-sourced claims.",
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "1-2 sentence orientation: what was screened, how many advanced, "
                "and the headline pick. Distinct from the recommendation.",
            },
            "recommendation": {
                "type": "string",
                "description": "2-4 sentence overall recommendation across the shortlist.",
            },
            "key_risks": {
                "type": "object",
                "description": "Portfolio- and fund-level risks. Each claim MUST cite a provided "
                "metric value (deepest drawdown, highest beta, highest vol, liquidity, concentration).",
                "properties": {
                    "body": {"type": "string"},
                    "claims": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "text": {"type": "string"},
                                "metric": {"type": "string"},
                                "fund_id": {"type": "string"},
                                "value": {"type": "number"},
                            },
                            "required": ["text", "metric", "fund_id", "value"],
                        },
                    },
                },
                "required": ["body", "claims"],
            },
            "funds": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "fund_id": {"type": "string"},
                        "paragraph": {
                            "type": "string",
                            "description": "One analytical paragraph on this fund for the IC.",
                        },
                        "claims": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "text": {"type": "string"},
                                    "metric": {"type": "string"},
                                    "fund_id": {"type": "string"},
                                    "value": {"type": "number"},
                                },
                                "required": ["text", "metric", "fund_id", "value"],
                            },
                        },
                    },
                    "required": ["fund_id", "paragraph", "claims"],
                },
            },
        },
        "required": ["summary", "recommendation", "funds", "key_risks"],
    },
}


def _build_prompt(ctx: AnalysisContext) -> str:
    m = ctx.mandate
    return (
        "You are an allocator writing an Investment Committee memo. Use ONLY the "
        "numbers provided below — never invent or recompute a figure. Every claim's "
        "`value` MUST exactly equal one of the provided metric values (decimals, e.g. "
        "0.14 for 14%), and `metric` must be one of: ann_return, ann_vol, sharpe, "
        "sortino, calmar, max_drawdown, alpha, beta, correlation, tracking_error, "
        "hit_rate, downside_dev.\n\n"
        f"MANDATE: {m.name}\n"
        f"Benchmark: {m.benchmark_id}. Risk-free: {m.risk_free_annual:.2%}.\n\n"
        "SHORTLIST FACTS (the only numbers you may cite):\n"
        f"{ctx.facts_table()}\n\n"
        "Write: (1) a 1-2 sentence SUMMARY orienting the reader (what was screened, "
        "how many advanced, the headline pick); (2) a 2-4 sentence overall RECOMMENDATION; "
        "(3) one crisp analytical paragraph per fund, each decomposed into 3-5 claims that "
        "each cite a single metric value; (4) a KEY_RISKS block naming the deepest-drawdown, "
        "highest-beta, and most-volatile shortlisted funds, each as a metric-cited claim, plus "
        "a sentence on liquidity and concentration. Be specific and allocator-grade; no hedging "
        "boilerplate. Every `value` MUST equal a provided number exactly."
    )


def _extract_tool_input(resp, tool_name: str) -> Optional[dict]:
    for block in getattr(resp, "content", []) or []:
        if getattr(block, "type", None) == "tool_use" and getattr(block, "name", None) == tool_name:
            return dict(block.input)
    return None


def _log_call(log_path: str | Path, model: str, dt: float, resp, ctx: AnalysisContext) -> None:
    try:
        p = Path(log_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        usage = getattr(resp, "usage", None)
        rec = {
            "model": model,
            "latency_s": round(dt, 3),
            "correlation_id": getattr(resp, "id", None),
            "input_tokens": getattr(usage, "input_tokens", None),
            "output_tokens": getattr(usage, "output_tokens", None),
            "mandate": ctx.mandate.name,
            "funds": ctx.shortlist_ids(),
        }
        with p.open("a") as fh:
            fh.write(json.dumps(rec) + "\n")
    except Exception:
        pass  # logging must never break generation


def anthropic_claims_provider(
    ctx: AnalysisContext, model: Optional[str] = None, log_path: str = "exports/llm_calls.jsonl"
) -> dict:
    s = get_settings()
    if not s.has_llm:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    import anthropic  # imported lazily so the deterministic path needs no SDK

    client = anthropic.Anthropic(api_key=s.anthropic_api_key)
    model = model or s.strong_model
    t0 = time.time()
    resp = client.messages.create(
        model=model,
        max_tokens=4096,
        tools=[_MEMO_TOOL],
        tool_choice={"type": "tool", "name": "submit_memo"},
        messages=[{"role": "user", "content": _build_prompt(ctx)}],
    )
    dt = time.time() - t0
    payload = _extract_tool_input(resp, "submit_memo") or {"recommendation": "", "funds": []}
    payload["_model"] = model
    _log_call(log_path, model, dt, resp, ctx)
    return payload

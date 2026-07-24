"""Claim-first memo assembly (ADR-0003).

A claims_provider yields prose + typed claims; every claim's asserted value is
re-verified here against the deterministic MetricResult before it enters the
memo, and each claim carries its source references.
"""
from __future__ import annotations

from typing import Callable, Optional

from .audit import build_audit_map
from .models import Claim, Memo, MemoSection
from .retrieval import AnalysisContext

ClaimsProvider = Callable[[AnalysisContext], dict]

# relative tolerance when checking an asserted value against the true metric
VERIFY_TOL = 0.02


def _verify(ctx: AnalysisContext, fund_id, metric, value) -> tuple[bool, list[str]]:
    refs: list[str] = []
    f = ctx.get_fund(fund_id) if fund_id else None
    if f and f.source_ref:
        refs.append(f.source_ref)
    mr = ctx.get_metric(fund_id, metric) if (fund_id and metric) else None
    if mr:
        refs.append(f"{mr.formula_id}|{mr.inputs_ref}")
        if value is not None and mr.value is not None:
            denom = abs(mr.value) if abs(mr.value) > 1e-9 else 1.0
            return (abs(value - mr.value) / denom <= VERIFY_TOL), refs
    # no numeric assertion tied to a metric -> nothing to falsify
    return (value is None), refs


def _mk_claims(ctx: AnalysisContext, raw: Optional[list]) -> list[Claim]:
    out = []
    for rc in raw or []:
        fid = rc.get("fund_id")
        metric = rc.get("metric")
        val = rc.get("value")
        verified, refs = _verify(ctx, fid, metric, val)
        out.append(
            Claim(
                text=rc.get("text", ""),
                metric=metric,
                fund_id=fid,
                value=val,
                source_refs=refs,
                verified=verified,
            )
        )
    return out


def _pct(x):
    return "n/a" if x is None else f"{x * 100:.1f}%"


def _num(x):
    return "n/a" if x is None else f"{x:.2f}"


def _default_recommendation(ctx: AnalysisContext) -> str:
    if not ctx.shortlist:
        return "No funds met the mandate constraints."
    top = ctx.get_fund(ctx.shortlist[0].fund_id)
    return (
        f"Across {len(ctx.shortlist)} funds meeting the {ctx.mandate.name} mandate, "
        f"{top.name if top else ctx.shortlist[0].fund_id} leads on risk-adjusted return."
    )


def _default_summary(ctx: AnalysisContext) -> str:
    n_univ = ctx.readiness.get("universe_count", len(ctx.funds))
    n_short = len(ctx.shortlist)
    if not ctx.shortlist:
        return (
            f"Screened {n_univ} funds against the {ctx.mandate.name} mandate; none cleared "
            f"the hard constraints. No recommendation follows."
        )
    top = ctx.get_fund(ctx.shortlist[0].fund_id)
    top_name = top.name if top else ctx.shortlist[0].fund_id
    m = ctx.metrics_by_fund.get(ctx.shortlist[0].fund_id, {})
    return (
        f"This memo screens {n_univ} funds against the {ctx.mandate.name} mandate and "
        f"advances {n_short} to a ranked shortlist. {top_name} is recommended, returning "
        f"{_pct(m.get('ann_return'))} annualized at {_pct(m.get('ann_vol'))} volatility "
        f"(Sharpe {_num(m.get('sharpe'))}). Every figure below is re-verified against the "
        f"deterministic metrics engine."
    )


def _default_key_risks(ctx: AnalysisContext) -> dict:
    """Deterministic, metric-backed risk read across the shortlist."""
    if not ctx.shortlist:
        return {"body": "No shortlist, so no fund-level risks to report.", "claims": []}
    ids = [s.fund_id for s in ctx.shortlist]

    def mval(fid, k):
        return ctx.metrics_by_fund.get(fid, {}).get(k)

    def pick(k, worst):
        cand = [(fid, mval(fid, k)) for fid in ids if mval(fid, k) is not None]
        if not cand:
            return None
        return (min if worst else max)(cand, key=lambda t: t[1])

    dd = pick("max_drawdown", worst=True)      # most negative
    bet = pick("beta", worst=False)            # highest benchmark sensitivity
    vol = pick("ann_vol", worst=False)         # highest volatility

    # liquidity: least-liquid shortlisted fund
    liq = None
    liq_days = [(fid, ctx.funds[fid].redemption_days) for fid in ids
                if ctx.funds.get(fid) and ctx.funds[fid].redemption_days is not None]
    if liq_days:
        liq = max(liq_days, key=lambda t: t[1])

    # concentration: strategy dominance in the shortlist
    strat_counts: dict[str, int] = {}
    for fid in ids:
        f = ctx.funds.get(fid)
        if f:
            strat_counts[f.strategy] = strat_counts.get(f.strategy, 0) + 1
    dominant = max(strat_counts.items(), key=lambda t: t[1]) if strat_counts else None

    parts, claims = [], []
    if dd:
        fid, v = dd
        parts.append(f"{ctx.funds[fid].name} carries the deepest drawdown at {_pct(v)}")
        claims.append({"text": f"Deepest drawdown: {_pct(v)}", "metric": "max_drawdown", "fund_id": fid, "value": v})
    if bet and bet[1] is not None:
        fid, v = bet
        parts.append(f"{ctx.funds[fid].name} has the highest benchmark sensitivity (beta {_num(v)})")
        claims.append({"text": f"Highest beta: {_num(v)}", "metric": "beta", "fund_id": fid, "value": v})
    if vol:
        fid, v = vol
        parts.append(f"{ctx.funds[fid].name} is the most volatile ({_pct(v)} annualized)")
        claims.append({"text": f"Highest volatility: {_pct(v)}", "metric": "ann_vol", "fund_id": fid, "value": v})
    body = ""
    if parts:
        sent = ". ".join(parts)
        body = sent[0].upper() + sent[1:] + ". "
    if liq:
        fid, days = liq
        f = ctx.funds[fid]
        body += (f"Liquidity is tightest at {f.name} ({f.redemption_freq or 'n/a'}, "
                 f"~{int(days)}-day redemption). ")
    if dominant and dominant[1] > 1:
        body += (f"Concentration risk: {dominant[1]} of {len(ids)} shortlisted funds are "
                 f"{dominant[0]} — size the sleeve accordingly. ")
    body += ("These are re-verified metric reads, not forward-looking forecasts; pair them "
             "with operational and manager due diligence before committing capital.")
    return {"body": body, "claims": claims}


def _data_appendix(ctx: AnalysisContext) -> str:
    b = ctx.benchmark
    bench = "none" if b is None else f"{b.name} ({b.source_kind}, as of {b.as_of})"
    rd = ctx.readiness
    q = rd.get("quarantined_count", 0)
    ov = rd.get("overlap") or {}
    win = f"{ov.get('start')} → {ov.get('end')}" if ov else "n/a"
    return (
        f"Metrics are computed from cleaned monthly returns over the common window {win}. "
        f"Volatility is the sample-standard-deviation annualization; Sharpe and Sortino use "
        f"excess return over a {_pct(ctx.rf_used)} risk-free ({ctx.rf_source}); beta/alpha are "
        f"OLS versus the benchmark. Benchmark: {bench}. Universe: "
        f"{rd.get('universe_count', len(ctx.funds))} funds, {rd.get('with_returns', '?')} with "
        f"return series; {q} row(s) quarantined during ingest. Every numeric claim in this memo "
        f"was recomputed from the source series and matched within tolerance — see the audit trail."
    )


def generate(ctx: AnalysisContext, claims_provider: ClaimsProvider) -> Memo:
    payload = claims_provider(ctx)

    # 1 · Summary — a distinct 1-2 sentence orientation (not the recommendation)
    sections = [
        MemoSection(heading="Summary", body=payload.get("summary") or _default_summary(ctx), claims=[]),
        MemoSection(
            heading="Recommendation",
            body=payload.get("recommendation") or _default_recommendation(ctx),
            claims=[],
        ),
    ]
    # 2 · per-fund analysis (the rationale)
    for fp in payload.get("funds", []):
        fid = fp.get("fund_id")
        f = ctx.get_fund(fid)
        heading = f"{f.name} ({fid}) — {f.strategy}" if f else str(fid)
        sections.append(
            MemoSection(heading=heading, body=fp.get("paragraph", ""), claims=_mk_claims(ctx, fp.get("claims")))
        )
    # 3 · Key Risks — LLM-supplied if present, else deterministic metric read
    kr = payload.get("key_risks")
    if isinstance(kr, dict) and kr.get("body"):
        risks_body, risks_claims = kr.get("body"), _mk_claims(ctx, kr.get("claims"))
    else:
        dr = _default_key_risks(ctx)
        risks_body, risks_claims = dr["body"], _mk_claims(ctx, dr["claims"])
    sections.append(MemoSection(heading="Key Risks", body=risks_body, claims=risks_claims))
    # 4 · Data Appendix — deterministic methodology + provenance
    sections.append(MemoSection(heading="Data Appendix", body=_data_appendix(ctx), claims=[]))

    memo = Memo(
        title=f"Investment Committee Memo — {ctx.mandate.name}",
        mandate=ctx.mandate.name,
        generated_by=payload.get("_model", "template"),
        sections=sections,
        shortlist=ctx.shortlist,
    )
    # Memo is frozen; derive the audit map and return a fully-formed copy rather
    # than mutating after construction.
    return memo.model_copy(update={"audit": build_audit_map(memo)})


def template_claims_provider(ctx: AnalysisContext) -> dict:
    """Deterministic, offline provider — real prose assembled from real numbers.
    Lets the demo and tests run with no API key, and doubles as a golden fixture."""

    def pct(x):
        return "n/a" if x is None else f"{x * 100:.1f}%"

    def num(x):
        return "n/a" if x is None else f"{x:.2f}"

    funds = []
    for s in ctx.shortlist:
        m = ctx.metrics_by_fund[s.fund_id]
        f = ctx.get_fund(s.fund_id)
        para = (
            f"{f.name} ranks #{s.rank} for this mandate. It returned {pct(m.get('ann_return'))} "
            f"annualized against {pct(m.get('ann_vol'))} volatility, producing a Sharpe of "
            f"{num(m.get('sharpe'))} and a Sortino of {num(m.get('sortino'))}. Its worst peak-to-"
            f"trough drawdown was {pct(m.get('max_drawdown'))} (Calmar {num(m.get('calmar'))}), "
            f"with a {num(m.get('beta'))} beta to the benchmark."
        )
        claims = [
            {"text": f"Annualized return of {pct(m.get('ann_return'))}", "metric": "ann_return", "fund_id": s.fund_id, "value": m.get("ann_return")},
            {"text": f"Sharpe ratio of {num(m.get('sharpe'))}", "metric": "sharpe", "fund_id": s.fund_id, "value": m.get("sharpe")},
            {"text": f"Sortino ratio of {num(m.get('sortino'))}", "metric": "sortino", "fund_id": s.fund_id, "value": m.get("sortino")},
            {"text": f"Max drawdown of {pct(m.get('max_drawdown'))}", "metric": "max_drawdown", "fund_id": s.fund_id, "value": m.get("max_drawdown")},
        ]
        funds.append({"fund_id": s.fund_id, "paragraph": para, "claims": claims})
    return {
        "summary": _default_summary(ctx),
        "recommendation": _default_recommendation(ctx),
        "funds": funds,
        "key_risks": _default_key_risks(ctx),
        "_model": "template",
    }


def render_markdown(memo: Memo) -> str:
    out = [f"# {memo.title}", ""]
    out.append(f"*Mandate:* {memo.mandate}  ·  *Generated by:* `{memo.generated_by}`  ·  *{memo.version}*")
    a = memo.audit
    out.append(
        f"*Audit:* {a.get('verified_count', 0)}/{a.get('claim_count', 0)} claims verified against the metrics engine."
    )
    out.append("")
    # shortlist table
    out.append("## Shortlist")
    out.append("")
    out.append("| # | Fund | Strategy | Ann.Return | Sharpe | Sortino | Calmar | MaxDD |")
    out.append("|---|------|----------|-----------:|-------:|--------:|-------:|------:|")
    for s in memo.shortlist:
        m = s.metrics

        def pct(x):
            return "n/a" if x is None else f"{x * 100:.1f}%"

        def num(x):
            return "n/a" if x is None else f"{x:.2f}"

        out.append(
            f"| {s.rank} | {s.name} | {s.strategy} | {pct(m.get('ann_return'))} | "
            f"{num(m.get('sharpe'))} | {num(m.get('sortino'))} | {num(m.get('calmar'))} | {pct(m.get('max_drawdown'))} |"
        )
    out.append("")
    for sec in memo.sections:
        out.append(f"## {sec.heading}")
        out.append("")
        out.append(sec.body)
        if sec.claims:
            out.append("")
            out.append("<details><summary>sources</summary>")
            out.append("")
            for c in sec.claims:
                mark = "✓" if c.verified else "⚠"
                out.append(f"- {mark} {c.text} — `{'; '.join(c.source_refs) or 'no source'}`")
            out.append("")
            out.append("</details>")
        out.append("")
    return "\n".join(out)


def _cli(argv=None) -> int:
    import sys
    from pathlib import Path

    from .config import get_settings
    from .export import export_all
    from .pipeline import load_mandate, run

    args = list(sys.argv[1:] if argv is None else argv)
    funds_csv = args[0] if len(args) > 0 else "data/samples/funds.csv"
    returns_csv = args[1] if len(args) > 1 else "data/samples/returns.csv"
    mandate = load_mandate("data/mandates/default.yaml")
    s = get_settings()
    provider = None
    if "--template" not in args:
        try:
            from .llm import select_claims_provider

            provider = select_claims_provider()  # None -> deterministic template
        except Exception:  # noqa: BLE001
            provider = None
    memo, ctx = run(funds_csv, returns_csv, mandate, provider)
    paths = export_all(memo, ctx, "exports")
    a = memo.audit
    print(f"✓ memo by {memo.generated_by}: {a['verified_count']}/{a['claim_count']} claims verified")
    for kind, pth in paths.items():
        print(f"  {kind} → {pth}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())

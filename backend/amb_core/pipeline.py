"""End-to-end orchestrator: validate/ingest -> metrics -> shortlist -> memo.

Deterministic through the shortlist; the memo step takes an injectable
claims_provider (LLM or template) so everything up to drafting is testable
without a network.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml

from .benchmarks import load_benchmark
from .ingest import load_funds, load_returns
from .memo import ClaimsProvider, generate, template_claims_provider
from .metrics import compute_for_fund
from .models import Mandate, Memo
from .retrieval import AnalysisContext
from .scoring import build_shortlist


def load_mandate(path: str | Path) -> Mandate:
    return Mandate(**yaml.safe_load(Path(path).read_text()))


def run(
    funds_csv: str | Path,
    returns_csv: str | Path,
    mandate: Mandate,
    claims_provider: Optional[ClaimsProvider] = None,
    data_dir: str | Path = "data",
) -> tuple[Memo, AnalysisContext]:
    funds = load_funds(funds_csv)
    series, quarantined = load_returns(returns_csv)
    try:
        benchmark = load_benchmark(mandate.benchmark_id, Path(data_dir) / "benchmarks")
    except FileNotFoundError:
        benchmark = None

    metrics_by_fund: dict[str, dict] = {}
    metric_results: dict[str, list] = {}
    for f in funds:
        s = series.get(f.fund_id)
        if s is None:
            continue
        vals, results = compute_for_fund(s, benchmark, mandate.risk_free_annual)
        metrics_by_fund[f.fund_id] = vals
        metric_results[f.fund_id] = results

    usable = [f for f in funds if f.fund_id in metrics_by_fund]
    shortlist = build_shortlist(usable, metrics_by_fund, mandate)
    ctx = AnalysisContext(funds, benchmark, metrics_by_fund, metric_results, shortlist, mandate, quarantined)
    memo = generate(ctx, claims_provider or template_claims_provider)
    return memo, ctx

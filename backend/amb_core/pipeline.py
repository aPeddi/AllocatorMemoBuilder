"""End-to-end orchestrator: validate/ingest -> metrics -> shortlist -> memo.

Deterministic through the shortlist; the memo step takes an injectable
claims_provider (LLM or template) so everything up to drafting is testable
without a network.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml

from .config import Settings, get_settings
from .ingest import load_funds, load_returns
from .marketdata import fetch_risk_free_annual, resolve_benchmark
from .memo import ClaimsProvider, generate, template_claims_provider
from .metrics import compute_for_fund
from .models import Mandate, Memo
from .readiness import build_readiness
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
    benchmark_mode: Optional[str] = None,
    settings: Optional[Settings] = None,
) -> tuple[Memo, AnalysisContext]:
    # composition root: read config ONCE here and inject the values downstream,
    # rather than have deep modules reach into a global settings singleton.
    settings = settings or get_settings()
    funds = load_funds(funds_csv)
    series, quarantined = load_returns(returns_csv)

    mode = benchmark_mode or settings.benchmark_mode
    fred_key = settings.fred_api_key
    benchmark = resolve_benchmark(mandate.benchmark_id, mode=mode, data_dir=data_dir, api_key=fred_key)

    # risk-free: mandate default, overridden by a live pull only in live/auto mode
    rf_used = mandate.risk_free_annual
    rf_source = "mandate"
    if mode in ("live", "auto"):
        live_rf = fetch_risk_free_annual(api_key=fred_key)
        if live_rf is not None:
            rf_used, rf_source = live_rf, "FRED · 3M T-bill"

    metrics_by_fund: dict[str, dict] = {}
    metric_results: dict[str, list] = {}
    for f in funds:
        s = series.get(f.fund_id)
        if s is None:
            continue
        vals, results = compute_for_fund(s, benchmark, rf_used)
        metrics_by_fund[f.fund_id] = vals
        metric_results[f.fund_id] = results

    usable = [f for f in funds if f.fund_id in metrics_by_fund]
    shortlist = build_shortlist(usable, metrics_by_fund, mandate)
    readiness = build_readiness(funds, series, benchmark, quarantined, rf_used, rf_source)
    ctx = AnalysisContext(
        funds=funds, benchmark=benchmark, metrics_by_fund=metrics_by_fund,
        metric_results=metric_results, shortlist=shortlist, mandate=mandate,
        quarantined=quarantined, series_by_fund=series,
        readiness=readiness, rf_used=rf_used, rf_source=rf_source,
    )
    memo = generate(ctx, claims_provider or template_claims_provider)
    return memo, ctx

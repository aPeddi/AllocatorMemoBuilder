"""End-to-end orchestrator: validate/ingest -> metrics -> shortlist -> memo.

Deterministic through the shortlist; the memo step takes an injectable
claims_provider (LLM or template) so everything up to drafting is testable
without a network.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

import yaml

from .config import Settings, get_settings
from .ingest import load_dataset, load_funds, load_returns
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
    dataset: str | Path,
    mandate: Mandate,
    claims_provider: Optional[ClaimsProvider] = None,
    data_dir: str | Path = "data",
    benchmark_mode: Optional[str] = None,
    settings: Optional[Settings] = None,
    on_step: Optional[Callable[[str], None]] = None,
    returns_csv: Optional[str | Path] = None,
) -> tuple[Memo, AnalysisContext]:
    # optional stage reporter so a caller (the CLI) can render live progress
    # without this module knowing anything about the terminal UI.
    step = on_step or (lambda _label: None)
    # composition root: read config ONCE here and inject the values downstream,
    # rather than have deep modules reach into a global settings singleton.
    settings = settings or get_settings()
    step("Ingesting dataset")
    # single combined file is canonical; a separate returns_csv keeps the legacy
    # two-file path working for callers that still have split exports.
    ingest_schema = None
    if returns_csv is None:
        funds, series, quarantined = load_dataset(dataset)
        _src_paths: tuple = (dataset,)
        try:
            from .ingest import dataset_schema
            ingest_schema = dataset_schema(dataset)
        except Exception:  # noqa: BLE001 — schema is UI sugar; never block the run
            ingest_schema = None
    else:
        funds = load_funds(dataset)
        series, quarantined = load_returns(returns_csv)
        _src_paths = (dataset, returns_csv)

    step("Resolving benchmark")
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

    step("Computing metrics")
    metrics_by_fund: dict[str, dict] = {}
    metric_results: dict[str, list] = {}
    for f in funds:
        s = series.get(f.fund_id)
        if s is None:
            continue
        vals, results = compute_for_fund(s, benchmark, rf_used)
        metrics_by_fund[f.fund_id] = vals
        metric_results[f.fund_id] = results

    step("Screening & scoring")
    usable = [f for f in funds if f.fund_id in metrics_by_fund]
    shortlist = build_shortlist(usable, metrics_by_fund, mandate)
    readiness = build_readiness(funds, series, benchmark, quarantined, rf_used, rf_source, ingest_schema)
    ctx = AnalysisContext(
        funds=funds, benchmark=benchmark, metrics_by_fund=metrics_by_fund,
        metric_results=metric_results, shortlist=shortlist, mandate=mandate,
        quarantined=quarantined, series_by_fund=series,
        readiness=readiness, rf_used=rf_used, rf_source=rf_source,
        sources=_read_sources(*_src_paths),
    )
    step("Drafting & verifying memo")
    memo = generate(ctx, claims_provider or template_claims_provider)
    return memo, ctx


def _read_sources(*paths: str | Path) -> list[dict]:
    """Capture the raw source CSV text so the memo can show/expose it as the
    single source of truth for its data (the in-app CSV panel)."""
    out: list[dict] = []
    for p in paths:
        try:
            pth = Path(p)
            text = pth.read_text(encoding="utf-8")
            data_rows = max(0, text.rstrip("\n").count("\n"))  # minus header
            out.append({"name": pth.name, "text": text, "rows": data_rows})
        except OSError:
            continue
    return out

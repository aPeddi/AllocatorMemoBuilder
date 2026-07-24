"""Deterministic, unit-tested metrics engine — the source of truth (ADR-0004).

All functions are pure and operate on aligned numpy arrays of *periodic* returns
(decimal fractions). The LLM never runs this code path; it only reports the
values these functions produce. Conventions are explicit and tested:

  * annualized return : geometric (CAGR) -> (prod(1+r))**(N/n) - 1
  * annualized vol    : sample stdev (ddof=1) * sqrt(N)
  * risk-free/period  : rf_annual / N   (simple), used for excess returns
  * Sharpe            : annualized_excess / annualized_vol
  * Sortino           : annualized_excess / annualized_downside_dev (MAR = rf/period)
  * max drawdown      : min of (wealth/running-peak - 1)   (<= 0)
  * Calmar            : annualized_return / |max drawdown|
  * beta/alpha        : OLS vs benchmark; alpha is annualized Jensen's alpha
"""
from __future__ import annotations

import math
from typing import Optional

import numpy as np

from .models import Benchmark, MetricResult, ReturnSeries

FORMULA_VERSION = "v1"

# stable metric keys, in report order
METRIC_KEYS = [
    "ann_return",
    "ann_vol",
    "sharpe",
    "sortino",
    "max_drawdown",
    "calmar",
    "downside_dev",
    "beta",
    "alpha",
    "correlation",
    "tracking_error",
    "hit_rate",
]


def _f(x) -> Optional[float]:
    if x is None:
        return None
    x = float(x)
    if math.isnan(x) or math.isinf(x):
        return None
    return x


def ann_return(r: np.ndarray, ppy: int) -> Optional[float]:
    n = len(r)
    if n == 0:
        return None
    growth = float(np.prod(1.0 + r))
    if growth <= 0:
        return _f(growth - 1.0)  # total wipeout / degenerate
    return _f(growth ** (ppy / n) - 1.0)


def ann_vol(r: np.ndarray, ppy: int) -> Optional[float]:
    if len(r) < 2:
        return None
    return _f(float(np.std(r, ddof=1)) * math.sqrt(ppy))


def wealth_curve(returns, round_to: Optional[int] = 4) -> list[float]:
    """Compounded growth-of-$1 curve from periodic returns."""
    out, c = [], 1.0
    for v in returns:
        c *= 1.0 + float(v)
        out.append(round(c, round_to) if round_to is not None else c)
    return out


def annualize(returns, ppy: int = 12):
    """(ann_return, ann_vol, wealth_curve) for a list of periodic returns.

    The one convenience wrapper the live-market proxy (serve.py) and the exporter
    both call, so annualization/vol/wealth is defined once, here, on the canonical
    engine — never re-implemented downstream.
    """
    vals = [float(v) for v in returns]
    if len(vals) < 2:
        return None, None, []
    arr = np.asarray(vals, dtype=float)
    return ann_return(arr, ppy), ann_vol(arr, ppy), wealth_curve(vals)


def sharpe(r: np.ndarray, ppy: int, rf_annual: float) -> Optional[float]:
    if len(r) < 2:
        return None
    rf_p = rf_annual / ppy
    vol = float(np.std(r, ddof=1)) * math.sqrt(ppy)
    if vol == 0:
        return None
    ann_excess = float(np.mean(r - rf_p)) * ppy
    return _f(ann_excess / vol)


def downside_dev(r: np.ndarray, ppy: int, mar_period: float) -> Optional[float]:
    if len(r) == 0:
        return None
    downside = np.minimum(r - mar_period, 0.0)
    dd = math.sqrt(float(np.mean(downside ** 2)))
    return _f(dd * math.sqrt(ppy))


def sortino(r: np.ndarray, ppy: int, rf_annual: float) -> Optional[float]:
    if len(r) < 2:
        return None
    rf_p = rf_annual / ppy
    dd = downside_dev(r, ppy, rf_p)
    if not dd:
        return None
    ann_excess = float(np.mean(r - rf_p)) * ppy
    return _f(ann_excess / dd)


def max_drawdown(r: np.ndarray) -> Optional[float]:
    if len(r) == 0:
        return None
    wealth = np.cumprod(1.0 + r)
    peak = np.maximum.accumulate(wealth)
    dd = wealth / peak - 1.0
    return _f(float(np.min(dd)))


def calmar(r: np.ndarray, ppy: int) -> Optional[float]:
    a = ann_return(r, ppy)
    mdd = max_drawdown(r)
    if a is None or mdd is None or mdd == 0:
        return None
    return _f(a / abs(mdd))


def beta(r: np.ndarray, b: np.ndarray) -> Optional[float]:
    if len(r) < 2 or len(r) != len(b):
        return None
    var_b = float(np.var(b, ddof=1))
    if var_b == 0:
        return None
    cov = float(np.cov(r, b, ddof=1)[0, 1])
    return _f(cov / var_b)


def alpha(r: np.ndarray, b: np.ndarray, ppy: int, rf_annual: float) -> Optional[float]:
    be = beta(r, b)
    ar = ann_return(r, ppy)
    ab = ann_return(b, ppy)
    if be is None or ar is None or ab is None:
        return None
    # Jensen's alpha, annualized
    return _f(ar - (rf_annual + be * (ab - rf_annual)))


def correlation(r: np.ndarray, b: np.ndarray) -> Optional[float]:
    if len(r) < 2 or len(r) != len(b):
        return None
    if np.std(r) == 0 or np.std(b) == 0:
        return None
    return _f(float(np.corrcoef(r, b)[0, 1]))


def tracking_error(r: np.ndarray, b: np.ndarray, ppy: int) -> Optional[float]:
    if len(r) < 2 or len(r) != len(b):
        return None
    return _f(float(np.std(r - b, ddof=1)) * math.sqrt(ppy))


def hit_rate(r: np.ndarray) -> Optional[float]:
    if len(r) == 0:
        return None
    return _f(float(np.mean(r > 0.0)))


def compute(
    fund_returns: np.ndarray,
    bench_returns: Optional[np.ndarray],
    ppy: int,
    rf_annual: float,
) -> dict[str, Optional[float]]:
    """Compute every metric on already-aligned arrays."""
    r = np.asarray(fund_returns, dtype=float)
    out: dict[str, Optional[float]] = {
        "ann_return": ann_return(r, ppy),
        "ann_vol": ann_vol(r, ppy),
        "sharpe": sharpe(r, ppy, rf_annual),
        "sortino": sortino(r, ppy, rf_annual),
        "max_drawdown": max_drawdown(r),
        "calmar": calmar(r, ppy),
        "downside_dev": downside_dev(r, ppy, rf_annual / ppy),
        "beta": None,
        "alpha": None,
        "correlation": None,
        "tracking_error": None,
        "hit_rate": hit_rate(r),
    }
    if bench_returns is not None and len(bench_returns) == len(r) and len(r) >= 2:
        b = np.asarray(bench_returns, dtype=float)
        out["beta"] = beta(r, b)
        out["alpha"] = alpha(r, b, ppy, rf_annual)
        out["correlation"] = correlation(r, b)
        out["tracking_error"] = tracking_error(r, b, ppy)
    return out


def _align(series: ReturnSeries, benchmark: Optional[Benchmark]):
    """Return (fund_arr, bench_arr|None) aligned on common periods."""
    fund_map = {p.period: p.value for p in series.points}
    if benchmark is None:
        periods = sorted(fund_map)
        return np.array([fund_map[p] for p in periods]), None
    bench_map = {p.period: p.value for p in benchmark.points}
    common = sorted(set(fund_map) & set(bench_map))
    if len(common) < 2:  # not enough overlap for relative metrics
        periods = sorted(fund_map)
        return np.array([fund_map[p] for p in periods]), None
    return (
        np.array([fund_map[p] for p in common]),
        np.array([bench_map[p] for p in common]),
    )


def compute_for_fund(
    series: ReturnSeries,
    benchmark: Optional[Benchmark],
    rf_annual: float,
) -> tuple[dict[str, Optional[float]], list[MetricResult]]:
    """Metrics dict + provenance-carrying MetricResult list for one fund."""
    r, b = _align(series, benchmark)
    values = compute(r, b, series.periods_per_year, rf_annual)
    bench_ref = f"|bench:{benchmark.benchmark_id}@{benchmark.as_of}" if benchmark else ""
    inputs_ref = f"returns:{series.source_hash}{bench_ref}"
    results = [
        MetricResult(
            fund_id=series.fund_id,
            metric=k,
            value=values[k],
            formula_id=f"{k}.{FORMULA_VERSION}",
            inputs_ref=inputs_ref,
        )
        for k in METRIC_KEYS
    ]
    return values, results


def _cli(argv=None) -> int:
    import sys
    from pathlib import Path

    from .ingest import load_funds, load_returns
    from .marketdata import load_snapshot

    args = list(sys.argv[1:] if argv is None else argv)
    funds_csv = args[0] if len(args) > 0 else "data/samples/funds.csv"
    returns_csv = args[1] if len(args) > 1 else "data/samples/returns.csv"
    funds = load_funds(funds_csv)
    series, _ = load_returns(returns_csv)
    bench = load_snapshot("SP500", Path("data/benchmarks"))
    print(f"  {'fund':<10} {'ret':>8} {'vol':>8} {'sharpe':>7} {'sortino':>7} {'calmar':>7} {'maxDD':>8} {'beta':>6}")
    for f in funds:
        s = series.get(f.fund_id)
        if s is None:
            continue
        vals, _ = compute_for_fund(s, bench, 0.02)

        def p(x):
            return "n/a" if x is None else f"{x * 100:6.1f}%"

        def n(x):
            return "n/a" if x is None else f"{x:6.2f}"

        print(
            f"  {f.fund_id:<10} {p(vals['ann_return'])} {p(vals['ann_vol'])} {n(vals['sharpe'])} "
            f"{n(vals['sortino'])} {n(vals['calmar'])} {p(vals['max_drawdown'])} {n(vals['beta'])}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())

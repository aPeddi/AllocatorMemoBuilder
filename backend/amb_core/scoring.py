"""Mandate-aware filtering + scoring -> ranked shortlist.

Deterministic: constraints hard-filter the universe, then eligible funds are
z-scored per metric (signed by whether higher or lower is better), weighted, and
summed. No LLM involved.
"""
from __future__ import annotations

import statistics
from typing import Optional

from .models import Fund, Mandate, ShortlistEntry

# +1 higher-is-better, -1 lower-is-better, 0 neutral (not scored directionally).
# max_drawdown is stored as <= 0, so "closer to zero" = larger = better -> +1.
DIRECTION = {
    "ann_return": 1,
    "sharpe": 1,
    "sortino": 1,
    "calmar": 1,
    "alpha": 1,
    "hit_rate": 1,
    "max_drawdown": 1,
    "ann_vol": -1,
    "downside_dev": -1,
    "tracking_error": -1,
    "beta": 0,
    "correlation": 0,
}

DEFAULT_WEIGHTS = {
    "sharpe": 0.30,
    "sortino": 0.20,
    "calmar": 0.15,
    "ann_return": 0.15,
    "max_drawdown": 0.10,
    "ann_vol": 0.10,
}


def _resolve(fund: Fund, metrics: dict[str, Optional[float]], field: str):
    if hasattr(fund, field):
        return getattr(fund, field)
    return metrics.get(field)


def _test(val, op: str, target) -> bool:
    if val is None:
        return op in {"!=", "not_in"}  # unknown fails positive constraints
    try:
        if op == ">=":
            return val >= target
        if op == "<=":
            return val <= target
        if op == ">":
            return val > target
        if op == "<":
            return val < target
        if op == "==":
            return val == target
        if op == "!=":
            return val != target
        if op == "in":
            return val in target
        if op == "not_in":
            return val not in target
    except TypeError:
        return False
    return False


def apply_constraints(
    funds: list[Fund], metrics_by_fund: dict[str, dict], mandate: Mandate
) -> list[str]:
    eligible = []
    for f in funds:
        m = metrics_by_fund.get(f.fund_id, {})
        if all(_test(_resolve(f, m, c.field), c.op, c.value) for c in mandate.constraints):
            eligible.append(f.fund_id)
    return eligible


def build_shortlist(
    funds: list[Fund], metrics_by_fund: dict[str, dict], mandate: Mandate
) -> list[ShortlistEntry]:
    by_id = {f.fund_id: f for f in funds}
    eligible = apply_constraints(funds, metrics_by_fund, mandate)
    weights = mandate.weights or DEFAULT_WEIGHTS

    # per-metric mean/stdev across the eligible universe
    stats: dict[str, tuple[float, float]] = {}
    for k in weights:
        vals = [metrics_by_fund[fid].get(k) for fid in eligible]
        present = [v for v in vals if v is not None]
        if len(present) >= 2:
            mu = statistics.fmean(present)
            sd = statistics.pstdev(present)
            stats[k] = (mu, sd)

    scores: dict[str, float] = {}
    for fid in eligible:
        s = 0.0
        for k, w in weights.items():
            v = metrics_by_fund[fid].get(k)
            if v is None or k not in stats:
                continue
            mu, sd = stats[k]
            if sd == 0:
                continue
            z = (v - mu) / sd
            s += w * z * DIRECTION.get(k, 0)
        scores[fid] = s

    ranked = sorted(eligible, key=lambda fid: scores.get(fid, 0.0), reverse=True)
    ranked = ranked[: mandate.top_n]

    shortlist = []
    for i, fid in enumerate(ranked, start=1):
        f = by_id[fid]
        m = metrics_by_fund[fid]
        shortlist.append(
            ShortlistEntry(
                rank=i,
                fund_id=fid,
                name=f.name,
                strategy=f.strategy,
                score=round(scores.get(fid, 0.0), 4),
                metrics={k: m.get(k) for k in ["ann_return", "sharpe", "sortino", "calmar", "max_drawdown", "ann_vol"]},
            )
        )
    return shortlist

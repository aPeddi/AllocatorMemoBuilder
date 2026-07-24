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


def resolve_field(fund: Fund, metrics: dict[str, Optional[float]], field: str):
    """A constraint field names either a Fund attribute or a metric — resolve it."""
    if hasattr(fund, field):
        return getattr(fund, field)
    return metrics.get(field)


def test_constraint(val, op: str, target) -> bool:
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


# backwards-compatible private aliases (kept so nothing importing the old names breaks)
_resolve = resolve_field
_test = test_constraint


def resolve_weights(mandate: Optional[Mandate]) -> dict[str, float]:
    """The scoring weights actually in force — the mandate's, else the house default."""
    return (mandate.weights if (mandate and mandate.weights) else DEFAULT_WEIGHTS)


def eligible_stats(
    eligible_ids, metrics_by_fund: dict[str, dict], weights: dict[str, float]
) -> dict[str, tuple[float, float]]:
    """Per-metric (mean, population-stdev) across the eligible set — the z-score basis.

    This is the ONE definition of the scoring basis; both build_shortlist (ranking)
    and the exporter (the on-screen weighing bars) read it, so the bar a fund shows
    is provably the score it was ranked on.
    """
    stats: dict[str, tuple[float, float]] = {}
    for k in weights:
        present = [metrics_by_fund[fid].get(k) for fid in eligible_ids
                   if metrics_by_fund.get(fid, {}).get(k) is not None]
        if len(present) >= 2:
            stats[k] = (statistics.fmean(present), statistics.pstdev(present))
    return stats


def score_components(
    fid: str, metrics_by_fund: dict[str, dict], weights: dict[str, float],
    stats: dict[str, tuple[float, float]], round_to: int = 3,
) -> list[dict]:
    """Signed, weighted z contribution of each metric to a fund's score."""
    out = []
    m = metrics_by_fund.get(fid, {})
    for k, w in weights.items():
        v = m.get(k)
        if v is None or k not in stats:
            continue
        mu, sd = stats[k]
        if sd == 0:
            continue
        out.append({"k": k, "c": round(w * ((v - mu) / sd) * DIRECTION.get(k, 0), round_to)})
    return out


def apply_constraints(
    funds: list[Fund], metrics_by_fund: dict[str, dict], mandate: Mandate
) -> list[str]:
    eligible = []
    for f in funds:
        m = metrics_by_fund.get(f.fund_id, {})
        if all(test_constraint(resolve_field(f, m, c.field), c.op, c.value) for c in mandate.constraints):
            eligible.append(f.fund_id)
    return eligible


def build_shortlist(
    funds: list[Fund], metrics_by_fund: dict[str, dict], mandate: Mandate
) -> list[ShortlistEntry]:
    by_id = {f.fund_id: f for f in funds}
    eligible = apply_constraints(funds, metrics_by_fund, mandate)
    weights = resolve_weights(mandate)
    stats = eligible_stats(eligible, metrics_by_fund, weights)

    # ranking score: sum of the *unrounded* weighted-z contributions
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
            s += w * ((v - mu) / sd) * DIRECTION.get(k, 0)
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
                components=score_components(fid, metrics_by_fund, weights, stats),
            )
        )
    return shortlist

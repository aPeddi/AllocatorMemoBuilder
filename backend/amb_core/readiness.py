"""Data-readiness reporting (ADR-0010).

Turns the messy-CSV cleanup into an auditable, on-screen story: how many rows
were read, what was quarantined and why, which fund identifiers reconciled
between the universe file and the returns file, each fund's date coverage, the
common overlap window, and the benchmark + risk-free provenance. The export
surfaces this as the 'Act 0 · Data' stage.
"""
from __future__ import annotations

from collections import Counter
from typing import Optional


def _reason_bucket(reason: str) -> str:
    r = (reason or "").lower()
    if "date" in r:
        return "bad date"
    if "fund" in r or "id" in r:
        return "missing id"
    if "return" in r or "value" in r:
        return "unparseable return"
    return "other"


def build_readiness(funds, series_by_fund, benchmark, quarantined, rf_used, rf_source) -> dict:
    fund_ids = [f.fund_id for f in funds]
    fund_id_set = set(fund_ids)
    series_ids = set(series_by_fund.keys())

    # identifier reconciliation, both directions
    in_universe_no_returns = sorted(fund_id_set - series_ids)     # listed but no return series
    returns_no_metadata = sorted(series_ids - fund_id_set)        # returns for an unknown fund
    matched = sorted(fund_id_set & series_ids)

    # per-fund coverage + overlap window
    coverage = []
    starts, ends = [], []
    for fid in sorted(series_ids):
        s = series_by_fund[fid]
        pts = s.points
        if not pts:
            continue
        d0, d1 = pts[0].period, pts[-1].period
        starts.append(d0)
        ends.append(d1)
        coverage.append({
            "fund_id": fid,
            "start": d0.isoformat(),
            "end": d1.isoformat(),
            "n": len(pts),
            "frequency": s.frequency,
        })
    overlap = None
    if starts and ends:
        lo, hi = max(starts), min(ends)
        overlap = {"start": lo.isoformat(), "end": hi.isoformat(), "aligned": lo <= hi}

    # date-range consistency: do all funds share one window?
    distinct_windows = {(c["start"], c["end"]) for c in coverage}
    date_ranges_consistent = len(distinct_windows) <= 1

    q_reasons = Counter(_reason_bucket(q.get("reason", "")) for q in (quarantined or []))

    bench_block = None
    if benchmark is not None:
        bench_block = {
            "id": benchmark.benchmark_id,
            "name": benchmark.name,
            "source_kind": benchmark.source_kind,
            "source_name": benchmark.source_name,
            "as_of": benchmark.as_of.isoformat(),
            "n": len(benchmark.points),
            "fetched_at": benchmark.fetched_at.isoformat() if benchmark.fetched_at else None,
        }

    return {
        "universe_count": len(fund_ids),
        "with_returns": len(matched),
        "missing_returns": in_universe_no_returns,       # ID mismatch: universe -> returns
        "orphan_returns": returns_no_metadata,           # ID mismatch: returns -> universe
        "quarantined_count": len(quarantined or []),
        "quarantine_reasons": dict(q_reasons),
        "coverage": coverage,
        "overlap": overlap,
        "date_ranges_consistent": date_ranges_consistent,
        "benchmark": bench_block,
        "risk_free": {"value": rf_used, "source": rf_source},
    }

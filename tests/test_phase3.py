"""Phase 3 — live market data, liquidity screening, readiness, memo structure."""
import io

import pytest

from amb_core import marketdata
from amb_core.ingest import redemption_to_days
from amb_core.marketdata import fetch_benchmark, resolve_benchmark


# ── liquidity ordinal ───────────────────────────────────────────────────────
def test_redemption_ordinal_monotone():
    daily = redemption_to_days("Daily", 0, 5)
    monthly = redemption_to_days("Monthly", 12, 30)
    quarterly = redemption_to_days("Quarterly", 24, 60)
    annual = redemption_to_days("Annual", 36, 90)
    assert daily < monthly < quarterly < annual
    assert redemption_to_days(None) is None
    # lockup does not distort steady-state redemption (kept as a separate term)
    assert redemption_to_days("Monthly", 0, 30) == redemption_to_days("Monthly", 24, 30)


# ── benchmark resolution + graceful fallback ────────────────────────────────
def test_snapshot_mode_is_offline_and_stamped():
    b = resolve_benchmark("SP500", mode="snapshot", data_dir="data")
    assert b is not None and b.source_kind == "snapshot"
    assert len(b.points) >= 12 and b.periods_per_year == 12


def test_live_falls_back_when_source_unreachable(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("no network")
    monkeypatch.setattr(marketdata, "_read_fred", boom)
    b = resolve_benchmark("SP500", mode="live", data_dir="data")
    # no cache in a clean tree -> snapshot, never an exception, never a hang
    assert b is not None and b.source_kind in ("cache", "snapshot")


# ── live parsing path, network-free (fixture stands in for FRED) ────────────
_FRED_CSV = "observation_date,SP500\n" + "\n".join(
    f"2024-{m:02d}-01,{100 + m}" for m in range(1, 13)
) + "\n" + "\n".join(f"2025-{m:02d}-15,{112 + m}" for m in range(1, 4))


def test_fetch_benchmark_parses_and_resamples(monkeypatch):
    import pandas as pd

    def fake_read(series_id, timeout=12.0):
        df = pd.read_csv(io.StringIO(_FRED_CSV))
        df.columns = ["date", "value"]
        df["date"] = pd.to_datetime(df["date"])
        return df

    monkeypatch.setattr(marketdata, "_read_fred", fake_read)
    b = fetch_benchmark("SP500")
    assert b.source_kind == "live" and b.source_name == "FRED"
    assert b.frequency == "monthly" and len(b.points) >= 12
    # first monthly return = 102/101 - 1
    assert b.points[0].value == pytest.approx(102 / 101 - 1, rel=1e-6)


def test_unknown_benchmark_has_no_live_mapping(monkeypatch):
    monkeypatch.setattr(marketdata, "_read_fred", lambda *a, **k: None)
    with pytest.raises(ValueError):
        fetch_benchmark("NOT_A_REAL_INDEX")


# ── readiness report ────────────────────────────────────────────────────────
def test_readiness_reconciles_and_reports(sample_run):
    _memo, ctx = sample_run
    r = ctx.readiness
    assert r["universe_count"] == 9
    assert r["with_returns"] >= 5
    assert r["overlap"] and r["overlap"]["aligned"] is True
    assert r["benchmark"] and r["benchmark"]["source_kind"] == "snapshot"
    assert r["quarantined_count"] >= 0


# ── liquidity actually screens ──────────────────────────────────────────────
def test_illiquid_funds_carry_terms(sample_run):
    _memo, ctx = sample_run
    ven = ctx.get_fund("VEN")
    assert ven.redemption_freq == "Illiquid" and ven.redemption_days is not None
    da = ctx.get_fund("DA")
    assert da.redemption_freq == "Daily"
    # shortlisted funds all clear the 200-day liquidity screen
    for s in ctx.shortlist:
        assert ctx.get_fund(s.fund_id).redemption_days <= 200


# ── memo structure ──────────────────────────────────────────────────────────
def test_memo_has_summary_risks_appendix(sample_run):
    memo, _ctx = sample_run
    headings = [s.heading for s in memo.sections]
    assert headings[0] == "Summary"
    assert "Recommendation" in headings
    assert "Key Risks" in headings
    assert headings[-1] == "Data Appendix"


def test_key_risks_claims_verify(sample_run):
    memo, _ctx = sample_run
    kr = next(s for s in memo.sections if s.heading == "Key Risks")
    assert kr.claims and all(c.verified for c in kr.claims)


def test_net_return_reflects_fee(sample_run):
    _memo, ctx = sample_run
    fid = ctx.shortlist[0].fund_id
    gross = ctx.metric_value(fid, "ann_return")
    net = ctx.net_return(fid)
    fee = ctx.get_fund(fid).mgmt_fee_pct
    if gross is not None and fee is not None:
        assert net == pytest.approx(gross - fee / 100.0, abs=1e-6)

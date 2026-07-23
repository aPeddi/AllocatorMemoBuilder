"""CSV ingestion + normalization.

Auto-detects columns, coerces messy return values, infers frequency, hashes the
cleaned series for provenance, and quarantines (never silently drops) bad rows.
"""
from __future__ import annotations

import math
import re
from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd

from .audit import content_hash
from .models import Fund, ReturnPoint, ReturnSeries

_NA = {"", "na", "nan", "n/a", "null", "none", "-", "--"}


def normalize_return(raw) -> Optional[float]:
    """Coerce a return cell to a decimal fraction (0.023 == 2.3%).

    Handles '%', thousands commas, European stray spaces, and bare percent
    points (a value like 2.3 with |v|>1.5 is read as 2.3%, not 230%).
    """
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        v = float(raw)
        if math.isnan(v) or math.isinf(v):
            return None
        pct = False
    else:
        s = str(raw).strip()
        if s.lower() in _NA:
            return None
        pct = "%" in s
        s = s.replace("%", "").replace(",", "").replace(" ", "")
        try:
            v = float(s)
        except ValueError:
            return None
    if pct:
        return v / 100.0
    # bare number: monthly returns don't exceed ~150%, so |v|>1.5 means percent points
    return v / 100.0 if abs(v) > 1.5 else v


def _parse_date(raw) -> Optional[date]:
    try:
        ts = pd.to_datetime(raw, errors="coerce")
        return None if pd.isna(ts) else ts.date()
    except Exception:
        return None


def _find_col(columns: list[str], candidates: list[str]) -> Optional[str]:
    lower = {c.lower().strip(): c for c in columns}
    for cand in candidates:
        if cand in lower:
            return lower[cand]
    # substring fallback
    for key, orig in lower.items():
        if any(cand in key for cand in candidates):
            return orig
    return None


def infer_frequency(dates: list[date]) -> tuple[str, int]:
    if len(dates) < 2:
        return ("monthly", 12)
    ds = sorted(dates)
    diffs = [(ds[i + 1] - ds[i]).days for i in range(len(ds) - 1)]
    med = sorted(diffs)[len(diffs) // 2]
    if med <= 3:
        return ("daily", 252)
    if med <= 45:
        return ("monthly", 12)
    if med <= 135:
        return ("quarterly", 4)
    return ("annual", 1)


def load_returns(path: str | Path) -> tuple[dict[str, ReturnSeries], list[dict]]:
    df = pd.read_csv(path)
    cols = list(df.columns)
    date_col = _find_col(cols, ["date", "period", "month", "asof", "as_of"])
    fund_col = _find_col(cols, ["fund_id", "fund", "ticker", "symbol", "id"])
    ret_col = _find_col(cols, ["return", "monthly_return", "ret", "performance", "value"])
    if not (date_col and fund_col and ret_col):
        raise ValueError(
            f"returns CSV needs date/fund/return columns; detected "
            f"date={date_col}, fund={fund_col}, return={ret_col} from {cols}"
        )

    rows: list[tuple[str, date, float]] = []
    quarantined: list[dict] = []
    for i, r in df.iterrows():
        d = _parse_date(r[date_col])
        f = str(r[fund_col]).strip()
        v = normalize_return(r[ret_col])
        if d is None or v is None or f == "" or f.lower() == "nan":
            quarantined.append(
                {"row": int(i), "reason": "unparseable date/fund/return", "raw": dict(r)}
            )
            continue
        rows.append((f, d, v))

    by_fund: dict[str, ReturnSeries] = {}
    for f in sorted({x[0] for x in rows}):
        pts = sorted([(d, v) for (ff, d, v) in rows if ff == f])
        freq, ppy = infer_frequency([d for d, _ in pts])
        by_fund[f] = ReturnSeries(
            fund_id=f,
            frequency=freq,
            periods_per_year=ppy,
            points=[ReturnPoint(period=d, value=v) for d, v in pts],
            source_hash=content_hash([v for _, v in pts]),
        )
    return by_fund, quarantined


# named redemption frequency -> days-to-liquidity ordinal (for screening/sorting)
_REDEMPTION_DAYS = {
    "daily": 1, "weekly": 7, "biweekly": 14, "semi-monthly": 15,
    "monthly": 30, "bi-monthly": 60, "quarterly": 90, "semi-annual": 180,
    "semiannual": 180, "annual": 365, "annually": 365, "yearly": 365,
    "biennial": 730, "illiquid": 3650, "locked": 3650, "closed": 3650,
}


def redemption_to_days(freq: Optional[str], lockup_months: Optional[float] = None,
                       notice_days: Optional[float] = None) -> Optional[float]:
    """Steady-state days-to-liquidity = redemption cadence + notice period.
    A monotone ordinal so a mandate can screen 'liquid within N days'. Lockup is
    kept as a separate term (a one-time gate at entry), not folded in here."""
    if freq is None:
        return None
    base = _REDEMPTION_DAYS.get(str(freq).strip().lower())
    if base is None:
        return None
    return round(float(base) + float(notice_days or 0), 1)


def load_funds(path: str | Path) -> list[Fund]:
    df = pd.read_csv(path)
    cols = list(df.columns)
    c_id = _find_col(cols, ["fund_id", "fund", "id", "ticker", "symbol"])
    c_name = _find_col(cols, ["name", "fund_name"])
    c_strat = _find_col(cols, ["strategy", "style", "asset_class", "category"])
    c_aum = _find_col(cols, ["aum_mm", "aum", "assets"])
    c_inc = _find_col(cols, ["inception", "inception_date", "since"])
    c_fee = _find_col(cols, ["mgmt_fee_pct", "fee", "management_fee", "expense"])
    c_notes = _find_col(cols, ["notes", "note", "comment", "description"])
    c_redf = _find_col(cols, ["redemption_freq", "redemption", "liquidity", "liquidity_terms", "dealing"])
    c_lock = _find_col(cols, ["lockup_months", "lockup", "lock_up", "lock"])
    c_notice = _find_col(cols, ["notice_days", "notice", "notice_period"])
    if not c_id:
        raise ValueError(f"funds CSV needs a fund id column; got {cols}")

    funds: list[Fund] = []
    for i, r in df.iterrows():
        def g(c):
            return None if (c is None or pd.isna(r[c])) else r[c]

        def gf(c):
            v = g(c)
            try:
                return float(v) if v is not None else None
            except (TypeError, ValueError):
                return None

        fee = g(c_fee)
        aum = g(c_aum)
        inc = _parse_date(g(c_inc)) if c_inc else None
        redf = (str(g(c_redf)).strip() if g(c_redf) is not None else None)
        lock = gf(c_lock)
        notice = gf(c_notice)
        funds.append(
            Fund(
                fund_id=str(r[c_id]).strip(),
                name=str(g(c_name) or r[c_id]).strip(),
                strategy=str(g(c_strat) or "Unclassified").strip(),
                aum_mm=float(aum) if aum is not None else None,
                inception=inc,
                mgmt_fee_pct=float(fee) if fee is not None else None,
                notes=(str(g(c_notes)) if g(c_notes) is not None else None),
                redemption_freq=redf,
                lockup_months=lock,
                notice_days=notice,
                redemption_days=redemption_to_days(redf, lock, notice),
                source_ref=f"funds.csv:row={int(i)}",
            )
        )
    return funds


def _cli(argv=None) -> int:
    import sys

    args = list(sys.argv[1:] if argv is None else argv)
    path = args[0] if args else "data/samples/returns.csv"
    series, quarantined = load_returns(path)
    print(f"funds: {len(series)}  quarantined rows: {len(quarantined)}")
    for fid, s in series.items():
        print(f"  {fid:<10} {s.frequency:<9} n={len(s.points):<4} hash={s.source_hash}")
    for q in quarantined[:5]:
        print(f"  ! row {q['row']}: {q['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())

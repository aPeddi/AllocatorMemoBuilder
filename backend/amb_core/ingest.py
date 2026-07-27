"""CSV ingestion + normalization.

Auto-detects columns, coerces messy return values, infers frequency, hashes the
cleaned series for provenance, and quarantines (never silently drops) bad rows.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd

from .audit import content_hash
from .coercion import normalize_return, parse_date
from .models import Fund, ReturnPoint, ReturnSeries

# re-exported for backwards compatibility with callers that imported the old private name
_parse_date = parse_date


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


# fund-metadata column synonyms — one source, shared by load_funds and load_dataset
_FUND_COLS = {
    "id": ["fund_id", "fund", "id", "ticker", "symbol"],
    "name": ["name", "fund_name"],
    "strategy": ["strategy", "style", "asset_class", "category"],
    "aum": ["aum_mm", "aum", "assets"],
    "inc": ["inception", "inception_date", "since"],
    "fee": ["mgmt_fee_pct", "fee", "management_fee", "expense"],
    "notes": ["notes", "note", "comment", "description"],
    "redf": ["redemption_freq", "redemption", "liquidity", "liquidity_terms", "dealing"],
    "lock": ["lockup_months", "lockup", "lock_up", "lock"],
    "notice": ["notice_days", "notice", "notice_period"],
}


def _fund_colmap(cols: list[str]) -> dict[str, Optional[str]]:
    return {role: _find_col(cols, cands) for role, cands in _FUND_COLS.items()}


def _fund_from_row(r, cm: dict[str, Optional[str]], source_ref: str) -> Fund:
    def g(role: str):
        c = cm.get(role)
        return None if (c is None or pd.isna(r[c])) else r[c]

    def gf(role: str) -> Optional[float]:
        v = g(role)
        try:
            return float(v) if v is not None else None
        except (TypeError, ValueError):
            return None

    idv = g("id")
    redf = (str(g("redf")).strip() if g("redf") is not None else None)
    lock, notice = gf("lock"), gf("notice")
    fee, aum = g("fee"), g("aum")
    inc = _parse_date(g("inc")) if cm.get("inc") else None
    return Fund(
        fund_id=str(idv).strip(),
        name=str(g("name") or idv).strip(),
        strategy=str(g("strategy") or "Unclassified").strip(),
        aum_mm=float(aum) if aum is not None else None,
        inception=inc,
        mgmt_fee_pct=float(fee) if fee is not None else None,
        notes=(str(g("notes")) if g("notes") is not None else None),
        redemption_freq=redf,
        lockup_months=lock,
        notice_days=notice,
        redemption_days=redemption_to_days(redf, lock, notice),
        source_ref=source_ref,
    )


def load_funds(path: str | Path) -> list[Fund]:
    df = pd.read_csv(path)
    cm = _fund_colmap(list(df.columns))
    if cm["id"] is None:
        raise ValueError(f"funds CSV needs a fund id column; got {list(df.columns)}")
    return [_fund_from_row(r, cm, f"funds.csv:row={int(i)}") for i, r in df.iterrows()]


def load_dataset(path: str | Path) -> tuple[list[Fund], dict[str, ReturnSeries], list[dict]]:
    """One combined CSV → (funds, return-series, quarantined). The single-file
    canonical input: a long file with date/fund/return columns plus optional
    per-fund metadata columns (name, strategy, fee, liquidity terms …). Metadata is
    read from the first row seen per fund; returns are parsed and quarantined exactly
    as the two-file path does, so a merged sample reproduces it identically."""
    df = pd.read_csv(path)
    cols = list(df.columns)
    date_col = _find_col(cols, ["date", "period", "month", "asof", "as_of"])
    fund_col = _find_col(cols, ["fund_id", "fund", "ticker", "symbol", "id"])
    ret_col = _find_col(cols, ["monthly_return", "return", "ret", "performance", "value"])
    if not (date_col and fund_col and ret_col):
        raise ValueError(
            f"dataset CSV needs date/fund/return columns; detected "
            f"date={date_col}, fund={fund_col}, return={ret_col} from {cols}"
        )
    cm = _fund_colmap(cols)
    name = Path(path).name

    funds: list[Fund] = []
    seen: set[str] = set()
    for i, r in df.iterrows():
        fid = str(r[fund_col]).strip()
        if not fid or fid.lower() == "nan" or fid in seen:
            continue
        seen.add(fid)
        funds.append(_fund_from_row(r, cm, f"{name}:row={int(i)}"))

    rows: list[tuple[str, date, float]] = []
    quarantined: list[dict] = []
    for i, r in df.iterrows():
        d = _parse_date(r[date_col])
        f = str(r[fund_col]).strip()
        v = normalize_return(r[ret_col])
        if d is None or v is None or f == "" or f.lower() == "nan":
            quarantined.append({"row": int(i), "reason": "unparseable date/fund/return", "raw": dict(r)})
            continue
        rows.append((f, d, v))

    by_fund: dict[str, ReturnSeries] = {}
    for f in sorted({x[0] for x in rows}):
        pts = sorted([(d, v) for (ff, d, v) in rows if ff == f])
        freq, ppy = infer_frequency([d for d, _ in pts])
        by_fund[f] = ReturnSeries(
            fund_id=f, frequency=freq, periods_per_year=ppy,
            points=[ReturnPoint(period=d, value=v) for d, v in pts],
            source_hash=content_hash([v for _, v in pts]),
        )
    return funds, by_fund, quarantined


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

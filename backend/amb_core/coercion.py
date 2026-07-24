"""Shared CSV-cell coercion helpers.

These parse messy human/spreadsheet values (returns, dates) into clean typed
values. They are genuinely shared infrastructure — ``ingest`` (fund/return
CSVs), ``benchmarks`` and ``marketdata`` (index snapshots/FRED CSVs) all read
the same kinds of cells — so they live here with a stable public API instead of
being reached into as private ``ingest._parse_date`` across module boundaries.
"""
from __future__ import annotations

import math
from datetime import date
from typing import Any, Optional

import pandas as pd

# tokens that mean "no value" in a spreadsheet cell
_NA = {"", "na", "nan", "n/a", "null", "none", "-", "--"}


def normalize_return(raw: Any) -> Optional[float]:
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


def parse_date(raw: Any) -> Optional[date]:
    """Parse any spreadsheet date cell to a ``date``; None if unparseable."""
    try:
        ts = pd.to_datetime(raw, errors="coerce")
        return None if pd.isna(ts) else ts.date()
    except Exception:
        return None

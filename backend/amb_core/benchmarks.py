"""Benchmark + risk-free loading. Snapshot mode (default) reads committed
as-of fixtures so every memo is reproducible (ADR-0005)."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from .coercion import normalize_return, parse_date
from .models import Benchmark, ReturnPoint

_NAMES = {"sp500": "S&P 500 Total Return", "agg": "US Aggregate Bond"}


def load_benchmark(benchmark_id: str = "SP500", data_dir: str | Path = "data/benchmarks") -> Benchmark:
    path = Path(data_dir) / f"{benchmark_id.lower()}_monthly.csv"
    if not path.exists():
        raise FileNotFoundError(f"benchmark snapshot not found: {path}")
    df = pd.read_csv(path)
    pts = []
    for _, r in df.iterrows():
        d = parse_date(r["date"])
        v = normalize_return(r["return"])
        if d is not None and v is not None:
            pts.append(ReturnPoint(period=d, value=v))
    pts.sort(key=lambda p: p.period)
    as_of = pts[-1].period if pts else date(2000, 1, 1)
    return Benchmark(
        benchmark_id=benchmark_id.upper(),
        name=_NAMES.get(benchmark_id.lower(), benchmark_id.upper()),
        as_of=as_of,
        frequency="monthly",
        periods_per_year=12,
        points=pts,
        source=str(path),
    )

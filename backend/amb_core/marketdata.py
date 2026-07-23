"""Live market-data access (ADR-0009).

Pulls a benchmark index and the risk-free rate from FRED's public CSV endpoints
(no API key), resamples to first-of-month monthly returns to match the fund
convention, caches the cleaned series to disk so a memo stays reproducible, and
stamps provenance (source, url, as-of, fetched-at). ANY failure — no network,
timeout, unknown series — falls back to the committed snapshot, so the offline
and test paths never depend on a live call.
"""
from __future__ import annotations

import io
import json
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd

from .config import get_settings
from .ingest import _parse_date, normalize_return
from .models import Benchmark, ReturnPoint

# Official FRED API (keyed) — has real history and is the "proper" integration.
# The key lives server-side (config/.env) and is never shipped to the browser.
_FRED_API = "https://api.stlouisfed.org/fred/series/observations"

# benchmark_id -> (FRED series id, display name). FRED index series are daily
# price levels; we convert to monthly returns. Total-return series need a key,
# so these are price-return and labelled honestly.
_FRED_INDEX = {
    "SP500": ("SP500", "S&P 500 (price, FRED)"),
    "NASDAQ": ("NASDAQCOM", "NASDAQ Composite (price, FRED)"),
    "DJIA": ("DJIA", "Dow Jones Industrial Average (price, FRED)"),
    "WILSHIRE": ("WILL5000INDFC", "Wilshire 5000 (full-cap, FRED)"),
}
# risk-free: 3-Month Treasury Bill secondary-market rate, monthly, in percent.
_FRED_RISK_FREE = "TB3MS"
_FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"

_SNAP_NAMES = {"sp500": "S&P 500 Total Return", "agg": "US Aggregate Bond"}


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _http_get(url: str, timeout: float) -> str:
    """GET text with a hard timeout, robust to macOS's missing SSL cert store.

    Tries requests (bundles CA certs) first, then urllib with a certifi context,
    then urllib's default context. Raises RuntimeError listing every failure so
    the caller can tell the user *why* a live fetch fell back."""
    headers = {"User-Agent": "AllocatorMemoBuilder/0.3"}
    errors = []
    try:
        import requests  # bundles its own CA bundle — fixes the common macOS SSL error
        r = requests.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
        return r.text
    except ImportError:
        pass
    except Exception as e:  # noqa: BLE001
        errors.append(f"requests: {e!r}")
    import ssl
    try:
        try:
            import certifi
            ctx = ssl.create_default_context(cafile=certifi.where())
        except Exception:  # noqa: BLE001
            ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.read().decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        errors.append(f"urllib: {e!r}")
    raise RuntimeError("FRED unreachable — " + " | ".join(errors))


def _read_fred_api(series_id: str, api_key: str, timeout: float = 12.0) -> pd.DataFrame:
    """Fetch a series via the official keyed FRED API (JSON). Raises on failure."""
    q = urllib.parse.urlencode({"series_id": series_id, "api_key": api_key, "file_type": "json"})
    raw = _http_get(f"{_FRED_API}?{q}", timeout)
    obs = json.loads(raw).get("observations", [])
    rows = [(o.get("date"), o.get("value")) for o in obs if o.get("value") not in (None, ".", "")]
    out = pd.DataFrame(rows, columns=["date", "value"])
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    out = out.dropna()
    if out.empty:
        raise ValueError(f"FRED API series {series_id} returned no usable rows")
    return out


def _read_fred(series_id: str, timeout: float = 12.0) -> pd.DataFrame:
    """Fetch a FRED series as a tidy (date, value) frame. Raises on failure.

    Uses the keyed official API when a key is configured (proper integration,
    full history), else the keyless fredgraph.csv endpoint."""
    key = get_settings().fred_api_key.strip()
    if key:
        return _read_fred_api(series_id, key, timeout)
    url = _FRED_URL.format(sid=series_id)
    raw = _http_get(url, timeout)
    df = pd.read_csv(io.StringIO(raw))
    # FRED CSVs have an observation-date column (name varies) + the series column.
    date_col = df.columns[0]
    val_col = series_id if series_id in df.columns else df.columns[-1]
    out = df[[date_col, val_col]].copy()
    out.columns = ["date", "value"]
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    out = out.dropna()
    if out.empty:
        raise ValueError(f"FRED series {series_id} returned no usable rows")
    return out


def fetch_risk_free_annual(timeout: float = 12.0) -> Optional[float]:
    """Latest 3M T-bill rate as an annual decimal (0.0366 for 3.66%)."""
    try:
        df = _read_fred(_FRED_RISK_FREE, timeout)
        return round(float(df["value"].iloc[-1]) / 100.0, 6)
    except Exception:
        return None


def _index_to_monthly_returns(df: pd.DataFrame) -> list[ReturnPoint]:
    """Daily price levels -> first-of-month monthly returns."""
    s = df.set_index("date")["value"].sort_index()
    monthly = s.resample("MS").first()  # first observed level each month
    rets = monthly.pct_change().dropna()
    pts = [ReturnPoint(period=idx.date(), value=float(v)) for idx, v in rets.items()]
    return pts


def fetch_benchmark(benchmark_id: str, timeout: float = 12.0) -> Benchmark:
    """Live benchmark from FRED. Raises if the id is unknown or the fetch fails."""
    key = benchmark_id.upper()
    if key not in _FRED_INDEX:
        raise ValueError(f"no live FRED mapping for benchmark '{benchmark_id}'")
    sid, name = _FRED_INDEX[key]
    df = _read_fred(sid, timeout)
    pts = _index_to_monthly_returns(df)
    if len(pts) < 2:
        raise ValueError(f"benchmark {benchmark_id} produced too few monthly returns")
    as_of = pts[-1].period
    return Benchmark(
        benchmark_id=key,
        name=name,
        as_of=as_of,
        frequency="monthly",
        periods_per_year=12,
        points=pts,
        source=_FRED_URL.format(sid=sid),
        source_kind="live",
        source_name="FRED",
        fetched_at=_now_utc(),
    )


def _write_cache(bench: Benchmark, cache_dir: Path) -> None:
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        rows = [{"date": p.period.isoformat(), "return": p.value} for p in bench.points]
        pd.DataFrame(rows).to_csv(cache_dir / f"{bench.benchmark_id.lower()}_monthly.csv", index=False)
    except Exception:
        pass  # caching is best-effort; never break a build over it


def _load_cache(benchmark_id: str, cache_dir: Path) -> Optional[Benchmark]:
    path = cache_dir / f"{benchmark_id.lower()}_monthly.csv"
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path)
        pts = []
        for _, r in df.iterrows():
            d, v = _parse_date(r["date"]), normalize_return(r["return"])
            if d is not None and v is not None:
                pts.append(ReturnPoint(period=d, value=v))
        pts.sort(key=lambda p: p.period)
        if len(pts) < 2:
            return None
        name = _FRED_INDEX.get(benchmark_id.upper(), (None, benchmark_id.upper()))[1]
        return Benchmark(
            benchmark_id=benchmark_id.upper(), name=name, as_of=pts[-1].period,
            frequency="monthly", periods_per_year=12, points=pts,
            source=str(path), source_kind="cache", source_name="FRED (cached)",
        )
    except Exception:
        return None


def _load_snapshot(benchmark_id: str, snapshot_dir: Path) -> Optional[Benchmark]:
    path = snapshot_dir / f"{benchmark_id.lower()}_monthly.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path)
    pts = []
    for _, r in df.iterrows():
        d, v = _parse_date(r["date"]), normalize_return(r["return"])
        if d is not None and v is not None:
            pts.append(ReturnPoint(period=d, value=v))
    pts.sort(key=lambda p: p.period)
    if not pts:
        return None
    return Benchmark(
        benchmark_id=benchmark_id.upper(),
        name=_SNAP_NAMES.get(benchmark_id.lower(), benchmark_id.upper()),
        as_of=pts[-1].period, frequency="monthly", periods_per_year=12, points=pts,
        source=str(path), source_kind="snapshot", source_name="bundled snapshot",
    )


def resolve_benchmark(
    benchmark_id: str = "SP500",
    mode: str = "snapshot",
    data_dir: str | Path = "data",
) -> Optional[Benchmark]:
    """The single entry point pipeline uses. `mode` is one of:
      snapshot  — committed fixture only (deterministic; default for tests)
      live/auto — try FRED, then cache, then snapshot (graceful degradation)
    Returns None only if every source is missing.
    """
    data_dir = Path(data_dir)
    snap_dir = data_dir / "benchmarks"
    cache_dir = snap_dir / "cache"

    if mode in ("live", "auto"):
        try:
            bench = fetch_benchmark(benchmark_id)
            _write_cache(bench, cache_dir)
            print(f"✓ live benchmark: {bench.name} via FRED · {len(bench.points)} monthly obs · as-of {bench.as_of}", file=sys.stderr)
            return bench
        except Exception as e:  # noqa: BLE001
            cached = _load_cache(benchmark_id, cache_dir)
            if cached is not None:
                print(f"! live FRED fetch failed ({e}); using cached benchmark ({cached.as_of})", file=sys.stderr)
                return cached
            print(f"! live FRED fetch failed ({e}); falling back to the committed snapshot", file=sys.stderr)
    return _load_snapshot(benchmark_id, snap_dir)

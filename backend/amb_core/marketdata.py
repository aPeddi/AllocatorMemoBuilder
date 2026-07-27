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
import logging
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd

from .coercion import normalize_return, parse_date
from .models import Benchmark, ReturnPoint

log = logging.getLogger("amb.marketdata")

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

# ── Yahoo Finance (keyless public chart endpoint; what yfinance uses) ──────────
# benchmark_id -> (Yahoo symbol, display name). Yahoo's monthly bars carry an
# adjusted close (dividend-inclusive → total return), a truer benchmark than FRED's
# price-only index series.
_YF_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=15y&interval=1mo"
_YF_INDEX = {
    "SP500": ("^GSPC", "S&P 500 (Yahoo)"),
    "NASDAQ": ("^IXIC", "NASDAQ Composite (Yahoo)"),
    "DJIA": ("^DJI", "Dow Jones Industrial Average (Yahoo)"),
    "WILSHIRE": ("^W5000", "Wilshire 5000 (Yahoo)"),
}


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _http_get(url: str, timeout: float, extra_headers: Optional[dict] = None, label: str = "source") -> str:
    """GET text with a hard timeout, robust to macOS's missing SSL cert store.

    Tries requests (bundles CA certs) first, then urllib with a certifi context,
    then urllib's default context. Raises RuntimeError listing every failure so
    the caller can tell the user *why* a live fetch fell back."""
    headers = {"User-Agent": "AllocatorMemoBuilder/0.3"}
    if extra_headers:
        headers.update(extra_headers)
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
    raise RuntimeError(f"{label} unreachable — " + " | ".join(errors))


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


def _read_fred(series_id: str, timeout: float = 12.0, api_key: str = "") -> pd.DataFrame:
    """Fetch a FRED series as a tidy (date, value) frame. Raises on failure.

    Uses the keyed official API when a key is supplied (proper integration, full
    history), else the keyless fredgraph.csv endpoint. The key is passed in by the
    caller (composition root) — never read from global config here."""
    key = (api_key or "").strip()
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


def fetch_risk_free_annual(timeout: float = 12.0, api_key: str = "") -> Optional[float]:
    """Latest 3M T-bill rate as an annual decimal (0.0366 for 3.66%).

    Returns None (caller falls back to the mandate default) only for *expected*
    fetch/parse failures — which are logged, so a genuine bug isn't silently
    swallowed as a valid "no data" fallback.
    """
    try:
        df = _read_fred(_FRED_RISK_FREE, timeout, api_key)
        return round(float(df["value"].iloc[-1]) / 100.0, 6)
    except (RuntimeError, ValueError, KeyError, IndexError, OSError, pd.errors.ParserError) as e:
        log.warning("risk-free fetch failed, using mandate default: %s", e)
        return None


def _index_to_monthly_returns(df: pd.DataFrame) -> list[ReturnPoint]:
    """Daily price levels -> first-of-month monthly returns."""
    s = df.set_index("date")["value"].sort_index()
    monthly = s.resample("MS").first()  # first observed level each month
    rets = monthly.pct_change().dropna()
    pts = [ReturnPoint(period=idx.date(), value=float(v)) for idx, v in rets.items()]
    return pts


def fetch_benchmark(benchmark_id: str, timeout: float = 12.0, api_key: str = "") -> Benchmark:
    """Live benchmark from FRED. Raises if the id is unknown or the fetch fails."""
    key = benchmark_id.upper()
    if key not in _FRED_INDEX:
        raise ValueError(f"no live FRED mapping for benchmark '{benchmark_id}'")
    sid, name = _FRED_INDEX[key]
    df = _read_fred(sid, timeout, api_key)
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


def _read_yahoo(symbol: str, timeout: float = 12.0, api_key: str = "") -> pd.DataFrame:
    """Fetch a Yahoo monthly chart as a tidy (date, value) frame of adjusted closes.

    Uses the keyless public chart endpoint by default (the same one yfinance uses);
    a key, if supplied, is sent as a gateway header for a gated Yahoo proxy. Raises
    on failure so the caller can fall back."""
    extra = {"X-API-KEY": api_key.strip(), "X-RapidAPI-Key": api_key.strip()} if (api_key or "").strip() else None
    raw = _http_get(_YF_URL.format(sym=urllib.parse.quote(symbol)), timeout, extra, label="Yahoo Finance")
    result = (json.loads(raw).get("chart", {}).get("result") or [None])[0]
    if not result:
        raise ValueError(f"Yahoo returned no result for {symbol}")
    ts = result.get("timestamp") or []
    ind = result.get("indicators", {})
    adj = (ind.get("adjclose") or [{}])[0].get("adjclose")
    close = (ind.get("quote") or [{}])[0].get("close")
    vals = adj if adj else close  # prefer dividend-inclusive adjusted close (total return)
    if not ts or not vals or len(ts) != len(vals):
        raise ValueError(f"Yahoo series for {symbol} is empty or misaligned")
    rows = [(datetime.fromtimestamp(int(t), tz=timezone.utc).date().replace(day=1), v)
            for t, v in zip(ts, vals) if v is not None]
    out = pd.DataFrame(rows, columns=["date", "value"])
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    out = out.dropna()
    if out.empty:
        raise ValueError(f"Yahoo series {symbol} returned no usable rows")
    return out


def fetch_benchmark_yahoo(benchmark_id: str, timeout: float = 12.0, api_key: str = "") -> Benchmark:
    """Live benchmark from Yahoo Finance. Raises if the id is unknown or the fetch fails."""
    key = benchmark_id.upper()
    if key not in _YF_INDEX:
        raise ValueError(f"no Yahoo mapping for benchmark '{benchmark_id}'")
    sym, name = _YF_INDEX[key]
    df = _read_yahoo(sym, timeout, api_key)
    pts = _index_to_monthly_returns(df)
    if len(pts) < 2:
        raise ValueError(f"benchmark {benchmark_id} produced too few monthly returns from Yahoo")
    return Benchmark(
        benchmark_id=key, name=name, as_of=pts[-1].period,
        frequency="monthly", periods_per_year=12, points=pts,
        source=_YF_URL.format(sym=sym), source_kind="live", source_name="Yahoo Finance",
        fetched_at=_now_utc(),
    )


# provider id -> (display, fetch fn taking (benchmark_id, timeout, api_key))
_PROVIDERS = {
    "fred": ("FRED", fetch_benchmark),
    "yahoo": ("Yahoo Finance", fetch_benchmark_yahoo),
}


def _provider_order(provider: str) -> list[str]:
    """Which live providers to try, in order. 'auto' tries both (FRED first for
    continuity with older memos); a named provider pins exactly that one."""
    p = (provider or "auto").strip().lower()
    if p == "yahoo":
        return ["yahoo"]
    if p == "fred":
        return ["fred"]
    return ["fred", "yahoo"]


def _write_cache(bench: Benchmark, cache_dir: Path) -> None:
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        rows = [{"date": p.period.isoformat(), "return": p.value} for p in bench.points]
        pd.DataFrame(rows).to_csv(cache_dir / f"{bench.benchmark_id.lower()}_monthly.csv", index=False)
    except OSError as e:
        log.debug("benchmark cache write skipped (best-effort): %s", e)  # never break a build over caching


def _benchmark_from_csv(
    path: Path, benchmark_id: str, name: str, source_kind: str, source_name: str,
    min_points: int = 1,
) -> Optional[Benchmark]:
    """The ONE monthly-CSV -> Benchmark loader, shared by every disk-backed source
    (cache, snapshot; formerly a third copy in benchmarks.py). Returns None if the
    file is absent or has too few usable rows."""
    if not path.exists():
        return None
    df = pd.read_csv(path)
    pts = []
    for _, r in df.iterrows():
        d, v = parse_date(r["date"]), normalize_return(r["return"])
        if d is not None and v is not None:
            pts.append(ReturnPoint(period=d, value=v))
    pts.sort(key=lambda p: p.period)
    if len(pts) < min_points:
        return None
    return Benchmark(
        benchmark_id=benchmark_id.upper(), name=name, as_of=pts[-1].period,
        frequency="monthly", periods_per_year=12, points=pts,
        source=str(path), source_kind=source_kind, source_name=source_name,
    )


def _load_cache(benchmark_id: str, cache_dir: Path) -> Optional[Benchmark]:
    name = _FRED_INDEX.get(benchmark_id.upper(), (None, benchmark_id.upper()))[1]
    try:
        return _benchmark_from_csv(
            cache_dir / f"{benchmark_id.lower()}_monthly.csv",
            benchmark_id, name, "cache", "FRED (cached)", min_points=2,
        )
    except (OSError, ValueError, KeyError, pd.errors.ParserError) as e:
        log.warning("benchmark cache read failed, ignoring cache: %s", e)
        return None


def load_snapshot(benchmark_id: str, snapshot_dir: Path) -> Optional[Benchmark]:
    """Load a committed benchmark snapshot (the deterministic, offline source)."""
    return _benchmark_from_csv(
        snapshot_dir / f"{benchmark_id.lower()}_monthly.csv",
        benchmark_id, _SNAP_NAMES.get(benchmark_id.lower(), benchmark_id.upper()),
        "snapshot", "bundled snapshot", min_points=1,
    )


# backwards-compatible private alias
_load_snapshot = load_snapshot


def _fetch_live(benchmark_id: str, provider: str, api_key: str, yahoo_api_key: str, timeout: float = 12.0) -> Benchmark:
    """Fetch one provider's live benchmark. Raises on failure."""
    _name, fn = _PROVIDERS[provider]
    key = yahoo_api_key if provider == "yahoo" else api_key
    return fn(benchmark_id, timeout=timeout, api_key=key)


def resolve_benchmark(
    benchmark_id: str = "SP500",
    mode: str = "snapshot",
    data_dir: str | Path = "data",
    api_key: str = "",
    provider: str = "auto",
    yahoo_api_key: str = "",
) -> Optional[Benchmark]:
    """The single entry point pipeline uses. `mode` is one of:
      snapshot  — committed fixture only (deterministic; default for tests)
      live/auto — try the configured provider(s), then cache, then snapshot
    `provider` is auto | fred | yahoo. Returns None only if every source is missing.
    Keys (FRED / Yahoo) are supplied by the caller — this module never reads config.
    """
    data_dir = Path(data_dir)
    snap_dir = data_dir / "benchmarks"
    cache_dir = snap_dir / "cache"

    if mode in ("live", "auto"):
        for prov in _provider_order(provider):
            try:
                bench = _fetch_live(benchmark_id, prov, api_key, yahoo_api_key)
                _write_cache(bench, cache_dir)
                print(f"✓ live benchmark: {bench.name} via {bench.source_name} · {len(bench.points)} monthly obs · as-of {bench.as_of}", file=sys.stderr)
                return bench
            except Exception as e:  # noqa: BLE001
                print(f"! live {prov} fetch failed ({e})", file=sys.stderr)
        cached = _load_cache(benchmark_id, cache_dir)
        if cached is not None:
            print(f"! all live providers failed; using cached benchmark ({cached.as_of})", file=sys.stderr)
            return cached
        print("! all live providers failed; falling back to the committed snapshot", file=sys.stderr)
    return _load_snapshot(benchmark_id, snap_dir)


def resolve_providers(
    benchmark_id: str = "SP500",
    data_dir: str | Path = "data",
    api_key: str = "",
    yahoo_api_key: str = "",
    timeout: float = 8.0,
) -> dict:
    """Probe EVERY live provider and report which returned data. The serve layer uses
    this to let the page offer a source choice when more than one is available; each
    entry is {ok, name, benchmark?} and never raises (a dead provider is ok=False)."""
    out: dict = {}
    for prov, (name, _fn) in _PROVIDERS.items():
        try:
            b = _fetch_live(benchmark_id, prov, api_key, yahoo_api_key, timeout=timeout)
            out[prov] = {"ok": True, "name": b.name, "benchmark": b}
        except Exception as e:  # noqa: BLE001
            out[prov] = {"ok": False, "name": name, "error": str(e)[:120]}
    return out

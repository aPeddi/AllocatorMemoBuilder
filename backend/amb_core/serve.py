"""A tiny localhost server so the *browser* can make a real, live FRED call.

The browser can't call FRED directly (no CORS) and the key must never ship in
client code — so this process holds the key, exposes `/api/market`, and the page
fetches that: browser → localhost → FRED. It also serves the built memo. Falls
back to the committed snapshot if the live call fails. (ADR-0010.)

Right-sized for a single-user local tool: bound to 127.0.0.1, keys read
server-side only (responses expose booleans like `has_fred_key`, never the
secret), no client-supplied input beyond a whitelisted `mode`, and errors return
generic text with detail logged server-side.
"""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse

from .config import get_settings
from .ingest import load_dataset
from .marketdata import fetch_risk_free_annual, resolve_benchmark, resolve_providers
from .metrics import annualize as _annualize  # shared engine helper (ret, vol, wealth)

log = logging.getLogger("amb.serve")

ROOT = Path(".")
EXPORTS = ROOT / "exports"
SAMPLES = ROOT / "data" / "samples"

_ALLOWED_MODES = {"live", "snapshot", "cache"}

app = FastAPI(title="AllocatorMemoBuilder · live market data")


@app.middleware("http")
async def _security_headers(request: Request, call_next):
    """Conservative headers for a local tool that renders untrusted CSV-derived data."""
    resp = await call_next(request)
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("Referrer-Policy", "no-referrer")
    resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    return resp


def _fund_window():
    """(lo, hi) of the sample fund return window, so a benchmark curve overlays it."""
    try:
        _funds, series, _quar = load_dataset(SAMPLES / "dataset.csv")
        periods = {p.period for sr in series.values() for p in sr.points}
        return min(periods), max(periods)
    except Exception:  # noqa: BLE001
        return None, None


def _bench_summary(bench, lo, hi) -> dict:
    """A benchmark aligned to the fund window + annualized on the shared engine."""
    win = [p for p in bench.points if (lo is None or lo <= p.period <= hi)] or bench.points
    ret, vol, wealth = _annualize([p.value for p in win])
    return {
        "name": bench.name, "ret": ret, "vol": vol, "wealth": wealth,
        "kind": bench.source_kind, "srcName": bench.source_name,
        "asOf": str(win[-1].period if win else bench.as_of), "n": len(win),
    }


def market_payload(data_dir: str = "data", mode: str = "live", provider: str = "") -> dict:
    """Live benchmark + risk-free, aligned to the sample fund window. Probes EVERY live
    provider (FRED, Yahoo) so the page can offer a source choice when more than one is
    available; the keys are used server-side only and never leave this process."""
    if mode not in _ALLOWED_MODES:  # defence-in-depth: never trust an unexpected mode
        mode = "live"
    s = get_settings()
    lo, hi = _fund_window()

    # probe both providers (live) so the client can choose when both return data
    providers: dict = {}
    live_any = None
    if mode in ("live", "cache"):
        # short per-provider timeout so one slow/unreachable source can't stall the endpoint
        probe = resolve_providers("SP500", data_dir=data_dir, api_key=s.fred_api_key, yahoo_api_key=s.yahoo_api_key, timeout=5.0)
        for pid, info in probe.items():
            if info.get("ok"):
                b = info["benchmark"]
                providers[pid] = {"ok": True, "name": info["name"], "benchmark": _bench_summary(b, lo, hi)}
                live_any = live_any or b
            else:
                providers[pid] = {"ok": False, "name": info.get("name", pid), "error": info.get("error", "")}

    # choose the primary: the requested provider if live, else config order, else any
    # live, else fall through to cache/snapshot via resolve_benchmark.
    order = [p for p in [(provider or s.benchmark_provider), "fred", "yahoo"] if p]
    chosen_id = next((p for p in order if providers.get(p, {}).get("ok")), None)
    if chosen_id:
        primary = providers[chosen_id]["benchmark"]
    else:
        bench = resolve_benchmark("SP500", mode=mode, data_dir=data_dir, api_key=s.fred_api_key,
                                  provider=s.benchmark_provider, yahoo_api_key=s.yahoo_api_key)
        if bench is None:
            return {"ok": False, "error": "no benchmark source available"}
        primary = _bench_summary(bench, lo, hi)
        chosen_id = "fred" if bench.source_name.startswith("FRED") else ("yahoo" if "Yahoo" in bench.source_name else "snapshot")

    is_live = primary["kind"] == "live"
    # risk-free comes from FRED only — skip the call (and its timeout) when FRED is down
    fred_ok = providers.get("fred", {}).get("ok", False)
    rf = fetch_risk_free_annual(api_key=s.fred_api_key, timeout=5.0) if (is_live and fred_ok) else None
    return {
        "ok": True,
        "live": is_live,
        "keyed": s.has_fred_key,          # boolean only — the key itself never leaves the server
        "yahooKeyed": s.has_yahoo_key,
        "provider": chosen_id,
        "providers": providers,           # {fred:{ok,name,benchmark?}, yahoo:{ok,name,benchmark?}}
        "benchmark": primary,             # the chosen source (back-compat with older clients)
        "riskFree": {"value": rf, "source": "FRED · 3M T-bill" if rf is not None else "mandate"},
    }


@app.get("/api/market")
def api_market(provider: str = ""):
    try:
        return JSONResponse(market_payload(provider=provider))
    except Exception as e:  # noqa: BLE001 — log detail server-side, return a generic message
        log.warning("market_payload failed: %s", e)
        return JSONResponse({"ok": False, "error": "market data temporarily unavailable"}, status_code=502)


@app.post("/api/map-columns")
async def api_map_columns(request: Request):
    """Served-mode ingest assist: propose a CSV column mapping (structure only).
    Receives just the header + a few sample rows (never the full file, never values);
    returns index-based hints the browser presents for the user to confirm. Falls back
    to `{ok: False}` (client uses its deterministic detection) when no LLM is configured."""
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        return JSONResponse({"ok": False, "error": "bad request"}, status_code=400)
    header = body.get("header") or []
    samples = body.get("samples") or []
    shape = body.get("shape") or "long"
    if not isinstance(header, list) or not header or len(header) > 512:
        return JSONResponse({"ok": False, "error": "header required"}, status_code=400)
    samples = [r for r in samples if isinstance(r, list)][:8]  # cap: only a taste of the data leaves the browser
    from .llm import propose_mapping, select_tool_caller
    caller = select_tool_caller()
    if caller is None:
        return JSONResponse({"ok": False, "reason": "no LLM configured"})
    try:
        return JSONResponse(propose_mapping(header, samples, str(shape), caller))
    except Exception as e:  # noqa: BLE001 — degrade to deterministic client detection
        log.warning("map-columns proposal failed: %s", e)
        return JSONResponse({"ok": False, "error": "mapping unavailable"}, status_code=502)


@app.get("/api/health")
def api_health():
    s = get_settings()
    return {"ok": True, "fred_key": s.has_fred_key, "mode": "live"}


@app.get("/")
def index():
    # Only ever the one built artifact is served; no client-supplied path is honoured.
    f = EXPORTS / "memo.html"
    if not f.exists():
        return JSONResponse({"error": "run `./amb` once to build the memo, then `./amb serve`"}, status_code=404)
    return FileResponse(str(f), media_type="text/html")


def run_server() -> int:
    import uvicorn

    s = get_settings()
    src = "live FRED (keyed API)" if s.has_fred_key else "live FRED (keyless fredgraph)"
    print(f"▸ Serving the memo with a live market-data proxy → {src}")
    print(f"  open  http://{s.serve_host}:{s.serve_port}   ·  the page will fetch /api/market live")
    uvicorn.run(app, host=s.serve_host, port=s.serve_port, log_level="warning")
    return 0

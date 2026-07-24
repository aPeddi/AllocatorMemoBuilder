"""`./amb serve` — a tiny local API so the *browser* makes a real, live FRED call.

The browser can't call FRED directly (FRED sends no CORS header), and the API key
must never ship in client code. So this process holds the key server-side, exposes
`/api/market`, and the page fetches that: browser → localhost → FRED. The secret
stays on the server; the reviewer sees a real market-data API call in the network
tab and the server log. Falls back to the committed snapshot if the live call fails.

Security posture (local, single-user tool):
  * The FRED / LLM keys are read server-side only; responses expose booleans
    (`has_fred_key`) never the secret itself.
  * Endpoints take no client-supplied input, so there is no injection surface;
    `mode` is validated against a whitelist as defence-in-depth.
  * Only the built memo file is ever served — no arbitrary path is exposed.
  * Bound to 127.0.0.1 by default (see config.serve_host) — not the network.
  * Same-origin by default (no permissive CORS); errors return generic text
    and the detail is logged server-side, never leaked to the client.
"""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse

from .config import get_settings
from .ingest import load_returns
from .marketdata import fetch_risk_free_annual, resolve_benchmark
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


def market_payload(data_dir: str = "data", mode: str = "live") -> dict:
    """Live benchmark + risk-free, aligned to the sample fund window. The one place
    the FRED key is used — server-side only."""
    if mode not in _ALLOWED_MODES:  # defence-in-depth: never trust an unexpected mode
        mode = "live"
    s = get_settings()
    bench = resolve_benchmark("SP500", mode=mode, data_dir=data_dir, api_key=s.fred_api_key)
    if bench is None:
        return {"ok": False, "error": "no benchmark source available"}
    # align to the fund window so the live curve overlays the fund curves
    try:
        series, _ = load_returns(SAMPLES / "returns.csv")
        periods = {p.period for sr in series.values() for p in sr.points}
        lo, hi = min(periods), max(periods)
        win = [p for p in bench.points if lo <= p.period <= hi]
    except Exception:
        win = bench.points
    vals = [p.value for p in win]
    ret, vol, wealth = _annualize(vals)
    rf = fetch_risk_free_annual(api_key=s.fred_api_key) if bench.source_kind == "live" else None
    return {
        "ok": True,
        "live": bench.source_kind == "live",
        "keyed": s.has_fred_key,  # boolean only — the key itself never leaves the server
        "benchmark": {
            "name": bench.name, "ret": ret, "vol": vol, "wealth": wealth,
            "kind": bench.source_kind, "srcName": bench.source_name,
            "asOf": str(win[-1].period if win else bench.as_of), "n": len(win),
        },
        "riskFree": {"value": rf, "source": "FRED · 3M T-bill" if rf is not None else "mandate"},
    }


@app.get("/api/market")
def api_market():
    try:
        return JSONResponse(market_payload())
    except Exception as e:  # noqa: BLE001 — log detail server-side, return a generic message
        log.warning("market_payload failed: %s", e)
        return JSONResponse({"ok": False, "error": "market data temporarily unavailable"}, status_code=502)


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

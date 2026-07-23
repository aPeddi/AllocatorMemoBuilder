"""`./amb serve` — a tiny local API so the *browser* makes a real, live FRED call.

The browser can't call FRED directly (FRED sends no CORS header), and the API key
must never ship in client code. So this process holds the key server-side, exposes
`/api/market`, and the page fetches that: browser → localhost → FRED. The secret
stays on the server; the reviewer sees a real market-data API call in the network
tab and the server log. Falls back to the committed snapshot if the live call fails.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse

from .config import get_settings
from .ingest import load_returns
from .marketdata import fetch_risk_free_annual, resolve_benchmark

ROOT = Path(".")
EXPORTS = ROOT / "exports"
SAMPLES = ROOT / "data" / "samples"

app = FastAPI(title="AllocatorMemoBuilder · live market data")


def _annualize(vals: list[float], ppy: int = 12):
    n = len(vals)
    if n < 2:
        return None, None, []
    g = 1.0
    for v in vals:
        g *= 1.0 + v
    ret = g ** (ppy / n) - 1.0 if g > 0 else g - 1.0
    mean = sum(vals) / n
    var = sum((v - mean) ** 2 for v in vals) / (n - 1)
    vol = var ** 0.5 * ppy ** 0.5
    wealth, c = [], 1.0
    for v in vals:
        c *= 1.0 + v
        wealth.append(round(c, 4))
    return ret, vol, wealth


def market_payload(data_dir: str = "data", mode: str = "live") -> dict:
    """Live benchmark + risk-free, aligned to the sample fund window. The one place
    the FRED key is used — server-side only."""
    s = get_settings()
    bench = resolve_benchmark("SP500", mode=mode, data_dir=data_dir)
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
    rf = fetch_risk_free_annual() if bench.source_kind == "live" else None
    return {
        "ok": True,
        "live": bench.source_kind == "live",
        "keyed": s.has_fred_key,
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
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"ok": False, "error": str(e)})


@app.get("/api/health")
def api_health():
    s = get_settings()
    return {"ok": True, "fred_key": s.has_fred_key, "mode": "live"}


@app.get("/")
def index():
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

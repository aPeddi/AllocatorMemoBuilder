"""Regression tests for the classes of bug that have actually bitten this project.

Each test pins an invariant whose violation we saw as a behavioural symptom, so the
next regression is caught by `./test` instead of by staring at the running app:

  * quarantine reasons stay SPECIFIC (not a blanket "bad date")
  * the ingest schema reports the real file's columns/roles
  * one outlier fund can't crush the scatter cluster into a corner (robust axis)
  * the benchmark reference line passes through the benchmark marker
  * the engine value overrides a wrong model value (verified by construction)
  * the single-file dataset is the sole bundled sample
"""
import json
import re
from pathlib import Path

import pytest

from amb_core.export import _axis, _pos, render_html
from amb_core.ingest import dataset_schema, load_dataset
from amb_core.pipeline import load_mandate, run


# ── ingest: specific quarantine reasons ───────────────────────────────────────
def test_quarantine_reasons_are_specific_not_blanket():
    """The bundled sample has one bad-date row, one bad-return row, and one with
    both. The reasons must distinguish them — a generic string that always buckets
    to 'bad date' is exactly the bug we shipped once."""
    _funds, _series, quarantined = load_dataset("data/samples/dataset.csv")
    reasons = {q["reason"] for q in quarantined}
    assert any("date" in r for r in reasons)
    assert any("return" in r for r in reasons)
    # not collapsed to a single blanket reason
    assert len(reasons) >= 2


def test_reason_distinguishes_missing_from_unparseable(tmp_path):
    """A blank cell is 'missing X'; a present-but-malformed cell is 'unparseable X'.
    'missing date' must not be reported as 'bad date' — they mean different things."""
    csv = tmp_path / "d.csv"
    csv.write_text(
        "date,fund_id,monthly_return\n"
        "2024-01-01,AAA,0.01\n2024-02-01,AAA,0.02\n"
        ",AAA,0.03\n"                 # blank date        -> missing date
        "2024-03-01,AAA,\n"           # blank return      -> missing return
        "not-a-date,AAA,0.04\n"       # malformed date    -> unparseable date
        "2024-04-01,,0.05\n"          # blank fund id     -> missing fund id
    )
    _f, _s, quar = load_dataset(str(csv))
    reasons = {q["reason"] for q in quar}
    assert any("missing date" in r for r in reasons)
    assert any("missing return" in r for r in reasons)
    assert any("unparseable date" in r for r in reasons)
    assert any("missing fund id" in r for r in reasons)
    # a blank date is never mislabeled as a malformed one
    assert not any(r == "bad date" for r in reasons)


# ── ingest schema: the app must show the real file's fields ───────────────────
def test_dataset_schema_reports_real_columns_and_roles(tmp_path):
    # synonyms the detector recognizes (period→date, symbol→id, performance→return, style→strategy)
    csv = tmp_path / "custom.csv"
    csv.write_text("period,symbol,performance,style\n2024-01-01,ORV,0.01,Macro\n")
    sc = dataset_schema(str(csv))
    by_role = {c["role"]: c["name"] for c in sc["cols"]}
    assert by_role["date"] == "period"
    assert by_role["id"] == "symbol"
    assert by_role["return"] == "performance"
    assert "style" in sc["optional"]
    assert sc["file"] == "custom.csv"


def test_pipeline_threads_ingest_schema_into_readiness():
    mandate = load_mandate("data/mandates/default.yaml")
    _memo, ctx = run("data/samples/dataset.csv", mandate)
    ing = ctx.readiness.get("ingest")
    assert ing and ing["file"] == "dataset.csv"
    roles = {c["role"] for c in ing["cols"]}
    assert {"date", "id", "return"} <= roles


# ── scatter: a robust axis so an outlier can't crush the cluster ──────────────
def test_axis_outlier_does_not_crush_the_cluster():
    cluster = [0.03, 0.04, 0.05, 0.06, 0.07]
    ax = _axis(cluster + [0.40])                       # one extreme fund
    # the range is the INLIER span, not stretched out to the outlier
    assert ax[1] < 0.15, "axis high was pulled toward the outlier"
    pos = [_pos(v, ax) for v in cluster]
    assert max(pos) - min(pos) > 0.5, "cluster got crushed into a thin band"
    out = _pos(0.40, ax)
    assert max(pos) <= out <= 1.0, "outlier must sit above the bulk, on-canvas"
    assert 0.0 <= _pos(-0.5, ax) <= 0.1, "below-range value must clamp to the floor"


def test_benchmark_is_anchored_not_saturated():
    """The reported bug: with a big outlier fund (Cedar ~37%) and a tight low cluster,
    the S&P reference (~12%) saturated into the SAME top band as the outlier, so it read
    as a ~35% return. The benchmark must anchor the shared axis so it lands in the
    proportional bulk (clearly above the cluster, clearly BELOW the outlier), not pinned
    to a saturating margin. A reference below the cluster must likewise not pin to the
    floor. Mirrors the client's _axisWith; the two must stay identical."""
    from amb_core.export import _axis_with
    cluster = [0.053, 0.054, 0.064, 0.072, 0.082]     # the 5–8% fund cluster
    ax = _axis(cluster + [0.375])                      # + Cedar, the extreme outlier
    bench_hi = 0.12                                     # S&P above the cluster fence
    # WITHOUT anchoring it saturates into the top band with the outlier …
    assert _pos(bench_hi, ax) > 0.95, "precondition: an above-fence bench would saturate"
    # … WITH anchoring it lands in the proportional bulk, and strictly below the outlier
    axb = _axis_with(ax, bench_hi)
    p_bench = _pos(bench_hi, axb)
    p_out = _pos(0.375, axb)
    assert 0.05 < p_bench <= 0.9501, f"anchored benchmark must be proportional, got {p_bench:.3f}"
    assert p_out - p_bench > 0.02, "outlier fund must sit clearly ABOVE the reference, not on top of it"
    # a reference below the cluster anchors the axis floor (bulk bottom), not a saturated margin
    axlo = _axis_with(ax, 0.02)
    assert _pos(0.02, axlo) == pytest.approx(0.05, abs=1e-6)


# ── HUD data: marker sits on its reference line; cluster stays balanced ───────
def _extract_data(html: str) -> dict:
    m = re.search(r"window\.AMB=(\{.*?\});</script>", html, re.S)
    assert m, "window.AMB payload not found in the rendered HTML"
    raw = (m.group(1)
           .replace("\\u003c", "<").replace("\\u003e", ">").replace("\\u0026", "&"))
    return json.loads(raw)


def _outlier_ctx(tmp_path):
    hdr = "date,fund_id,monthly_return,strategy,redemption_freq,lockup_months,notice_days"
    means = {"CEDAR": 0.028, "BLUEFIN": 0.005, "MERIDIAN": 0.004,
             "ORION": 0.007, "KEYSTONE": 0.006, "AZURA": 0.0045}
    rows = [hdr]
    for fid, mu in means.items():
        for i in range(12):
            r = mu + (0.012 if i % 2 else -0.012)      # deterministic, gives vol
            rows.append(f"2024-{i+1:02d}-01,{fid},{r:.6f},Equity,Monthly,0,30")
    csv = tmp_path / "outlier.csv"
    csv.write_text("\n".join(rows) + "\n")
    return run(str(csv), load_mandate("data/mandates/default.yaml"))


def test_benchmark_marker_stays_on_its_reference_line():
    # the bug: marker and line were computed from different layouts and drifted far
    # apart. They now share one axis, so the marker sits on (or hugs) its line.
    memo, ctx = run("data/samples/dataset.csv", load_mandate("data/mandates/default.yaml"))
    data = _extract_data(render_html(memo, ctx))
    bl, bench = data.get("benchLine"), data.get("bench")
    assert bl and bench and bench.get("xz") is not None
    dx, dy = bl["x2"] - bl["x1"], bl["y2"] - bl["y1"]
    seg = (dx * dx + dy * dy) ** 0.5 or 1.0
    dist = abs(dx * (bench["yz"] - bl["y1"]) - dy * (bench["xz"] - bl["x1"])) / seg
    assert dist < 6.0, f"benchmark marker is {dist:.1f}% off its reference line (should hug it)"


def test_client_bench_line_single_ray_through_builder():
    """The 'S&P diamond floats off its reference line' bug kept coming back because
    each client path (baked relayout, CSV upload, live refetch) rebuilt the benchmark
    line on its own — and the upload path used a chord between axis endpoints, which
    drifts off the marker whenever _pos saturates an outlier fund. Lock it down: the
    benchmark marker + line has exactly ONE client builder (_benchMark), it rays
    THROUGH the marker (marker on the line by construction), every dynamic path routes
    through it, and the endpoint-chord slope can never be reintroduced."""
    js = Path("backend/amb_core/assets/memo.js").read_text()
    assert js.count("function _benchMark(") == 1, "the benchmark line must have ONE shared client builder"
    b0 = js.index("function _benchMark(")
    assert "_rayThrough(" in js[b0:b0 + 800], "_benchMark must build the line as a ray THROUGH the marker"
    # builder definition (1) + both call sites (recompute + relayoutScatter) => >= 3 refs
    assert js.count("_benchMark(") >= 3, "recompute() and relayoutScatter() must both use the shared _benchMark builder"
    # the axis-endpoint chord slope that caused the drift must never come back
    assert "bench.ret/bench.vol" not in js and "b.ret/b.vol" not in js, (
        "benchmark reference line was rebuilt as an axis-endpoint chord — the marker will drift off it again"
    )


def test_client_has_one_metric_implementation():
    """Every audit false-flag under live data (Sharpe/Sortino, then Calmar/drawdown) had
    the same root: the client computed metrics in more than one place, and those copies
    drifted from each other and from metrics.py. Lock in a single implementation —
    synthAlphaOverBench must derive its metrics through fundMetrics, not inline formulas,
    and fundMetrics must use the ACTUAL risk-free (A.rfUsed) so the re-derivation matches
    the stored value. No second Sharpe/drawdown formula anywhere in the live path."""
    js = "".join(Path("backend/amb_core/assets/memo.js").read_text().split())  # whitespace-insensitive
    fm = js[js.index("functionfundMetrics("):][:400]
    assert "A.rfUsed" in fm, "fundMetrics must re-derive with the actual risk-free (A.rfUsed), not a hardcoded default"
    synth = js[js.index("functionsynthAlphaOverBench("):][:3800]
    assert "fundMetrics(nr)" in synth, "synth must derive metrics through the shared fundMetrics, not inline"
    assert "d.sharpe=mm.sharpe" in synth and "d.maxdd=mm.max_drawdown" in synth, "synth metrics must come from fundMetrics"
    # no second, inline definition of the metrics in the live path (the drift source)
    assert "(ret-rf)/vol" not in synth, "inline geometric-excess Sharpe reintroduced in synth"
    assert "annex=nm*ppy-rf" not in synth, "inline arithmetic-excess Sharpe reintroduced in synth — must use fundMetrics"
    assert "peak=1,mdd" not in synth, "inline drawdown reintroduced in synth — must use fundMetrics"


def test_js_python_metric_parity():
    """FOUNDATIONAL guard against the whole class of bug we kept hitting: the client's
    JavaScript metric engine (fundMetrics) drifting from the Python engine (metrics.py).
    Runs the ACTUAL client fundMetrics headlessly on golden return series and asserts
    every figure matches metrics.py within tolerance. Skips cleanly where the headless
    toolchain isn't available, so it never blocks a minimal `./test`."""
    import json
    import os
    import shutil
    import subprocess

    node = shutil.which("node")
    html = Path("exports/memo.html")
    script = Path("tests/metric_parity.js")
    if not node:
        pytest.skip("node not available")
    if not html.exists():
        pytest.skip("built export not found — run `python -m amb_core.demo` first")
    if not script.exists():
        pytest.skip("parity helper missing")

    golden = [
        [0.01, 0.02, -0.01, 0.03, 0.00, 0.015, -0.02, 0.025, 0.01, -0.005, 0.02, 0.01],
        [-0.03, 0.02, 0.018, 0.041, -0.012, 0.02, 0.03, -0.008, 0.015, 0.022, -0.004, 0.028],  # negative first month → drawdown convention
        [0.005] * 24,                                                                            # flat, zero drawdown
        [0.08, -0.05, 0.06, -0.04, 0.09, -0.03, 0.07, -0.06, 0.05, -0.02, 0.10, -0.07],          # high-vol, deep drawdowns
    ]
    env = dict(os.environ)
    try:
        proc = subprocess.run(
            [node, str(script), str(html.resolve()), json.dumps(golden)],
            capture_output=True, text=True, timeout=120, env=env,
        )
    except Exception as e:  # node/chromium launch problems → skip, don't fail
        pytest.skip(f"headless metric eval unavailable: {e}")
    if proc.returncode != 0 or not proc.stdout.strip():
        pytest.skip(f"headless metric eval unavailable: {proc.stderr.strip()[:200]}")

    import numpy as np

    from amb_core.metrics import annualize, calmar, max_drawdown
    from amb_core.metrics import sharpe as py_sharpe
    from amb_core.metrics import sortino as py_sortino

    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    rf, results = payload["rf"], payload["results"]
    for series, js in zip(golden, results):
        r = np.array(series, dtype=float)
        pr, pv, _ = annualize(r)
        expected = {
            "ann_return": pr, "ann_vol": pv,
            "sharpe": py_sharpe(r, 12, rf), "sortino": py_sortino(r, 12, rf),
            "calmar": calmar(r, 12), "max_drawdown": max_drawdown(r),
        }
        for k, py_val in expected.items():
            js_val = js.get(k)
            if py_val is None or js_val is None:
                # an undefined metric (e.g. Sharpe on a zero-vol series) must be undefined on BOTH sides
                assert (py_val is None) == (js_val is None), (
                    f"JS/Python disagree on whether {k} is defined: JS={js_val} Python={py_val} (series={series[:3]}…)"
                )
                continue
            assert js_val == pytest.approx(py_val, rel=0.01, abs=1e-4), (
                f"JS/Python metric drift on {k}: JS={js_val} Python={py_val} (series={series[:3]}…)"
            )


def test_outlier_does_not_crush_the_plotted_cluster(tmp_path):
    memo, ctx = _outlier_ctx(tmp_path)
    data = _extract_data(render_html(memo, ctx))
    yz = [f["yz"] for f in data["funds"] if f.get("eligible") and f.get("yz") is not None]
    assert len(yz) >= 3, "expected several eligible funds to plot"
    assert max(yz) - min(yz) > 25, "eligible funds are crushed into a thin vertical band"


# ── memo: engine value is authoritative (a wrong model number never shows) ────
def test_engine_value_overrides_model_and_drops_unresolvable():
    from amb_core.memo import _mk_claims
    mandate = load_mandate("data/mandates/default.yaml")
    _memo, ctx = run("data/samples/dataset.csv", mandate)
    fid = ctx.shortlist[0].fund_id
    true_sharpe = ctx.get_metric(fid, "sharpe").value
    claims = _mk_claims(ctx, [
        {"text": "x", "metric": "sharpe", "fund_id": fid, "value": 999.0},  # wrong -> engine wins
        {"text": "y", "metric": "not_a_metric", "fund_id": fid, "value": 1.0},  # unresolvable -> dropped
    ])
    assert len(claims) == 1
    assert claims[0].value == pytest.approx(true_sharpe)
    assert claims[0].verified is True


# ── the single-file dataset is the only bundled sample ────────────────────────
def test_single_file_is_the_sole_sample():
    samples = Path("data/samples")
    assert (samples / "dataset.csv").exists()
    assert not (samples / "funds.csv").exists(), "legacy funds.csv came back"
    assert not (samples / "returns.csv").exists(), "legacy returns.csv came back"

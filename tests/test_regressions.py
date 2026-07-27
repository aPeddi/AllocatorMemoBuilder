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

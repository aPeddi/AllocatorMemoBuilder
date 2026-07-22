"""Golden-value tests for the metrics engine. These pin the conventions."""
import numpy as np
import pytest

from amb_core import metrics as M


def test_max_drawdown_known_path():
    r = np.array([0.10, -0.50, 0.10])  # wealth 1.1 -> 0.55 -> 0.605; trough -50%
    assert M.max_drawdown(r) == pytest.approx(-0.50, abs=1e-9)


def test_beta_and_correlation_perfect():
    b = np.array([0.01, -0.02, 0.03, 0.00, 0.015])
    r = 2.0 * b
    assert M.beta(r, b) == pytest.approx(2.0, abs=1e-9)
    assert M.correlation(r, b) == pytest.approx(1.0, abs=1e-9)
    assert M.tracking_error(r, b, 12) == pytest.approx(np.std(r - b, ddof=1) * np.sqrt(12), abs=1e-12)


def test_hit_rate():
    r = np.array([0.10, -0.10, 0.20, 0.00])  # zero is not a hit
    assert M.hit_rate(r) == pytest.approx(0.5)


def test_zero_vol_gives_no_sharpe():
    r = np.array([0.01, 0.01, 0.01, 0.01])
    assert M.ann_vol(r, 12) == pytest.approx(0.0)
    assert M.sharpe(r, 12, 0.02) is None  # undefined, not inf


def test_ann_return_flat_is_zero():
    r = np.zeros(12)
    assert M.ann_return(r, 12) == pytest.approx(0.0)


def test_ann_return_geometric():
    r = np.array([0.10, 0.10])  # 1.1*1.1 = 1.21, over 2 periods, N=2 -> annualize to 1yr
    # growth**(N/n)-1 = 1.21**(2/2)-1 = 0.21
    assert M.ann_return(r, 2) == pytest.approx(0.21, abs=1e-9)


def test_sortino_only_penalizes_downside():
    # all-positive excess -> downside deviation ~0 -> sortino undefined or huge; guard None
    r = np.array([0.05, 0.05, 0.05])
    assert M.sortino(r, 12, 0.0) is None  # no downside dispersion


def test_compute_bundle_keys():
    r = np.array([0.02, -0.01, 0.03, 0.00, 0.015, -0.02])
    b = np.array([0.01, -0.005, 0.02, 0.00, 0.01, -0.01])
    out = M.compute(r, b, 12, 0.02)
    assert set(out.keys()) == set(M.METRIC_KEYS)
    assert out["beta"] is not None and out["correlation"] is not None


def test_sharpe_sign_positive_when_beating_rf():
    r = np.array([0.03, 0.02, 0.04, 0.03, 0.02])  # well above rf/12
    assert M.sharpe(r, 12, 0.02) > 0

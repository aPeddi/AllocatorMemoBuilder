import pytest

from amb_core.ingest import load_dataset, normalize_return


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("5%", 0.05),
        ("2.3%", 0.023),
        ("0.05", 0.05),
        ("5", 0.05),        # bare percent point
        ("-0.02", -0.02),
        ("1,234", None) if False else ("-1.5%", -0.015),
        ("", None),
        ("n/a", None),
        (0.012, 0.012),
    ],
)
def test_normalize_return(raw, expected):
    got = normalize_return(raw)
    if expected is None:
        assert got is None
    else:
        assert got == pytest.approx(expected)


def test_dataset_quarantines_bad_rows():
    funds, series, quarantined = load_dataset("data/samples/dataset.csv")
    assert len(funds) == 9                  # 9 funds (metadata, one per fund_id)
    assert len(series) == 9                 # 9 return series
    assert len(quarantined) == 3            # the 3 deliberately messy rows
    for s in series.values():
        assert s.frequency == "monthly"
        assert s.periods_per_year == 12
        assert len(s.points) == 36
        assert s.source_hash                # provenance hash present

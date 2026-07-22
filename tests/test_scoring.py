from amb_core.models import Fund, Mandate, MandateConstraint
from amb_core.scoring import apply_constraints, build_shortlist


def _fund(fid, strat):
    return Fund(fund_id=fid, name=fid, strategy=strat)


def test_constraints_filter_strategy_and_metric():
    funds = [_fund("A", "Venture"), _fund("B", "Global Macro"), _fund("C", "Digital Assets")]
    metrics = {"A": {"ann_vol": 0.2}, "B": {"ann_vol": 0.2}, "C": {"ann_vol": 0.5}}
    mandate = Mandate(
        name="t",
        constraints=[
            MandateConstraint(field="strategy", op="not_in", value=["Venture", "Real Assets"]),
            MandateConstraint(field="ann_vol", op="<=", value=0.35),
        ],
    )
    eligible = apply_constraints(funds, metrics, mandate)
    assert eligible == ["B"]  # A excluded by strategy, C by vol


def test_shortlist_orders_by_score_desc():
    funds = [_fund("HI", "Macro"), _fund("LO", "Macro")]
    metrics = {
        "HI": {"sharpe": 2.0, "sortino": 2.5, "calmar": 1.5, "ann_return": 0.2, "max_drawdown": -0.1, "ann_vol": 0.1},
        "LO": {"sharpe": 0.2, "sortino": 0.3, "calmar": 0.2, "ann_return": 0.03, "max_drawdown": -0.3, "ann_vol": 0.25},
    }
    mandate = Mandate(name="t", top_n=5)
    sl = build_shortlist(funds, metrics, mandate)
    assert [e.fund_id for e in sl] == ["HI", "LO"]
    assert sl[0].rank == 1 and sl[0].score >= sl[1].score

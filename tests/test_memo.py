import pytest

from amb_core.memo import generate, template_claims_provider


def test_sample_shortlist_excludes_illiquid_and_high_vol(sample_run):
    memo, ctx = sample_run
    ids = ctx.shortlist_ids()
    assert "VEN" not in ids and "RA" not in ids  # excluded by strategy
    assert "DA" not in ids                        # excluded by vol cap
    assert len(memo.shortlist) == 5               # top_n of the 6 eligible


def test_template_claims_all_verify(sample_run):
    memo, ctx = sample_run
    a = memo.audit
    assert a["claim_count"] > 0
    # template asserts exact engine values -> everything must verify
    assert a["verified_count"] == a["claim_count"]


def test_wrong_value_is_reconciled_to_engine(sample_run):
    """Engine-authoritative claims: a model can't corrupt a number it never sets.
    A bogus asserted value is reconciled to the engine's true value (never shown),
    and a claim citing a metric the engine can't produce is dropped, not displayed."""
    _memo, ctx = sample_run
    top = ctx.shortlist[0].fund_id
    true_sharpe = ctx.get_metric(top, "sharpe").value

    def bad_provider(_ctx):
        return {
            "recommendation": "x",
            "funds": [
                {
                    "fund_id": top,
                    "paragraph": "wrong",
                    "claims": [
                        {"text": "bogus", "metric": "sharpe", "fund_id": top, "value": 999.0},
                        {"text": "ghost", "metric": "not_a_metric", "fund_id": top, "value": 1.0},
                    ],
                }
            ],
            "_model": "test",
        }

    memo = generate(ctx, bad_provider)
    claims = memo.audit["claims"]
    # the bogus 999.0 never enters the memo — the engine value is displayed instead
    assert not any(c["value"] == 999.0 for c in claims)
    sharpe_claims = [c for c in claims if c["fund_id"] == top and c["metric"] == "sharpe"]
    assert sharpe_claims and sharpe_claims[0]["value"] == pytest.approx(true_sharpe)
    assert all(c["verified"] for c in sharpe_claims)
    # the unresolvable metric was dropped, not shown as unverified
    assert not any(c["metric"] == "not_a_metric" for c in claims)
    # every claim that made it into the memo is verified by construction
    assert memo.audit["verified_count"] == memo.audit["claim_count"]

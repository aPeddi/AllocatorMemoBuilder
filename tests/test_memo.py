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


def test_wrong_value_fails_verification(sample_run):
    _memo, ctx = sample_run
    top = ctx.shortlist[0].fund_id

    def bad_provider(_ctx):
        return {
            "recommendation": "x",
            "funds": [
                {
                    "fund_id": top,
                    "paragraph": "wrong",
                    "claims": [{"text": "bogus", "metric": "sharpe", "fund_id": top, "value": 999.0}],
                }
            ],
            "_model": "test",
        }

    memo = generate(ctx, bad_provider)
    assert memo.audit["verified_count"] == 0
    assert memo.audit["unverified_count"] == 1

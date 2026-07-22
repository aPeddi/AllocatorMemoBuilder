import pytest

from amb_core.pipeline import load_mandate, run

SAMPLE_FUNDS = "data/samples/funds.csv"
SAMPLE_RETURNS = "data/samples/returns.csv"
MANDATE = "data/mandates/default.yaml"


@pytest.fixture(scope="session")
def sample_run():
    """Full deterministic pipeline on bundled sample data (template provider)."""
    mandate = load_mandate(MANDATE)
    memo, ctx = run(SAMPLE_FUNDS, SAMPLE_RETURNS, mandate)  # template provider
    return memo, ctx

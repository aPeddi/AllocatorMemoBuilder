import pytest

from amb_core.config import get_settings
from amb_core.pipeline import load_mandate, run


@pytest.fixture(autouse=True)
def _fresh_settings():
    """Clear the lru_cached settings around every test, so a test that sets an env
    var sees fresh config instead of the first-constructed (stale) singleton."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


SAMPLE_DATASET = "data/samples/dataset.csv"
MANDATE = "data/mandates/default.yaml"


@pytest.fixture(scope="session")
def sample_run():
    """Full deterministic pipeline on the bundled single-file sample (template provider)."""
    mandate = load_mandate(MANDATE)
    memo, ctx = run(SAMPLE_DATASET, mandate)  # single combined dataset · template provider
    return memo, ctx

import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def _clean_cache():
    """The rate limiters count in the cache; start and end every test with it empty."""
    cache.clear()
    yield
    cache.clear()

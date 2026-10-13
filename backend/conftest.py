import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def _clear_cache():
    """Throttle counters, revoked-JTI and used-OAuth-state entries live in the
    cache — start every test from an empty one."""
    cache.clear()
    yield
    cache.clear()

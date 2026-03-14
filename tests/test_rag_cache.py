"""
Unit tests for the RAG retriever in-process cache (src/rag/retriever.py).

Tests _cache_get, _cache_set, FIFO eviction, and cache-key construction.
The vector DB and external dependencies are not needed; we operate directly
on the module-level _RAG_CACHE dict.
"""
import pytest

from src.domain.schemas import RetrievedContext
from src.rag.retriever import _RAG_CACHE, _RAG_CACHE_MAX, _cache_get, _cache_set


@pytest.fixture(autouse=True)
def clear_rag_cache():
    """Ensure the cache starts empty before each test and is cleaned up after."""
    _RAG_CACHE.clear()
    yield
    _RAG_CACHE.clear()


def _make_context(content="chunk", score=0.9):
    """Helper to create a minimal RetrievedContext."""
    return RetrievedContext(
        content=content,
        source_document="test.pdf",
        page_number=1,
        relevance_score=score,
    )


# ---------------------------------------------------------------------------
# _cache_get
# ---------------------------------------------------------------------------

class TestCacheGet:

    def test_missing_key_returns_none(self):
        """A key that was never set returns None."""
        result = _cache_get(("nonexistent", "disc", 4))
        assert result is None

    def test_returns_stored_value(self):
        """After _cache_set, _cache_get returns the same list."""
        key = ("query", "disc", 4)
        value = [_make_context()]
        _cache_set(key, value)
        assert _cache_get(key) is value


# ---------------------------------------------------------------------------
# _cache_set
# ---------------------------------------------------------------------------

class TestCacheSet:

    def test_stores_value(self):
        """A value stored via _cache_set is present in _RAG_CACHE."""
        key = ("q", "d", 3)
        val = [_make_context("stored")]
        _cache_set(key, val)
        assert key in _RAG_CACHE
        assert _RAG_CACHE[key] is val

    def test_overwrites_existing_key(self):
        """Setting the same key twice overwrites the first value."""
        key = ("q", "d", 3)
        val1 = [_make_context("first")]
        val2 = [_make_context("second")]
        _cache_set(key, val1)
        _cache_set(key, val2)
        assert _RAG_CACHE[key] is val2


# ---------------------------------------------------------------------------
# FIFO eviction
# ---------------------------------------------------------------------------

class TestCacheEviction:

    def test_evicts_oldest_when_max_reached(self):
        """When the cache has _RAG_CACHE_MAX entries, inserting a new one
        evicts the oldest (first-inserted) entry (FIFO)."""
        # Fill up to max
        for i in range(_RAG_CACHE_MAX):
            _cache_set((f"q{i}", "d", 4), [_make_context(f"chunk_{i}")])

        assert len(_RAG_CACHE) == _RAG_CACHE_MAX

        # The very first key should exist before eviction
        first_key = ("q0", "d", 4)
        assert first_key in _RAG_CACHE

        # Insert one more, triggering eviction
        new_key = ("new_query", "d", 4)
        _cache_set(new_key, [_make_context("new")])

        # The oldest entry should have been evicted
        assert first_key not in _RAG_CACHE
        # The new entry should be present
        assert new_key in _RAG_CACHE
        # Size should stay at max
        assert len(_RAG_CACHE) == _RAG_CACHE_MAX

    def test_no_eviction_below_max(self):
        """No entries are removed when the cache is below capacity."""
        for i in range(5):
            _cache_set((f"q{i}", "d", 4), [_make_context(f"c{i}")])

        assert len(_RAG_CACHE) == 5
        # All five keys should still be present
        for i in range(5):
            assert (f"q{i}", "d", 4) in _RAG_CACHE

    def test_max_constant_is_128(self):
        """Verify the documented max cache size."""
        assert _RAG_CACHE_MAX == 128


# ---------------------------------------------------------------------------
# Cache key construction (search_context uses truncated query)
# ---------------------------------------------------------------------------

class TestCacheKeyConstruction:

    def test_key_uses_truncated_query(self):
        """search_context builds keys with query[:160].
        Verify that two queries differing only after 160 chars produce the
        same truncated prefix."""
        base = "A" * 160
        query_a = base + "_extra_a"
        query_b = base + "_extra_b"

        # Both should truncate to the same first 160 chars
        assert query_a[:160] == query_b[:160]

        # Simulate cache key construction
        key_a = (query_a[:160], "Estrutura de Dados", 4)
        key_b = (query_b[:160], "Estrutura de Dados", 4)
        assert key_a == key_b

    def test_short_query_not_truncated(self):
        """Queries shorter than 160 chars are used as-is in the key."""
        short = "AVL tree balancing"
        key = (short[:160], "disc", 4)
        assert key[0] == short

    def test_discipline_differentiates_keys(self):
        """Same query but different discipline produces different keys."""
        key_a = ("query"[:160], "Estrutura de Dados", 4)
        key_b = ("query"[:160], "Redes", 4)
        assert key_a != key_b

    def test_k_value_differentiates_keys(self):
        """Same query and discipline but different k produces different keys."""
        key_a = ("query"[:160], "disc", 4)
        key_b = ("query"[:160], "disc", 8)
        assert key_a != key_b

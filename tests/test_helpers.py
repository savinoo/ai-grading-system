"""
Unit tests for src/utils/helpers.py

Covers measure_time, get_api_semaphore, run_async, and save_uploaded_file.
All file-system and async operations are either mocked or self-contained.
No external services required.
"""
import asyncio
import logging
import os
from unittest.mock import MagicMock, patch

import pytest

from src.utils.helpers import (
    _api_semaphores,
    get_api_semaphore,
    measure_time,
    run_async,
    save_uploaded_file,
)

# ---------------------------------------------------------------------------
# measure_time
# ---------------------------------------------------------------------------

class TestMeasureTime:

    def test_yields_control(self):
        """The context manager must yield (allowing the body to execute)."""
        executed = False
        with measure_time("test_op"):
            executed = True
        assert executed

    def test_logs_start_and_end(self, caplog):
        """Start and completion messages are emitted at INFO level."""
        with caplog.at_level(logging.INFO, logger="src.utils.helpers"), measure_time("my_operation"):
            pass
        messages = caplog.text
        assert "my_operation" in messages

    def test_logs_even_on_exception(self, caplog):
        """Completion log is emitted even when the body raises."""
        with caplog.at_level(logging.INFO, logger="src.utils.helpers"), pytest.raises(ValueError):
            with measure_time("failing_op"):
                raise ValueError("boom")
        # The finally block should still log
        assert "failing_op" in caplog.text


# ---------------------------------------------------------------------------
# get_api_semaphore
# ---------------------------------------------------------------------------

class TestGetApiSemaphore:

    def test_returns_semaphore_instance(self):
        """Should return an asyncio.Semaphore."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            sem = get_api_semaphore(limit=5)
            assert isinstance(sem, asyncio.Semaphore)
        finally:
            loop.close()

    def test_respects_explicit_limit(self):
        """The semaphore internal counter reflects the provided limit."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Clear per-loop cache
            key = id(loop)
            _api_semaphores.pop(key, None)

            sem = get_api_semaphore(limit=3)
            # asyncio.Semaphore stores the value in _value
            assert sem._value == 3
        finally:
            loop.close()

    def test_returns_same_semaphore_for_same_loop(self):
        """Calling twice on the same loop returns the cached semaphore."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            key = id(loop)
            _api_semaphores.pop(key, None)

            sem1 = get_api_semaphore(limit=5)
            sem2 = get_api_semaphore(limit=5)
            assert sem1 is sem2
        finally:
            loop.close()

    def test_default_limit_from_env(self):
        """When limit is None, the env var API_CONCURRENCY is used (default 10)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            key = id(loop)
            _api_semaphores.pop(key, None)

            with patch.dict(os.environ, {"API_CONCURRENCY": "7"}):
                sem = get_api_semaphore()
                assert sem._value == 7
        finally:
            loop.close()


# ---------------------------------------------------------------------------
# run_async
# ---------------------------------------------------------------------------

class TestRunAsync:

    def test_executes_coroutine_and_returns_result(self):
        """run_async should drive a coroutine to completion and return its value."""

        async def add(a, b):
            return a + b

        result = run_async(add(3, 4))
        assert result == 7

    def test_propagates_exception(self):
        """Exceptions raised inside the coroutine should propagate."""

        async def failing():
            raise RuntimeError("async boom")

        with pytest.raises(RuntimeError, match="async boom"):
            run_async(failing())

    def test_works_with_await_chain(self):
        """Nested awaits resolve correctly."""

        async def inner():
            return 42

        async def outer():
            return await inner()

        assert run_async(outer()) == 42


# ---------------------------------------------------------------------------
# save_uploaded_file
# ---------------------------------------------------------------------------

class TestSaveUploadedFile:

    def test_creates_directory_and_writes_file(self, tmp_path):
        """File is saved to data/raw/<filename> and the path is returned."""
        mock_file = MagicMock()
        mock_file.name = "test_paper.pdf"
        mock_file.getbuffer.return_value = b"PDF content bytes"

        # Patch os.path and os.makedirs to use tmp_path
        raw_dir = str(tmp_path / "data" / "raw")
        expected_path = os.path.join(raw_dir, "test_paper.pdf")

        with patch("src.utils.helpers.os.path.exists", return_value=False), \
             patch("src.utils.helpers.os.makedirs") as mock_makedirs, \
             patch("src.utils.helpers.os.path.join", return_value=expected_path), \
             patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__ = MagicMock()
            mock_open.return_value.__exit__ = MagicMock(return_value=False)

            result = save_uploaded_file(mock_file)

            mock_makedirs.assert_called_once()
            assert result == expected_path

    def test_skips_mkdir_when_exists(self):
        """If data/raw already exists, os.makedirs is not called."""
        mock_file = MagicMock()
        mock_file.name = "paper.pdf"
        mock_file.getbuffer.return_value = b"bytes"

        with patch("src.utils.helpers.os.path.exists", return_value=True), \
             patch("src.utils.helpers.os.makedirs") as mock_makedirs, \
             patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__ = MagicMock()
            mock_open.return_value.__exit__ = MagicMock(return_value=False)

            save_uploaded_file(mock_file)

            mock_makedirs.assert_not_called()

    def test_returns_correct_path(self):
        """The returned path matches 'data/raw/<filename>'."""
        mock_file = MagicMock()
        mock_file.name = "my_exam.pdf"
        mock_file.getbuffer.return_value = b"data"

        with patch("src.utils.helpers.os.path.exists", return_value=True), \
             patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__ = MagicMock()
            mock_open.return_value.__exit__ = MagicMock(return_value=False)

            result = save_uploaded_file(mock_file)

            assert result == os.path.join("data/raw", "my_exam.pdf")

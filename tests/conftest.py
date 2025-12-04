"""Shared test fixtures for liq-core tests."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest


@pytest.fixture
def utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(UTC)


@pytest.fixture
def sample_timestamp() -> datetime:
    """Return a sample UTC timestamp for testing."""
    return datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)


@pytest.fixture
def sample_ohlcv() -> dict[str, Decimal]:
    """Return sample OHLCV data."""
    return {
        "open": Decimal("1.1000"),
        "high": Decimal("1.1050"),
        "low": Decimal("1.0950"),
        "close": Decimal("1.1025"),
        "volume": Decimal("10000"),
    }

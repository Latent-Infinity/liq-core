"""Tests for result data models."""

import pytest

from liq.core.results import BatchResult, FetchResult, UpdateResult


class TestFetchResult:
    """Tests for FetchResult dataclass."""

    def test_success_result(self) -> None:
        """Test creating a successful fetch result."""
        result = FetchResult(symbol="EUR_USD", success=True, count=5000)
        assert result.symbol == "EUR_USD"
        assert result.success is True
        assert result.count == 5000
        assert result.error is None

    def test_failure_result(self) -> None:
        """Test creating a failed fetch result."""
        result = FetchResult(symbol="EUR_USD", success=False, error="API error")
        assert result.symbol == "EUR_USD"
        assert result.success is False
        assert result.count is None
        assert result.error == "API error"

    def test_success_requires_count(self) -> None:
        """Test that success=True requires count."""
        with pytest.raises(ValueError, match="count is required"):
            FetchResult(symbol="EUR_USD", success=True)

    def test_failure_requires_error(self) -> None:
        """Test that success=False requires error."""
        with pytest.raises(ValueError, match="error is required"):
            FetchResult(symbol="EUR_USD", success=False)

    def test_immutable(self) -> None:
        """Test that FetchResult is immutable."""
        result = FetchResult(symbol="EUR_USD", success=True, count=5000)
        with pytest.raises(AttributeError):
            result.count = 6000  # type: ignore[misc]


class TestUpdateResult:
    """Tests for UpdateResult dataclass."""

    def test_success_result(self) -> None:
        """Test creating a successful update result."""
        result = UpdateResult(
            symbol="EUR_USD",
            success=True,
            gaps_filled=3,
            total_rows=50000,
        )
        assert result.symbol == "EUR_USD"
        assert result.success is True
        assert result.gaps_filled == 3
        assert result.total_rows == 50000
        assert result.error is None

    def test_failure_result(self) -> None:
        """Test creating a failed update result."""
        result = UpdateResult(symbol="EUR_USD", success=False, error="No data")
        assert result.symbol == "EUR_USD"
        assert result.success is False
        assert result.gaps_filled is None
        assert result.total_rows is None
        assert result.error == "No data"

    def test_success_requires_gaps_filled(self) -> None:
        """Test that success=True requires gaps_filled."""
        with pytest.raises(ValueError, match="gaps_filled is required"):
            UpdateResult(symbol="EUR_USD", success=True, total_rows=1000)

    def test_success_requires_total_rows(self) -> None:
        """Test that success=True requires total_rows."""
        with pytest.raises(ValueError, match="total_rows is required"):
            UpdateResult(symbol="EUR_USD", success=True, gaps_filled=3)

    def test_failure_requires_error(self) -> None:
        """Test that success=False requires error."""
        with pytest.raises(ValueError, match="error is required"):
            UpdateResult(symbol="EUR_USD", success=False)

    def test_immutable(self) -> None:
        """Test that UpdateResult is immutable."""
        result = UpdateResult(
            symbol="EUR_USD", success=True, gaps_filled=3, total_rows=50000
        )
        with pytest.raises(AttributeError):
            result.total_rows = 60000  # type: ignore[misc]


class TestBatchResult:
    """Tests for BatchResult dataclass."""

    def test_fetch_batch_result(self) -> None:
        """Test creating a batch result with fetch results."""
        results = [
            FetchResult(symbol="EUR_USD", success=True, count=5000),
            FetchResult(symbol="GBP_USD", success=True, count=4500),
            FetchResult(symbol="JPY_USD", success=False, error="Not found"),
        ]
        batch = BatchResult(total=3, succeeded=2, failed=1, results=results)

        assert batch.total == 3
        assert batch.succeeded == 2
        assert batch.failed == 1
        assert len(batch.results) == 3

    def test_update_batch_result(self) -> None:
        """Test creating a batch result with update results."""
        results = [
            UpdateResult(symbol="EUR_USD", success=True, gaps_filled=3, total_rows=50000),
            UpdateResult(symbol="GBP_USD", success=False, error="API error"),
        ]
        batch = BatchResult(total=2, succeeded=1, failed=1, results=results)

        assert batch.total == 2
        assert batch.succeeded == 1
        assert batch.failed == 1

    def test_success_rate(self) -> None:
        """Test success_rate property."""
        results = [
            FetchResult(symbol="EUR_USD", success=True, count=5000),
            FetchResult(symbol="GBP_USD", success=True, count=4500),
            FetchResult(symbol="JPY_USD", success=False, error="Not found"),
            FetchResult(symbol="CHF_USD", success=False, error="API error"),
        ]
        batch = BatchResult(total=4, succeeded=2, failed=2, results=results)
        assert batch.success_rate == 50.0

    def test_success_rate_empty(self) -> None:
        """Test success_rate with no results."""
        batch = BatchResult(total=0, succeeded=0, failed=0, results=[])
        assert batch.success_rate == 0.0

    def test_get_failures(self) -> None:
        """Test get_failures method."""
        results = [
            FetchResult(symbol="EUR_USD", success=True, count=5000),
            FetchResult(symbol="GBP_USD", success=False, error="Not found"),
            FetchResult(symbol="JPY_USD", success=False, error="API error"),
        ]
        batch = BatchResult(total=3, succeeded=1, failed=2, results=results)
        failures = batch.get_failures()

        assert len(failures) == 2
        assert all(not r.success for r in failures)

    def test_get_successes(self) -> None:
        """Test get_successes method."""
        results = [
            FetchResult(symbol="EUR_USD", success=True, count=5000),
            FetchResult(symbol="GBP_USD", success=True, count=4500),
            FetchResult(symbol="JPY_USD", success=False, error="Not found"),
        ]
        batch = BatchResult(total=3, succeeded=2, failed=1, results=results)
        successes = batch.get_successes()

        assert len(successes) == 2
        assert all(r.success for r in successes)

    def test_totals_must_match(self) -> None:
        """Test that total must equal succeeded + failed."""
        results = [FetchResult(symbol="EUR_USD", success=True, count=5000)]
        with pytest.raises(ValueError, match="total must equal"):
            BatchResult(total=2, succeeded=1, failed=0, results=results)

    def test_results_length_must_match_total(self) -> None:
        """Test that results length must equal total."""
        results = [
            FetchResult(symbol="EUR_USD", success=True, count=5000),
            FetchResult(symbol="GBP_USD", success=True, count=4500),
        ]
        with pytest.raises(ValueError, match="results length must equal"):
            BatchResult(total=3, succeeded=2, failed=1, results=results)

    def test_immutable(self) -> None:
        """Test that BatchResult is immutable."""
        results = [FetchResult(symbol="EUR_USD", success=True, count=5000)]
        batch = BatchResult(total=1, succeeded=1, failed=0, results=results)
        with pytest.raises(AttributeError):
            batch.total = 2  # type: ignore[misc]

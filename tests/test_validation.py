"""Tests for liq.core.validation module."""

from datetime import UTC, datetime

import pytest

from liq.core.validation import ValidationResult, is_timezone_aware


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_valid_result(self) -> None:
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []

    def test_invalid_result_with_errors(self) -> None:
        result = ValidationResult(
            is_valid=False, errors=["high < low", "volume < 0"], warnings=[]
        )
        assert result.is_valid is False
        assert len(result.errors) == 2
        assert "high < low" in result.errors

    def test_valid_result_with_warnings(self) -> None:
        result = ValidationResult(
            is_valid=True, errors=[], warnings=["price spike detected"]
        )
        assert result.is_valid is True
        assert len(result.warnings) == 1

    def test_result_immutable(self) -> None:
        """ValidationResult should be frozen (immutable)."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        with pytest.raises(AttributeError):
            result.is_valid = False  # type: ignore[misc]

    def test_result_equality(self) -> None:
        result1 = ValidationResult(is_valid=True, errors=[], warnings=[])
        result2 = ValidationResult(is_valid=True, errors=[], warnings=[])
        assert result1 == result2

    def test_result_with_multiple_errors_and_warnings(self) -> None:
        result = ValidationResult(
            is_valid=False,
            errors=["error1", "error2"],
            warnings=["warning1", "warning2"],
        )
        assert not result.is_valid
        assert len(result.errors) == 2
        assert len(result.warnings) == 2


class TestIsTimezoneAware:
    """Tests for is_timezone_aware helper function."""

    def test_utc_datetime_is_aware(self) -> None:
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)
        assert is_timezone_aware(dt) is True

    def test_naive_datetime_is_not_aware(self) -> None:
        dt = datetime(2024, 1, 15, 10, 30, 0)
        assert is_timezone_aware(dt) is False

    def test_now_utc_is_aware(self) -> None:
        dt = datetime.now(UTC)
        assert is_timezone_aware(dt) is True

    def test_now_without_tz_is_not_aware(self) -> None:
        dt = datetime.now()
        assert is_timezone_aware(dt) is False

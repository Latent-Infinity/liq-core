"""Tests for liq.core.bar module."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from liq.core.bar import Bar


class TestBarCreation:
    """Tests for Bar model creation."""

    def test_create_valid_bar(self, sample_timestamp: datetime) -> None:
        bar = Bar(
            timestamp=sample_timestamp,
            symbol="EUR_USD",
            open=Decimal("1.1000"),
            high=Decimal("1.1050"),
            low=Decimal("1.0950"),
            close=Decimal("1.1025"),
            volume=Decimal("10000"),
        )
        assert bar.symbol == "EUR_USD"
        assert bar.open == Decimal("1.1000")
        assert bar.high == Decimal("1.1050")
        assert bar.low == Decimal("1.0950")
        assert bar.close == Decimal("1.1025")
        assert bar.volume == Decimal("10000")

    def test_bar_timestamp_is_preserved(self, sample_timestamp: datetime) -> None:
        bar = Bar(
            timestamp=sample_timestamp,
            symbol="EUR_USD",
            open=Decimal("1.1000"),
            high=Decimal("1.1050"),
            low=Decimal("1.0950"),
            close=Decimal("1.1025"),
            volume=Decimal("10000"),
        )
        assert bar.timestamp == sample_timestamp
        assert bar.timestamp.tzinfo == UTC


class TestBarOHLCValidation:
    """Tests for OHLC constraint validation."""

    def test_rejects_high_less_than_low(self, sample_timestamp: datetime) -> None:
        with pytest.raises(ValidationError) as exc_info:
            Bar(
                timestamp=sample_timestamp,
                symbol="EUR_USD",
                open=Decimal("1.1000"),
                high=Decimal("1.0900"),  # High < Low
                low=Decimal("1.1000"),
                close=Decimal("1.0950"),
                volume=Decimal("10000"),
            )
        assert "high must be >= low" in str(exc_info.value).lower()

    def test_rejects_high_less_than_open(self, sample_timestamp: datetime) -> None:
        with pytest.raises(ValidationError) as exc_info:
            Bar(
                timestamp=sample_timestamp,
                symbol="EUR_USD",
                open=Decimal("1.1100"),  # Open > High
                high=Decimal("1.1000"),
                low=Decimal("1.0900"),
                close=Decimal("1.0950"),
                volume=Decimal("10000"),
            )
        assert "high must be >= open" in str(exc_info.value).lower()

    def test_rejects_high_less_than_close(self, sample_timestamp: datetime) -> None:
        with pytest.raises(ValidationError) as exc_info:
            Bar(
                timestamp=sample_timestamp,
                symbol="EUR_USD",
                open=Decimal("1.0950"),
                high=Decimal("1.1000"),
                low=Decimal("1.0900"),
                close=Decimal("1.1100"),  # Close > High
                volume=Decimal("10000"),
            )
        assert "high must be >= close" in str(exc_info.value).lower()

    def test_rejects_low_greater_than_open(self, sample_timestamp: datetime) -> None:
        with pytest.raises(ValidationError) as exc_info:
            Bar(
                timestamp=sample_timestamp,
                symbol="EUR_USD",
                open=Decimal("1.0800"),  # Open < Low
                high=Decimal("1.1000"),
                low=Decimal("1.0900"),
                close=Decimal("1.0950"),
                volume=Decimal("10000"),
            )
        assert "low must be <= open" in str(exc_info.value).lower()

    def test_rejects_low_greater_than_close(self, sample_timestamp: datetime) -> None:
        with pytest.raises(ValidationError) as exc_info:
            Bar(
                timestamp=sample_timestamp,
                symbol="EUR_USD",
                open=Decimal("1.0950"),
                high=Decimal("1.1000"),
                low=Decimal("1.0900"),
                close=Decimal("1.0800"),  # Close < Low
                volume=Decimal("10000"),
            )
        assert "low must be <= close" in str(exc_info.value).lower()

    def test_accepts_high_equals_low(self, sample_timestamp: datetime) -> None:
        """Doji candle where high == low is valid."""
        bar = Bar(
            timestamp=sample_timestamp,
            symbol="EUR_USD",
            open=Decimal("1.1000"),
            high=Decimal("1.1000"),
            low=Decimal("1.1000"),
            close=Decimal("1.1000"),
            volume=Decimal("0"),
        )
        assert bar.high == bar.low


class TestBarVolumeValidation:
    """Tests for volume validation."""

    def test_accepts_zero_volume(self, sample_timestamp: datetime) -> None:
        bar = Bar(
            timestamp=sample_timestamp,
            symbol="EUR_USD",
            open=Decimal("1.1000"),
            high=Decimal("1.1050"),
            low=Decimal("1.0950"),
            close=Decimal("1.1025"),
            volume=Decimal("0"),
        )
        assert bar.volume == Decimal("0")

    def test_rejects_negative_volume(self, sample_timestamp: datetime) -> None:
        with pytest.raises(ValidationError) as exc_info:
            Bar(
                timestamp=sample_timestamp,
                symbol="EUR_USD",
                open=Decimal("1.1000"),
                high=Decimal("1.1050"),
                low=Decimal("1.0950"),
                close=Decimal("1.1025"),
                volume=Decimal("-100"),
            )
        assert "volume" in str(exc_info.value).lower()

    def test_rejects_non_positive_prices(self, sample_timestamp: datetime) -> None:
        with pytest.raises(ValidationError):
            Bar(
                timestamp=sample_timestamp,
                symbol="EUR_USD",
                open=Decimal("0"),
                high=Decimal("1.1050"),
                low=Decimal("1.0950"),
                close=Decimal("1.1025"),
                volume=Decimal("10000"),
            )
        with pytest.raises(ValidationError):
            Bar(
                timestamp=sample_timestamp,
                symbol="EUR_USD",
                open=Decimal("1.1000"),
                high=Decimal("-1.1050"),
                low=Decimal("1.0950"),
                close=Decimal("1.1025"),
                volume=Decimal("10000"),
            )


class TestBarTimezoneValidation:
    """Tests for timezone validation."""

    def test_rejects_naive_datetime(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            Bar(
                timestamp=datetime(2024, 1, 15, 10, 30, 0),  # No timezone
                symbol="EUR_USD",
                open=Decimal("1.1000"),
                high=Decimal("1.1050"),
                low=Decimal("1.0950"),
                close=Decimal("1.1025"),
                volume=Decimal("10000"),
            )
        assert "timezone" in str(exc_info.value).lower()

    def test_accepts_utc_datetime(self, sample_timestamp: datetime) -> None:
        bar = Bar(
            timestamp=sample_timestamp,
            symbol="EUR_USD",
            open=Decimal("1.1000"),
            high=Decimal("1.1050"),
            low=Decimal("1.0950"),
            close=Decimal("1.1025"),
            volume=Decimal("10000"),
        )
        assert bar.timestamp.tzinfo is not None

    def test_rejects_invalid_symbol(self, sample_timestamp: datetime) -> None:
        with pytest.raises(ValidationError):
            Bar(
                timestamp=sample_timestamp,
                symbol="eur/usd",
                open=Decimal("1.1000"),
                high=Decimal("1.1050"),
                low=Decimal("1.0950"),
                close=Decimal("1.1025"),
                volume=Decimal("10000"),
            )


class TestBarDerivedFields:
    """Tests for computed derived fields."""

    def test_midrange_calculation(self, sample_timestamp: datetime) -> None:
        bar = Bar(
            timestamp=sample_timestamp,
            symbol="EUR_USD",
            open=Decimal("1.1000"),
            high=Decimal("1.1100"),
            low=Decimal("1.0900"),
            close=Decimal("1.1025"),
            volume=Decimal("10000"),
        )
        assert bar.midrange == Decimal("1.1000")

    def test_range_calculation(self, sample_timestamp: datetime) -> None:
        bar = Bar(
            timestamp=sample_timestamp,
            symbol="EUR_USD",
            open=Decimal("1.1000"),
            high=Decimal("1.1100"),
            low=Decimal("1.0900"),
            close=Decimal("1.1025"),
            volume=Decimal("10000"),
        )
        assert bar.range == Decimal("0.0200")

    def test_derived_fields_with_zero_range(self, sample_timestamp: datetime) -> None:
        """Doji candle has zero range."""
        bar = Bar(
            timestamp=sample_timestamp,
            symbol="EUR_USD",
            open=Decimal("1.1000"),
            high=Decimal("1.1000"),
            low=Decimal("1.1000"),
            close=Decimal("1.1000"),
            volume=Decimal("0"),
        )
        assert bar.midrange == Decimal("1.1000")
        assert bar.range == Decimal("0")


class TestBarImmutability:
    """Tests for Bar immutability (frozen model)."""

    def test_bar_is_frozen(self, sample_timestamp: datetime) -> None:
        bar = Bar(
            timestamp=sample_timestamp,
            symbol="EUR_USD",
            open=Decimal("1.1000"),
            high=Decimal("1.1050"),
            low=Decimal("1.0950"),
            close=Decimal("1.1025"),
            volume=Decimal("10000"),
        )
        with pytest.raises(ValidationError):
            bar.symbol = "USD_JPY"  # type: ignore[misc]


class TestBarSerialization:
    """Tests for Bar serialization."""

    def test_json_serialization(self, sample_timestamp: datetime) -> None:
        bar = Bar(
            timestamp=sample_timestamp,
            symbol="EUR_USD",
            open=Decimal("1.1000"),
            high=Decimal("1.1050"),
            low=Decimal("1.0950"),
            close=Decimal("1.1025"),
            volume=Decimal("10000"),
        )
        json_str = bar.model_dump_json()
        assert "EUR_USD" in json_str
        assert "1.1000" in json_str

    def test_json_roundtrip(self, sample_timestamp: datetime) -> None:
        bar = Bar(
            timestamp=sample_timestamp,
            symbol="EUR_USD",
            open=Decimal("1.1000"),
            high=Decimal("1.1050"),
            low=Decimal("1.0950"),
            close=Decimal("1.1025"),
            volume=Decimal("10000"),
        )
        json_str = bar.model_dump_json()
        bar2 = Bar.model_validate_json(json_str)
        assert bar.symbol == bar2.symbol
        assert bar.open == bar2.open
        assert bar.high == bar2.high
        assert bar.low == bar2.low
        assert bar.close == bar2.close
        assert bar.volume == bar2.volume

    def test_dict_serialization(self, sample_timestamp: datetime) -> None:
        bar = Bar(
            timestamp=sample_timestamp,
            symbol="EUR_USD",
            open=Decimal("1.1000"),
            high=Decimal("1.1050"),
            low=Decimal("1.0950"),
            close=Decimal("1.1025"),
            volume=Decimal("10000"),
        )
        data = bar.model_dump()
        assert data["symbol"] == "EUR_USD"
        assert "open" in data


class TestBarPropertyBased:
    """Property-based tests using Hypothesis."""

    @given(
        high=st.decimals(min_value=1, max_value=1000, places=4, allow_nan=False, allow_infinity=False),
        low=st.decimals(min_value=1, max_value=1000, places=4, allow_nan=False, allow_infinity=False),
    )
    def test_midrange_is_between_high_and_low(
        self, high: Decimal, low: Decimal
    ) -> None:
        """Property: midrange should always be between low and high."""
        if high < low:
            high, low = low, high  # Swap to make valid

        # Ensure open and close are within range
        open_price = (high + low) / 2
        close_price = (high + low) / 2

        bar = Bar(
            timestamp=datetime(2024, 1, 15, tzinfo=UTC),
            symbol="TEST",
            open=open_price,
            high=high,
            low=low,
            close=close_price,
            volume=Decimal("100"),
        )

        assert bar.midrange >= bar.low
        assert bar.midrange <= bar.high

    @given(
        volume=st.decimals(min_value=0, max_value=1_000_000, places=2, allow_nan=False, allow_infinity=False)
    )
    def test_volume_always_non_negative(self, volume: Decimal) -> None:
        """Property: volume must be >= 0."""
        bar = Bar(
            timestamp=datetime(2024, 1, 15, tzinfo=UTC),
            symbol="TEST",
            open=Decimal("100"),
            high=Decimal("110"),
            low=Decimal("90"),
            close=Decimal("105"),
            volume=volume,
        )
        assert bar.volume >= 0

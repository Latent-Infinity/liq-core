"""Tests for liq.core.quote module."""

from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from liq.core.quote import Quote


class TestQuoteCreation:
    """Tests for Quote model creation."""

    def test_create_valid_quote(self, sample_timestamp: datetime) -> None:
        quote = Quote(
            symbol="EUR_USD",
            timestamp=sample_timestamp,
            bid=Decimal("1.0990"),
            ask=Decimal("1.1000"),
            bid_size=Decimal("1000000"),
            ask_size=Decimal("1000000"),
        )
        assert quote.symbol == "EUR_USD"
        assert quote.bid == Decimal("1.0990")
        assert quote.ask == Decimal("1.1000")

    def test_quote_timestamp_preserved(self, sample_timestamp: datetime) -> None:
        quote = Quote(
            symbol="BTC-USD",
            timestamp=sample_timestamp,
            bid=Decimal("50000"),
            ask=Decimal("50010"),
            bid_size=Decimal("10"),
            ask_size=Decimal("10"),
        )
        assert quote.timestamp == sample_timestamp


class TestQuoteValidation:
    """Tests for Quote validation."""

    def test_rejects_naive_datetime(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            Quote(
                symbol="EUR_USD",
                timestamp=datetime(2024, 1, 15),  # No timezone
                bid=Decimal("1.0990"),
                ask=Decimal("1.1000"),
                bid_size=Decimal("1000000"),
                ask_size=Decimal("1000000"),
            )
        assert "timezone" in str(exc_info.value).lower()

    def test_accepts_bid_equal_to_ask(self, sample_timestamp: datetime) -> None:
        """Zero spread is valid (e.g., no liquidity)."""
        quote = Quote(
            symbol="EUR_USD",
            timestamp=sample_timestamp,
            bid=Decimal("1.1000"),
            ask=Decimal("1.1000"),
            bid_size=Decimal("1000000"),
            ask_size=Decimal("1000000"),
        )
        assert quote.bid == quote.ask

    def test_rejects_negative_bid_size(self, sample_timestamp: datetime) -> None:
        with pytest.raises(ValidationError):
            Quote(
                symbol="EUR_USD",
                timestamp=sample_timestamp,
                bid=Decimal("1.0990"),
                ask=Decimal("1.1000"),
                bid_size=Decimal("-100"),
                ask_size=Decimal("1000000"),
            )

    def test_rejects_negative_ask_size(self, sample_timestamp: datetime) -> None:
        with pytest.raises(ValidationError):
            Quote(
                symbol="EUR_USD",
                timestamp=sample_timestamp,
                bid=Decimal("1.0990"),
                ask=Decimal("1.1000"),
                bid_size=Decimal("1000000"),
                ask_size=Decimal("-100"),
            )

    def test_rejects_negative_prices(self, sample_timestamp: datetime) -> None:
        with pytest.raises(ValidationError):
            Quote(
                symbol="EUR_USD",
                timestamp=sample_timestamp,
                bid=Decimal("-1.0990"),
                ask=Decimal("1.1000"),
                bid_size=Decimal("1000000"),
                ask_size=Decimal("1000000"),
            )
        with pytest.raises(ValidationError):
            Quote(
                symbol="EUR_USD",
                timestamp=sample_timestamp,
                bid=Decimal("1.0990"),
                ask=Decimal("0"),
                bid_size=Decimal("1000000"),
                ask_size=Decimal("1000000"),
            )

    def test_rejects_crossed_market(self, sample_timestamp: datetime) -> None:
        with pytest.raises(ValidationError):
            Quote(
                symbol="EUR_USD",
                timestamp=sample_timestamp,
                bid=Decimal("1.1010"),
                ask=Decimal("1.1000"),
                bid_size=Decimal("1000000"),
                ask_size=Decimal("1000000"),
            )

    def test_rejects_invalid_symbol(self, sample_timestamp: datetime) -> None:
        with pytest.raises(ValidationError):
            Quote(
                symbol="eur/usd",
                timestamp=sample_timestamp,
                bid=Decimal("1.0990"),
                ask=Decimal("1.1000"),
                bid_size=Decimal("1000000"),
                ask_size=Decimal("1000000"),
            )


class TestQuoteDerivedFields:
    """Tests for Quote computed properties."""

    def test_mid_calculation(self, sample_timestamp: datetime) -> None:
        quote = Quote(
            symbol="EUR_USD",
            timestamp=sample_timestamp,
            bid=Decimal("1.0990"),
            ask=Decimal("1.1010"),
            bid_size=Decimal("1000000"),
            ask_size=Decimal("1000000"),
        )
        assert quote.mid == Decimal("1.1000")

    def test_spread_calculation(self, sample_timestamp: datetime) -> None:
        quote = Quote(
            symbol="EUR_USD",
            timestamp=sample_timestamp,
            bid=Decimal("1.0990"),
            ask=Decimal("1.1010"),
            bid_size=Decimal("1000000"),
            ask_size=Decimal("1000000"),
        )
        assert quote.spread == Decimal("0.0020")

    def test_spread_bps_calculation(self, sample_timestamp: datetime) -> None:
        quote = Quote(
            symbol="EUR_USD",
            timestamp=sample_timestamp,
            bid=Decimal("1.0990"),
            ask=Decimal("1.1010"),
            bid_size=Decimal("1000000"),
            ask_size=Decimal("1000000"),
        )
        # spread_bps = (0.0020 / 1.1000) * 10000 ≈ 18.18
        expected = (Decimal("0.0020") / Decimal("1.1000")) * 10000
        assert abs(quote.spread_bps - expected) < Decimal("0.01")

    def test_zero_spread(self, sample_timestamp: datetime) -> None:
        quote = Quote(
            symbol="EUR_USD",
            timestamp=sample_timestamp,
            bid=Decimal("1.1000"),
            ask=Decimal("1.1000"),
            bid_size=Decimal("1000000"),
            ask_size=Decimal("1000000"),
        )
        assert quote.spread == Decimal("0")
        assert quote.spread_bps == Decimal("0")


class TestQuoteSerialization:
    """Tests for Quote serialization."""

    def test_json_roundtrip(self, sample_timestamp: datetime) -> None:
        quote = Quote(
            symbol="EUR_USD",
            timestamp=sample_timestamp,
            bid=Decimal("1.0990"),
            ask=Decimal("1.1000"),
            bid_size=Decimal("1000000"),
            ask_size=Decimal("1000000"),
        )
        json_str = quote.model_dump_json()
        quote2 = Quote.model_validate_json(json_str)
        assert quote.symbol == quote2.symbol
        assert quote.bid == quote2.bid
        assert quote.ask == quote2.ask

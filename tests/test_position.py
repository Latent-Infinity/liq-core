"""Tests for liq.core.position module."""

from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from liq.core.position import Position


class TestPositionCreation:
    """Tests for Position model creation."""

    def test_create_long_position(self, sample_timestamp: datetime) -> None:
        position = Position(
            symbol="EUR_USD",
            quantity=Decimal("10000"),
            average_price=Decimal("1.1000"),
            realized_pnl=Decimal("0"),
            timestamp=sample_timestamp,
        )
        assert position.symbol == "EUR_USD"
        assert position.quantity == Decimal("10000")
        assert position.average_price == Decimal("1.1000")
        assert position.realized_pnl == Decimal("0")

    def test_create_short_position(self, sample_timestamp: datetime) -> None:
        position = Position(
            symbol="EUR_USD",
            quantity=Decimal("-10000"),
            average_price=Decimal("1.1000"),
            realized_pnl=Decimal("0"),
            timestamp=sample_timestamp,
        )
        assert position.quantity == Decimal("-10000")

    def test_create_flat_position(self, sample_timestamp: datetime) -> None:
        position = Position(
            symbol="EUR_USD",
            quantity=Decimal("0"),
            average_price=Decimal("0"),
            realized_pnl=Decimal("500"),
            timestamp=sample_timestamp,
        )
        assert position.quantity == Decimal("0")
        assert position.is_flat

    def test_position_with_realized_pnl(self, sample_timestamp: datetime) -> None:
        position = Position(
            symbol="EUR_USD",
            quantity=Decimal("5000"),
            average_price=Decimal("1.1050"),
            realized_pnl=Decimal("250.50"),
            timestamp=sample_timestamp,
        )
        assert position.realized_pnl == Decimal("250.50")


class TestPositionValidation:
    """Tests for Position validation."""

    def test_rejects_naive_datetime(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            Position(
                symbol="EUR_USD",
                quantity=Decimal("10000"),
                average_price=Decimal("1.1000"),
                realized_pnl=Decimal("0"),
                timestamp=datetime(2024, 1, 15),  # No timezone
            )
        assert "timezone" in str(exc_info.value).lower()

    def test_rejects_negative_average_price(self, sample_timestamp: datetime) -> None:
        with pytest.raises(ValidationError) as exc_info:
            Position(
                symbol="EUR_USD",
                quantity=Decimal("10000"),
                average_price=Decimal("-1.1000"),
                realized_pnl=Decimal("0"),
                timestamp=sample_timestamp,
            )
        assert "average_price" in str(exc_info.value).lower()

    def test_accepts_zero_average_price_for_flat(self, sample_timestamp: datetime) -> None:
        """Zero average price is valid for flat positions."""
        position = Position(
            symbol="EUR_USD",
            quantity=Decimal("0"),
            average_price=Decimal("0"),
            realized_pnl=Decimal("0"),
            timestamp=sample_timestamp,
        )
        assert position.average_price == Decimal("0")

    def test_rejects_invalid_symbol(self, sample_timestamp: datetime) -> None:
        with pytest.raises(ValidationError):
            Position(
                symbol="eur/usd",
                quantity=Decimal("10000"),
                average_price=Decimal("1.1000"),
                realized_pnl=Decimal("0"),
                timestamp=sample_timestamp,
            )


class TestPositionDerivedFields:
    """Tests for Position computed properties."""

    def test_is_long(self, sample_timestamp: datetime) -> None:
        position = Position(
            symbol="EUR_USD",
            quantity=Decimal("10000"),
            average_price=Decimal("1.1000"),
            realized_pnl=Decimal("0"),
            timestamp=sample_timestamp,
        )
        assert position.is_long
        assert not position.is_short
        assert not position.is_flat

    def test_is_short(self, sample_timestamp: datetime) -> None:
        position = Position(
            symbol="EUR_USD",
            quantity=Decimal("-10000"),
            average_price=Decimal("1.1000"),
            realized_pnl=Decimal("0"),
            timestamp=sample_timestamp,
        )
        assert position.is_short
        assert not position.is_long
        assert not position.is_flat

    def test_is_flat(self, sample_timestamp: datetime) -> None:
        position = Position(
            symbol="EUR_USD",
            quantity=Decimal("0"),
            average_price=Decimal("0"),
            realized_pnl=Decimal("0"),
            timestamp=sample_timestamp,
        )
        assert position.is_flat
        assert not position.is_long
        assert not position.is_short

    def test_market_value(self, sample_timestamp: datetime) -> None:
        position = Position(
            symbol="EUR_USD",
            quantity=Decimal("10000"),
            average_price=Decimal("1.1000"),
            realized_pnl=Decimal("0"),
            timestamp=sample_timestamp,
        )
        # market_value = abs(quantity) * average_price = 10000 * 1.1000 = 11000
        assert position.market_value == Decimal("11000")

    def test_market_value_short(self, sample_timestamp: datetime) -> None:
        position = Position(
            symbol="EUR_USD",
            quantity=Decimal("-10000"),
            average_price=Decimal("1.1000"),
            realized_pnl=Decimal("0"),
            timestamp=sample_timestamp,
        )
        # market_value is signed: quantity * price = -10000 * 1.1 = -11000
        assert position.market_value == Decimal("-11000.0000")

    def test_unrealized_pnl_long_profit(self, sample_timestamp: datetime) -> None:
        position = Position(
            symbol="EUR_USD",
            quantity=Decimal("10000"),
            average_price=Decimal("1.1000"),
            realized_pnl=Decimal("0"),
            timestamp=sample_timestamp,
        )
        current_price = Decimal("1.1050")
        # For long: (current - avg) * quantity = (1.1050 - 1.1000) * 10000 = 50
        assert position.unrealized_pnl(current_price) == Decimal("50")

    def test_unrealized_pnl_long_loss(self, sample_timestamp: datetime) -> None:
        position = Position(
            symbol="EUR_USD",
            quantity=Decimal("10000"),
            average_price=Decimal("1.1000"),
            realized_pnl=Decimal("0"),
            timestamp=sample_timestamp,
        )
        current_price = Decimal("1.0950")
        # For long: (current - avg) * quantity = (1.0950 - 1.1000) * 10000 = -50
        assert position.unrealized_pnl(current_price) == Decimal("-50")

    def test_unrealized_pnl_short_profit(self, sample_timestamp: datetime) -> None:
        position = Position(
            symbol="EUR_USD",
            quantity=Decimal("-10000"),
            average_price=Decimal("1.1000"),
            realized_pnl=Decimal("0"),
            timestamp=sample_timestamp,
        )
        current_price = Decimal("1.0950")
        # For short: (current - avg) * quantity = (1.0950 - 1.1000) * -10000 = 50
        assert position.unrealized_pnl(current_price) == Decimal("50")

    def test_unrealized_pnl_short_loss(self, sample_timestamp: datetime) -> None:
        position = Position(
            symbol="EUR_USD",
            quantity=Decimal("-10000"),
            average_price=Decimal("1.1000"),
            realized_pnl=Decimal("0"),
            timestamp=sample_timestamp,
        )
        current_price = Decimal("1.1050")
        # For short: (current - avg) * quantity = (1.1050 - 1.1000) * -10000 = -50
        assert position.unrealized_pnl(current_price) == Decimal("-50")

    def test_unrealized_pnl_flat_is_zero(self, sample_timestamp: datetime) -> None:
        position = Position(
            symbol="EUR_USD",
            quantity=Decimal("0"),
            average_price=Decimal("0"),
            realized_pnl=Decimal("0"),
            timestamp=sample_timestamp,
        )
        assert position.unrealized_pnl(Decimal("1.1050")) == Decimal("0")


class TestPositionImmutability:
    """Tests for Position immutability (frozen model)."""

    def test_position_is_frozen(self, sample_timestamp: datetime) -> None:
        position = Position(
            symbol="EUR_USD",
            quantity=Decimal("10000"),
            average_price=Decimal("1.1000"),
            realized_pnl=Decimal("0"),
            timestamp=sample_timestamp,
        )
        with pytest.raises(ValidationError):
            position.symbol = "USD_JPY"  # type: ignore[misc]


class TestPositionSerialization:
    """Tests for Position serialization."""

    def test_json_serialization(self, sample_timestamp: datetime) -> None:
        position = Position(
            symbol="EUR_USD",
            quantity=Decimal("10000"),
            average_price=Decimal("1.1000"),
            realized_pnl=Decimal("0"),
            timestamp=sample_timestamp,
        )
        json_str = position.model_dump_json()
        assert "EUR_USD" in json_str
        assert "10000" in json_str

    def test_json_roundtrip(self, sample_timestamp: datetime) -> None:
        position = Position(
            symbol="EUR_USD",
            quantity=Decimal("10000"),
            average_price=Decimal("1.1000"),
            realized_pnl=Decimal("250.50"),
            timestamp=sample_timestamp,
        )
        json_str = position.model_dump_json()
        position2 = Position.model_validate_json(json_str)
        assert position.symbol == position2.symbol
        assert position.quantity == position2.quantity
        assert position.average_price == position2.average_price
        assert position.realized_pnl == position2.realized_pnl

    def test_dict_serialization(self, sample_timestamp: datetime) -> None:
        position = Position(
            symbol="EUR_USD",
            quantity=Decimal("10000"),
            average_price=Decimal("1.1000"),
            realized_pnl=Decimal("0"),
            timestamp=sample_timestamp,
        )
        data = position.model_dump()
        assert data["symbol"] == "EUR_USD"
        assert "quantity" in data

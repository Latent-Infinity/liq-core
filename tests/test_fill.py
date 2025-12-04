"""Tests for liq.core.fill module."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from liq.core.fill import Fill


class TestFillCreation:
    """Tests for Fill model creation."""

    def test_create_full_fill(self, sample_timestamp: datetime) -> None:
        order_id = uuid4()
        fill = Fill(
            fill_id=uuid4(),
            client_order_id=order_id,
            symbol="EUR_USD",
            side="buy",
            quantity=Decimal("10000"),
            price=Decimal("1.1000"),
            commission=Decimal("0.50"),
            timestamp=sample_timestamp,
        )
        assert fill.symbol == "EUR_USD"
        assert fill.side == "buy"
        assert fill.quantity == Decimal("10000")
        assert fill.price == Decimal("1.1000")
        assert fill.commission == Decimal("0.50")
        assert fill.client_order_id == order_id
        assert fill.realized_pnl is None

    def test_create_fill_with_zero_commission(self, sample_timestamp: datetime) -> None:
        fill = Fill(
            fill_id=uuid4(),
            client_order_id=uuid4(),
            symbol="EUR_USD",
            side="buy",
            quantity=Decimal("10000"),
            price=Decimal("1.1000"),
            commission=Decimal("0"),
            timestamp=sample_timestamp,
        )
        assert fill.commission == Decimal("0")

    def test_fill_has_fill_id(self, sample_timestamp: datetime) -> None:
        fill_id = uuid4()
        fill = Fill(
            fill_id=fill_id,
            client_order_id=uuid4(),
            symbol="EUR_USD",
            side="buy",
            quantity=Decimal("10000"),
            price=Decimal("1.1000"),
            commission=Decimal("0.50"),
            timestamp=sample_timestamp,
        )
        assert fill.fill_id == fill_id
        assert isinstance(fill.fill_id, UUID)

    def test_fill_default_slippage(self, sample_timestamp: datetime) -> None:
        fill = Fill(
            fill_id=uuid4(),
            client_order_id=uuid4(),
            symbol="EUR_USD",
            side="buy",
            quantity=Decimal("10000"),
            price=Decimal("1.1000"),
            commission=Decimal("0.50"),
            timestamp=sample_timestamp,
        )
        assert fill.slippage is None

    def test_fill_with_slippage(self, sample_timestamp: datetime) -> None:
        fill = Fill(
            fill_id=uuid4(),
            client_order_id=uuid4(),
            symbol="EUR_USD",
            side="buy",
            quantity=Decimal("10000"),
            price=Decimal("1.1005"),
            commission=Decimal("0.50"),
            slippage=Decimal("0.0005"),
            realized_pnl=Decimal("25"),
            timestamp=sample_timestamp,
        )
        assert fill.slippage == Decimal("0.0005")
        assert fill.realized_pnl == Decimal("25")


class TestFillValidation:
    """Tests for Fill validation."""

    def test_rejects_naive_datetime(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            Fill(
                fill_id=uuid4(),
                client_order_id=uuid4(),
                symbol="EUR_USD",
                side="buy",
                quantity=Decimal("10000"),
                price=Decimal("1.1000"),
                commission=Decimal("0.50"),
                timestamp=datetime(2024, 1, 15),  # No timezone
            )
        assert "timezone" in str(exc_info.value).lower()

    def test_rejects_zero_quantity(self, sample_timestamp: datetime) -> None:
        with pytest.raises(ValidationError) as exc_info:
            Fill(
                fill_id=uuid4(),
                client_order_id=uuid4(),
                symbol="EUR_USD",
                side="buy",
                quantity=Decimal("0"),
                price=Decimal("1.1000"),
                commission=Decimal("0.50"),
                timestamp=sample_timestamp,
            )
        assert "quantity" in str(exc_info.value).lower()

    def test_rejects_negative_quantity(self, sample_timestamp: datetime) -> None:
        with pytest.raises(ValidationError) as exc_info:
            Fill(
                fill_id=uuid4(),
                client_order_id=uuid4(),
                symbol="EUR_USD",
                side="buy",
                quantity=Decimal("-100"),
                price=Decimal("1.1000"),
                commission=Decimal("0.50"),
                timestamp=sample_timestamp,
            )
        assert "quantity" in str(exc_info.value).lower()

    def test_rejects_non_positive_price(self, sample_timestamp: datetime) -> None:
        with pytest.raises(ValidationError) as exc_info:
            Fill(
                fill_id=uuid4(),
                client_order_id=uuid4(),
                symbol="EUR_USD",
                side="buy",
                quantity=Decimal("10000"),
                price=Decimal("0"),
                commission=Decimal("0.50"),
                timestamp=sample_timestamp,
            )
        assert "price" in str(exc_info.value).lower()

    def test_rejects_negative_commission(self, sample_timestamp: datetime) -> None:
        with pytest.raises(ValidationError) as exc_info:
            Fill(
                fill_id=uuid4(),
                client_order_id=uuid4(),
                symbol="EUR_USD",
                side="buy",
                quantity=Decimal("10000"),
                price=Decimal("1.1000"),
                commission=Decimal("-0.50"),
                timestamp=sample_timestamp,
            )
        assert "commission" in str(exc_info.value).lower()

    def test_rejects_invalid_side(self, sample_timestamp: datetime) -> None:
        with pytest.raises(ValidationError):
            Fill(
                fill_id=uuid4(),
                client_order_id=uuid4(),
                symbol="EUR_USD",
                side="invalid",  # type: ignore[arg-type]
                quantity=Decimal("10000"),
                price=Decimal("1.1000"),
                commission=Decimal("0.50"),
                timestamp=sample_timestamp,
            )

    def test_rejects_invalid_symbol(self, sample_timestamp: datetime) -> None:
        with pytest.raises(ValidationError):
            Fill(
                fill_id=uuid4(),
                client_order_id=uuid4(),
                symbol="eur/usd",
                side="buy",
                quantity=Decimal("10000"),
                price=Decimal("1.1000"),
                commission=Decimal("0.50"),
                timestamp=sample_timestamp,
            )


class TestFillDerivedFields:
    """Tests for Fill computed properties."""

    def test_notional_value_calculation(self, sample_timestamp: datetime) -> None:
        fill = Fill(
            fill_id=uuid4(),
            client_order_id=uuid4(),
            symbol="EUR_USD",
            side="buy",
            quantity=Decimal("10000"),
            price=Decimal("1.1000"),
            commission=Decimal("0.50"),
            timestamp=sample_timestamp,
        )
        # notional = quantity * price = 10000 * 1.1000 = 11000
        assert fill.notional_value == Decimal("11000")

    def test_total_cost_buy(self, sample_timestamp: datetime) -> None:
        fill = Fill(
            fill_id=uuid4(),
            client_order_id=uuid4(),
            symbol="EUR_USD",
            side="buy",
            quantity=Decimal("10000"),
            price=Decimal("1.1000"),
            commission=Decimal("0.50"),
            timestamp=sample_timestamp,
        )
        # For buy: total_cost = notional + commission = 11000 + 0.50 = 11000.50
        assert fill.total_cost == Decimal("11000.50")

    def test_total_cost_sell(self, sample_timestamp: datetime) -> None:
        fill = Fill(
            fill_id=uuid4(),
            client_order_id=uuid4(),
            symbol="EUR_USD",
            side="sell",
            quantity=Decimal("10000"),
            price=Decimal("1.1000"),
            commission=Decimal("0.50"),
            timestamp=sample_timestamp,
        )
        # For sell: total_cost = -notional + commission = -11000 + 0.50 = -10999.50 (proceeds)
        assert fill.total_cost == Decimal("-10999.50")


class TestFillImmutability:
    """Tests for Fill immutability (frozen model)."""

    def test_fill_is_frozen(self, sample_timestamp: datetime) -> None:
        fill = Fill(
            fill_id=uuid4(),
            client_order_id=uuid4(),
            symbol="EUR_USD",
            side="buy",
            quantity=Decimal("10000"),
            price=Decimal("1.1000"),
            commission=Decimal("0.50"),
            timestamp=sample_timestamp,
        )
        with pytest.raises(ValidationError):
            fill.symbol = "USD_JPY"  # type: ignore[misc]


class TestFillSerialization:
    """Tests for Fill serialization."""

    def test_json_serialization(self, sample_timestamp: datetime) -> None:
        fill = Fill(
            fill_id=uuid4(),
            client_order_id=uuid4(),
            symbol="EUR_USD",
            side="buy",
            quantity=Decimal("10000"),
            price=Decimal("1.1000"),
            commission=Decimal("0.50"),
            timestamp=sample_timestamp,
        )
        json_str = fill.model_dump_json()
        assert "EUR_USD" in json_str
        assert "buy" in json_str
        assert "realized_pnl" in json_str

    def test_json_roundtrip(self, sample_timestamp: datetime) -> None:
        fill = Fill(
            fill_id=uuid4(),
            client_order_id=uuid4(),
            symbol="EUR_USD",
            side="buy",
            quantity=Decimal("10000"),
            price=Decimal("1.1000"),
            commission=Decimal("0.50"),
            realized_pnl=Decimal("10"),
            timestamp=sample_timestamp,
        )
        json_str = fill.model_dump_json()
        fill2 = Fill.model_validate_json(json_str)
        assert fill.symbol == fill2.symbol
        assert fill.side == fill2.side
        assert fill.quantity == fill2.quantity
        assert fill.price == fill2.price
        assert fill.commission == fill2.commission
        assert fill.realized_pnl == fill2.realized_pnl

    def test_dict_serialization(self, sample_timestamp: datetime) -> None:
        fill = Fill(
            fill_id=uuid4(),
            client_order_id=uuid4(),
            symbol="EUR_USD",
            side="buy",
            quantity=Decimal("10000"),
            price=Decimal("1.1000"),
            commission=Decimal("0.50"),
            timestamp=sample_timestamp,
        )
        data = fill.model_dump()
        assert data["symbol"] == "EUR_USD"
        assert data["side"] == "buy"
        assert "realized_pnl" in data

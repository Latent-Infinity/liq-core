"""Tests for liq.core.order module."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

import pytest
from pydantic import ValidationError

from liq.core.order import OrderRequest


class TestOrderRequestCreation:
    """Tests for OrderRequest model creation."""

    def test_create_market_order(self, sample_timestamp: datetime) -> None:
        order = OrderRequest(
            symbol="EUR_USD",
            side="buy",
            order_type="market",
            quantity=Decimal("10000"),
            strategy_id="strat_a",
            confidence=0.8,
            tags={"version": "v1"},
            timestamp=sample_timestamp,
        )
        assert order.symbol == "EUR_USD"
        assert order.side == "buy"
        assert order.order_type == "market"
        assert order.quantity == Decimal("10000")
        assert order.limit_price is None
        assert order.stop_price is None
        assert order.strategy_id == "strat_a"
        assert order.confidence == 0.8
        assert order.tags == {"version": "v1"}

    def test_create_limit_order(self, sample_timestamp: datetime) -> None:
        order = OrderRequest(
            symbol="EUR_USD",
            side="buy",
            order_type="limit",
            quantity=Decimal("10000"),
            limit_price=Decimal("1.1000"),
            timestamp=sample_timestamp,
        )
        assert order.order_type == "limit"
        assert order.limit_price == Decimal("1.1000")

    def test_create_stop_order(self, sample_timestamp: datetime) -> None:
        order = OrderRequest(
            symbol="EUR_USD",
            side="sell",
            order_type="stop",
            quantity=Decimal("10000"),
            stop_price=Decimal("1.0900"),
            timestamp=sample_timestamp,
        )
        assert order.order_type == "stop"
        assert order.stop_price == Decimal("1.0900")

    def test_create_stop_limit_order(self, sample_timestamp: datetime) -> None:
        order = OrderRequest(
            symbol="EUR_USD",
            side="sell",
            order_type="stop_limit",
            quantity=Decimal("10000"),
            limit_price=Decimal("1.0880"),
            stop_price=Decimal("1.0900"),
            timestamp=sample_timestamp,
        )
        assert order.order_type == "stop_limit"
        assert order.limit_price == Decimal("1.0880")
        assert order.stop_price == Decimal("1.0900")

    def test_order_has_client_order_id(self, sample_timestamp: datetime) -> None:
        order = OrderRequest(
            symbol="EUR_USD",
            side="buy",
            order_type="market",
            quantity=Decimal("10000"),
            timestamp=sample_timestamp,
        )
        assert order.client_order_id is not None
        assert isinstance(order.client_order_id, UUID)

    def test_order_default_time_in_force(self, sample_timestamp: datetime) -> None:
        order = OrderRequest(
            symbol="EUR_USD",
            side="buy",
            order_type="market",
            quantity=Decimal("10000"),
            timestamp=sample_timestamp,
        )
        assert order.time_in_force == "day"

    def test_order_custom_time_in_force(self, sample_timestamp: datetime) -> None:
        order = OrderRequest(
            symbol="EUR_USD",
            side="buy",
            order_type="limit",
            quantity=Decimal("10000"),
            limit_price=Decimal("1.1000"),
            time_in_force="gtc",
            timestamp=sample_timestamp,
        )
        assert order.time_in_force == "gtc"


class TestOrderRequestValidation:
    """Tests for OrderRequest validation."""

    def test_rejects_naive_datetime(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            OrderRequest(
                symbol="EUR_USD",
                side="buy",
                order_type="market",
                quantity=Decimal("10000"),
                timestamp=datetime(2024, 1, 15),  # No timezone
            )
        assert "timezone" in str(exc_info.value).lower()

    def test_rejects_zero_quantity(self, sample_timestamp: datetime) -> None:
        with pytest.raises(ValidationError) as exc_info:
            OrderRequest(
                symbol="EUR_USD",
                side="buy",
                order_type="market",
                quantity=Decimal("0"),
                timestamp=sample_timestamp,
            )
        assert "quantity" in str(exc_info.value).lower()

    def test_rejects_negative_quantity(self, sample_timestamp: datetime) -> None:
        with pytest.raises(ValidationError) as exc_info:
            OrderRequest(
                symbol="EUR_USD",
                side="buy",
                order_type="market",
                quantity=Decimal("-100"),
                timestamp=sample_timestamp,
            )
        assert "quantity" in str(exc_info.value).lower()

    def test_limit_order_requires_limit_price(self, sample_timestamp: datetime) -> None:
        with pytest.raises(ValidationError) as exc_info:
            OrderRequest(
                symbol="EUR_USD",
                side="buy",
                order_type="limit",
                quantity=Decimal("10000"),
                timestamp=sample_timestamp,
                # Missing limit_price
            )
        assert "limit_price" in str(exc_info.value).lower()

    def test_stop_order_requires_stop_price(self, sample_timestamp: datetime) -> None:
        with pytest.raises(ValidationError) as exc_info:
            OrderRequest(
                symbol="EUR_USD",
                side="sell",
                order_type="stop",
                quantity=Decimal("10000"),
                timestamp=sample_timestamp,
                # Missing stop_price
            )
        assert "stop_price" in str(exc_info.value).lower()

    def test_stop_limit_requires_both_prices(self, sample_timestamp: datetime) -> None:
        # Missing limit_price
        with pytest.raises(ValidationError) as exc_info:
            OrderRequest(
                symbol="EUR_USD",
                side="sell",
                order_type="stop_limit",
                quantity=Decimal("10000"),
                stop_price=Decimal("1.0900"),
                timestamp=sample_timestamp,
            )
        assert "limit_price" in str(exc_info.value).lower()

        # Missing stop_price
        with pytest.raises(ValidationError) as exc_info:
            OrderRequest(
                symbol="EUR_USD",
                side="sell",
                order_type="stop_limit",
                quantity=Decimal("10000"),
                limit_price=Decimal("1.0880"),
                timestamp=sample_timestamp,
            )
        assert "stop_price" in str(exc_info.value).lower()

    def test_rejects_non_positive_limit_price(self, sample_timestamp: datetime) -> None:
        with pytest.raises(ValidationError) as exc_info:
            OrderRequest(
                symbol="EUR_USD",
                side="buy",
                order_type="limit",
                quantity=Decimal("10000"),
                limit_price=Decimal("0"),
                timestamp=sample_timestamp,
            )
        assert "limit_price" in str(exc_info.value).lower()

    def test_rejects_non_positive_stop_price(self, sample_timestamp: datetime) -> None:
        with pytest.raises(ValidationError) as exc_info:
            OrderRequest(
                symbol="EUR_USD",
                side="sell",
                order_type="stop",
                quantity=Decimal("10000"),
                stop_price=Decimal("-1"),
                timestamp=sample_timestamp,
            )
        assert "stop_price" in str(exc_info.value).lower()

    def test_rejects_invalid_side(self, sample_timestamp: datetime) -> None:
        with pytest.raises(ValidationError):
            OrderRequest(
                symbol="EUR_USD",
                side="invalid",  # type: ignore[arg-type]
                order_type="market",
                quantity=Decimal("10000"),
                timestamp=sample_timestamp,
            )

    def test_rejects_confidence_out_of_range(self, sample_timestamp: datetime) -> None:
        with pytest.raises(ValidationError):
            OrderRequest(
                symbol="EUR_USD",
                side="buy",
                order_type="market",
                quantity=Decimal("10000"),
                confidence=1.5,
                timestamp=sample_timestamp,
            )

    def test_rejects_invalid_order_type(self, sample_timestamp: datetime) -> None:
        with pytest.raises(ValidationError):
            OrderRequest(
                symbol="EUR_USD",
                side="buy",
                order_type="invalid",  # type: ignore[arg-type]
                quantity=Decimal("10000"),
                timestamp=sample_timestamp,
            )

    def test_rejects_invalid_time_in_force(self, sample_timestamp: datetime) -> None:
        with pytest.raises(ValidationError):
            OrderRequest(
                symbol="EUR_USD",
                side="buy",
                order_type="market",
                quantity=Decimal("10000"),
                time_in_force="invalid",  # type: ignore[arg-type]
                timestamp=sample_timestamp,
            )

    def test_rejects_invalid_symbol(self, sample_timestamp: datetime) -> None:
        with pytest.raises(ValidationError):
            OrderRequest(
                symbol="eur/usd",
                side="buy",
                order_type="market",
                quantity=Decimal("10000"),
                timestamp=sample_timestamp,
            )


class TestOrderRequestImmutability:
    """Tests for OrderRequest immutability (frozen model)."""

    def test_order_is_frozen(self, sample_timestamp: datetime) -> None:
        order = OrderRequest(
            symbol="EUR_USD",
            side="buy",
            order_type="market",
            quantity=Decimal("10000"),
            timestamp=sample_timestamp,
        )
        with pytest.raises(ValidationError):
            order.symbol = "USD_JPY"  # type: ignore[misc]


class TestOrderRequestSerialization:
    """Tests for OrderRequest serialization."""

    def test_json_serialization(self, sample_timestamp: datetime) -> None:
        order = OrderRequest(
            symbol="EUR_USD",
            side="buy",
            order_type="limit",
            quantity=Decimal("10000"),
            limit_price=Decimal("1.1000"),
            timestamp=sample_timestamp,
        )
        json_str = order.model_dump_json()
        assert "EUR_USD" in json_str
        assert "buy" in json_str
        assert "limit" in json_str

    def test_json_roundtrip(self, sample_timestamp: datetime) -> None:
        order = OrderRequest(
            symbol="EUR_USD",
            side="buy",
            order_type="limit",
            quantity=Decimal("10000"),
            limit_price=Decimal("1.1000"),
            time_in_force="gtc",
            timestamp=sample_timestamp,
        )
        json_str = order.model_dump_json()
        order2 = OrderRequest.model_validate_json(json_str)
        assert order.symbol == order2.symbol
        assert order.side == order2.side
        assert order.order_type == order2.order_type
        assert order.quantity == order2.quantity
        assert order.limit_price == order2.limit_price
        assert order.time_in_force == order2.time_in_force

    def test_dict_serialization(self, sample_timestamp: datetime) -> None:
        order = OrderRequest(
            symbol="EUR_USD",
            side="buy",
            order_type="market",
            quantity=Decimal("10000"),
            timestamp=sample_timestamp,
        )
        data = order.model_dump()
        assert data["symbol"] == "EUR_USD"
        assert data["side"] == "buy"
        assert data["order_type"] == "market"

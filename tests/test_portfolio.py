"""Tests for liq.core.portfolio module."""

from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from liq.core.portfolio import PortfolioState
from liq.core.position import Position


class TestPortfolioStateCreation:
    """Tests for PortfolioState model creation."""

    def test_create_empty_portfolio(self, sample_timestamp: datetime) -> None:
        portfolio = PortfolioState(
            cash=Decimal("100000"),
            positions={},
            timestamp=sample_timestamp,
        )
        assert portfolio.cash == Decimal("100000")
        assert portfolio.positions == {}
        assert portfolio.unsettled_cash == Decimal("0")
        assert portfolio.day_trades_remaining is None

    def test_create_portfolio_with_positions(self, sample_timestamp: datetime) -> None:
        eur_position = Position(
            symbol="EUR_USD",
            quantity=Decimal("10000"),
            average_price=Decimal("1.1000"),
            realized_pnl=Decimal("0"),
            timestamp=sample_timestamp,
        )
        btc_position = Position(
            symbol="BTC-USD",
            quantity=Decimal("0.5"),
            average_price=Decimal("50000"),
            realized_pnl=Decimal("100"),
            timestamp=sample_timestamp,
        )
        portfolio = PortfolioState(
            cash=Decimal("75000"),
            positions={"EUR_USD": eur_position, "BTC-USD": btc_position},
            timestamp=sample_timestamp,
        )
        assert len(portfolio.positions) == 2
        assert "EUR_USD" in portfolio.positions
        assert "BTC-USD" in portfolio.positions

    def test_portfolio_with_realized_pnl(self, sample_timestamp: datetime) -> None:
        portfolio = PortfolioState(
            cash=Decimal("100000"),
            positions={},
            realized_pnl=Decimal("5000.50"),
            timestamp=sample_timestamp,
        )
        assert portfolio.realized_pnl == Decimal("5000.50")

    def test_portfolio_default_realized_pnl(self, sample_timestamp: datetime) -> None:
        portfolio = PortfolioState(
            cash=Decimal("100000"),
            positions={},
            timestamp=sample_timestamp,
        )
        assert portfolio.realized_pnl == Decimal("0")


class TestPortfolioStateValidation:
    """Tests for PortfolioState validation."""

    def test_rejects_naive_datetime(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            PortfolioState(
                cash=Decimal("100000"),
                positions={},
                timestamp=datetime(2024, 1, 15),  # No timezone
            )
        assert "timezone" in str(exc_info.value).lower()

    def test_accepts_negative_cash(self, sample_timestamp: datetime) -> None:
        """Negative cash (margin) is valid."""
        portfolio = PortfolioState(
            cash=Decimal("-50000"),
            positions={},
            timestamp=sample_timestamp,
        )
        assert portfolio.cash == Decimal("-50000")

    def test_rejects_invalid_position_key_symbol(self, sample_timestamp: datetime) -> None:
        with pytest.raises(ValidationError):
            PortfolioState(
                cash=Decimal("100000"),
                positions={"eur/usd": Position(
                    symbol="EUR_USD",
                    quantity=Decimal("10000"),
                    average_price=Decimal("1.1000"),
                    realized_pnl=Decimal("0"),
                    timestamp=sample_timestamp,
                )},
                timestamp=sample_timestamp,
            )

    def test_normalizes_position_key_symbol(self, sample_timestamp: datetime) -> None:
        eur_position = Position(
            symbol="eur_usd",
            quantity=Decimal("10000"),
            average_price=Decimal("1.1000"),
            realized_pnl=Decimal("0"),
            timestamp=sample_timestamp,
        )
        portfolio = PortfolioState(
            cash=Decimal("100000"),
            positions={"eur_usd": eur_position},
            timestamp=sample_timestamp,
        )
        assert "EUR_USD" in portfolio.positions


class TestPortfolioStateDerivedFields:
    """Tests for PortfolioState computed properties."""

    def test_total_market_value_empty(self, sample_timestamp: datetime) -> None:
        portfolio = PortfolioState(
            cash=Decimal("100000"),
            positions={},
            timestamp=sample_timestamp,
        )
        assert portfolio.total_market_value == Decimal("0")

    def test_total_market_value_with_positions(self, sample_timestamp: datetime) -> None:
        eur_position = Position(
            symbol="EUR_USD",
            quantity=Decimal("10000"),
            average_price=Decimal("1.1000"),
            realized_pnl=Decimal("0"),
            timestamp=sample_timestamp,
        )
        btc_position = Position(
            symbol="BTC-USD",
            quantity=Decimal("0.5"),
            average_price=Decimal("50000"),
            realized_pnl=Decimal("0"),
            timestamp=sample_timestamp,
        )
        portfolio = PortfolioState(
            cash=Decimal("75000"),
            positions={"EUR_USD": eur_position, "BTC-USD": btc_position},
            timestamp=sample_timestamp,
        )
        # EUR: 10000 * 1.1000 = 11000
        # BTC: 0.5 * 50000 = 25000
        # Total: 36000
        assert portfolio.total_market_value == Decimal("36000")

    def test_equity(self, sample_timestamp: datetime) -> None:
        eur_position = Position(
            symbol="EUR_USD",
            quantity=Decimal("10000"),
            average_price=Decimal("1.1000"),
            realized_pnl=Decimal("0"),
            timestamp=sample_timestamp,
        )
        portfolio = PortfolioState(
            cash=Decimal("89000"),
            positions={"EUR_USD": eur_position},
            timestamp=sample_timestamp,
        )
        # equity = cash + unsettled_cash + total_market_value = 89000 + 0 + 11000 = 100000
        assert portfolio.equity == Decimal("100000")

    def test_equity_with_unsettled_cash(self, sample_timestamp: datetime) -> None:
        eur_position = Position(
            symbol="EUR_USD",
            quantity=Decimal("10000"),
            average_price=Decimal("1.1000"),
            realized_pnl=Decimal("0"),
            timestamp=sample_timestamp,
        )
        portfolio = PortfolioState(
            cash=Decimal("89000"),
            unsettled_cash=Decimal("500"),
            positions={"EUR_USD": eur_position},
            timestamp=sample_timestamp,
        )
        # equity = cash + unsettled_cash + total_market_value = 89000 + 500 + 11000 = 100500
        assert portfolio.equity == Decimal("100500")

    def test_position_count(self, sample_timestamp: datetime) -> None:
        eur_position = Position(
            symbol="EUR_USD",
            quantity=Decimal("10000"),
            average_price=Decimal("1.1000"),
            realized_pnl=Decimal("0"),
            timestamp=sample_timestamp,
        )
        portfolio = PortfolioState(
            cash=Decimal("89000"),
            positions={"EUR_USD": eur_position},
            timestamp=sample_timestamp,
        )
        assert portfolio.position_count == 1

    def test_position_count_empty(self, sample_timestamp: datetime) -> None:
        portfolio = PortfolioState(
            cash=Decimal("100000"),
            positions={},
            timestamp=sample_timestamp,
        )
        assert portfolio.position_count == 0

    def test_symbols(self, sample_timestamp: datetime) -> None:
        eur_position = Position(
            symbol="EUR_USD",
            quantity=Decimal("10000"),
            average_price=Decimal("1.1000"),
            realized_pnl=Decimal("0"),
            timestamp=sample_timestamp,
        )
        btc_position = Position(
            symbol="BTC-USD",
            quantity=Decimal("0.5"),
            average_price=Decimal("50000"),
            realized_pnl=Decimal("0"),
            timestamp=sample_timestamp,
        )
        portfolio = PortfolioState(
            cash=Decimal("75000"),
            positions={"EUR_USD": eur_position, "BTC-USD": btc_position},
            timestamp=sample_timestamp,
        )
        symbols = portfolio.symbols
        assert "EUR_USD" in symbols
        assert "BTC-USD" in symbols

    def test_get_position_existing(self, sample_timestamp: datetime) -> None:
        eur_position = Position(
            symbol="EUR_USD",
            quantity=Decimal("10000"),
            average_price=Decimal("1.1000"),
            realized_pnl=Decimal("0"),
            timestamp=sample_timestamp,
        )
        portfolio = PortfolioState(
            cash=Decimal("89000"),
            positions={"EUR_USD": eur_position},
            timestamp=sample_timestamp,
        )
        pos = portfolio.get_position("EUR_USD")
        assert pos is not None
        assert pos.quantity == Decimal("10000")

    def test_get_position_not_found(self, sample_timestamp: datetime) -> None:
        portfolio = PortfolioState(
            cash=Decimal("100000"),
            positions={},
            timestamp=sample_timestamp,
        )
        assert portfolio.get_position("EUR_USD") is None

    def test_total_unrealized_pnl(self, sample_timestamp: datetime) -> None:
        eur_position = Position(
            symbol="EUR_USD",
            quantity=Decimal("10000"),
            average_price=Decimal("1.1000"),
            realized_pnl=Decimal("0"),
            timestamp=sample_timestamp,
        )
        btc_position = Position(
            symbol="BTC-USD",
            quantity=Decimal("0.5"),
            average_price=Decimal("50000"),
            realized_pnl=Decimal("0"),
            timestamp=sample_timestamp,
        )
        portfolio = PortfolioState(
            cash=Decimal("75000"),
            positions={"EUR_USD": eur_position, "BTC-USD": btc_position},
            timestamp=sample_timestamp,
        )
        current_prices = {
            "EUR_USD": Decimal("1.1050"),  # +50 profit (10000 * 0.0050)
            "BTC-USD": Decimal("51000"),   # +500 profit (0.5 * 1000)
        }
        total_unrealized = portfolio.total_unrealized_pnl(current_prices)
        assert total_unrealized == Decimal("550")

    def test_total_unrealized_pnl_missing_price(self, sample_timestamp: datetime) -> None:
        eur_position = Position(
            symbol="EUR_USD",
            quantity=Decimal("10000"),
            average_price=Decimal("1.1000"),
            realized_pnl=Decimal("0"),
            timestamp=sample_timestamp,
        )
        portfolio = PortfolioState(
            cash=Decimal("89000"),
            positions={"EUR_USD": eur_position},
            timestamp=sample_timestamp,
        )
        # Missing price for EUR_USD should raise KeyError
        with pytest.raises(KeyError):
            portfolio.total_unrealized_pnl({})


class TestPortfolioStateImmutability:
    """Tests for PortfolioState immutability (frozen model)."""

    def test_portfolio_is_frozen(self, sample_timestamp: datetime) -> None:
        portfolio = PortfolioState(
            cash=Decimal("100000"),
            positions={},
            timestamp=sample_timestamp,
        )
        with pytest.raises(ValidationError):
            portfolio.cash = Decimal("50000")  # type: ignore[misc]


class TestPortfolioStateSerialization:
    """Tests for PortfolioState serialization."""

    def test_json_serialization(self, sample_timestamp: datetime) -> None:
        eur_position = Position(
            symbol="EUR_USD",
            quantity=Decimal("10000"),
            average_price=Decimal("1.1000"),
            realized_pnl=Decimal("0"),
            timestamp=sample_timestamp,
        )
        portfolio = PortfolioState(
            cash=Decimal("89000"),
            positions={"EUR_USD": eur_position},
            timestamp=sample_timestamp,
        )
        json_str = portfolio.model_dump_json()
        assert "89000" in json_str
        assert "EUR_USD" in json_str

    def test_json_roundtrip(self, sample_timestamp: datetime) -> None:
        eur_position = Position(
            symbol="EUR_USD",
            quantity=Decimal("10000"),
            average_price=Decimal("1.1000"),
            realized_pnl=Decimal("0"),
            timestamp=sample_timestamp,
        )
        portfolio = PortfolioState(
            cash=Decimal("89000"),
            positions={"EUR_USD": eur_position},
            realized_pnl=Decimal("500"),
            timestamp=sample_timestamp,
        )
        json_str = portfolio.model_dump_json()
        portfolio2 = PortfolioState.model_validate_json(json_str)
        assert portfolio.cash == portfolio2.cash
        assert portfolio.realized_pnl == portfolio2.realized_pnl
        assert len(portfolio.positions) == len(portfolio2.positions)

    def test_dict_serialization(self, sample_timestamp: datetime) -> None:
        portfolio = PortfolioState(
            cash=Decimal("100000"),
            positions={},
            timestamp=sample_timestamp,
        )
        data = portfolio.model_dump()
        assert "cash" in data
        assert "positions" in data

"""Tests for liq.core.enums module."""

from liq.core.enums import (
    AssetClass,
    Currency,
    OrderSide,
    OrderStatus,
    OrderType,
    Provider,
    Timeframe,
    TimeInForce,
)


class TestAssetClass:
    """Tests for AssetClass enum."""

    def test_forex_value(self) -> None:
        assert AssetClass.FOREX.value == "forex"

    def test_crypto_value(self) -> None:
        assert AssetClass.CRYPTO.value == "crypto"

    def test_equity_value(self) -> None:
        assert AssetClass.EQUITY.value == "equity"

    def test_future_value(self) -> None:
        assert AssetClass.FUTURE.value == "future"

    def test_option_value(self) -> None:
        assert AssetClass.OPTION.value == "option"

    def test_str_enum_conversion(self) -> None:
        """AssetClass should be usable as a string."""
        assert str(AssetClass.FOREX) == "forex"
        assert AssetClass("forex") == AssetClass.FOREX

    def test_all_members(self) -> None:
        """Verify all expected members exist."""
        members = {m.value for m in AssetClass}
        expected = {"forex", "crypto", "equity", "future", "option"}
        assert members == expected


class TestOrderSide:
    """Tests for OrderSide enum."""

    def test_buy_value(self) -> None:
        assert OrderSide.BUY.value == "buy"

    def test_sell_value(self) -> None:
        assert OrderSide.SELL.value == "sell"

    def test_str_enum_conversion(self) -> None:
        assert str(OrderSide.BUY) == "buy"
        assert OrderSide("sell") == OrderSide.SELL

    def test_all_members(self) -> None:
        members = {m.value for m in OrderSide}
        assert members == {"buy", "sell"}


class TestOrderType:
    """Tests for OrderType enum."""

    def test_market_value(self) -> None:
        assert OrderType.MARKET.value == "market"

    def test_limit_value(self) -> None:
        assert OrderType.LIMIT.value == "limit"

    def test_stop_value(self) -> None:
        assert OrderType.STOP.value == "stop"

    def test_stop_limit_value(self) -> None:
        assert OrderType.STOP_LIMIT.value == "stop_limit"

    def test_str_enum_conversion(self) -> None:
        assert str(OrderType.MARKET) == "market"
        assert OrderType("limit") == OrderType.LIMIT

    def test_all_members(self) -> None:
        members = {m.value for m in OrderType}
        assert members == {"market", "limit", "stop", "stop_limit"}


class TestTimeInForce:
    """Tests for TimeInForce enum."""

    def test_day_value(self) -> None:
        assert TimeInForce.DAY.value == "day"

    def test_gtc_value(self) -> None:
        assert TimeInForce.GTC.value == "gtc"

    def test_ioc_value(self) -> None:
        assert TimeInForce.IOC.value == "ioc"

    def test_fok_value(self) -> None:
        assert TimeInForce.FOK.value == "fok"

    def test_str_enum_conversion(self) -> None:
        assert str(TimeInForce.GTC) == "gtc"
        assert TimeInForce("day") == TimeInForce.DAY

    def test_all_members(self) -> None:
        members = {m.value for m in TimeInForce}
        assert members == {"day", "gtc", "ioc", "fok"}


class TestProvider:
    """Tests for Provider enum."""

    def test_oanda_value(self) -> None:
        assert Provider.OANDA.value == "oanda"

    def test_binance_value(self) -> None:
        assert Provider.BINANCE.value == "binance"

    def test_coinbase_value(self) -> None:
        assert Provider.COINBASE.value == "coinbase"

    def test_polygon_value(self) -> None:
        assert Provider.POLYGON.value == "polygon"

    def test_alpaca_value(self) -> None:
        assert Provider.ALPACA.value == "alpaca"

    def test_tradestation_value(self) -> None:
        assert Provider.TRADESTATION.value == "tradestation"

    def test_robinhood_value(self) -> None:
        assert Provider.ROBINHOOD.value == "robinhood"

    def test_str_enum_conversion(self) -> None:
        assert str(Provider.OANDA) == "oanda"
        assert Provider("binance") == Provider.BINANCE

    def test_all_members(self) -> None:
        members = {m.value for m in Provider}
        expected = {
            "oanda",
            "binance",
            "coinbase",
            "polygon",
            "alpaca",
            "tradestation",
            "robinhood",
        }
        assert members == expected


class TestCurrency:
    """Tests for Currency enum."""

    def test_usd_value(self) -> None:
        assert Currency.USD.value == "USD"

    def test_eur_value(self) -> None:
        assert Currency.EUR.value == "EUR"

    def test_gbp_value(self) -> None:
        assert Currency.GBP.value == "GBP"

    def test_jpy_value(self) -> None:
        assert Currency.JPY.value == "JPY"

    def test_btc_value(self) -> None:
        assert Currency.BTC.value == "BTC"

    def test_eth_value(self) -> None:
        assert Currency.ETH.value == "ETH"

    def test_usdt_value(self) -> None:
        assert Currency.USDT.value == "USDT"

    def test_str_enum_conversion(self) -> None:
        assert str(Currency.USD) == "USD"
        assert Currency("EUR") == Currency.EUR

    def test_all_members(self) -> None:
        members = {m.value for m in Currency}
        expected = {"USD", "EUR", "GBP", "JPY", "BTC", "ETH", "USDT"}
        assert members == expected


class TestTimeframe:
    """Tests for Timeframe enum."""

    def test_m1_value(self) -> None:
        assert Timeframe.M1.value == "1m"

    def test_m5_value(self) -> None:
        assert Timeframe.M5.value == "5m"

    def test_m15_value(self) -> None:
        assert Timeframe.M15.value == "15m"

    def test_m30_value(self) -> None:
        assert Timeframe.M30.value == "30m"

    def test_h1_value(self) -> None:
        assert Timeframe.H1.value == "1h"

    def test_h4_value(self) -> None:
        assert Timeframe.H4.value == "4h"

    def test_d1_value(self) -> None:
        assert Timeframe.D1.value == "1d"

    def test_w1_value(self) -> None:
        assert Timeframe.W1.value == "1w"

    def test_mo1_value(self) -> None:
        assert Timeframe.MO1.value == "1mo"

    def test_str_enum_conversion(self) -> None:
        assert str(Timeframe.H1) == "1h"
        assert Timeframe("1d") == Timeframe.D1

    def test_all_members(self) -> None:
        members = {m.value for m in Timeframe}
        expected = {"1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1mo"}
        assert members == expected


class TestOrderStatus:
    """Tests for OrderStatus enum."""

    def test_pending_value(self) -> None:
        assert OrderStatus.PENDING.value == "pending"

    def test_submitted_value(self) -> None:
        assert OrderStatus.SUBMITTED.value == "submitted"

    def test_partial_value(self) -> None:
        assert OrderStatus.PARTIAL.value == "partial"

    def test_filled_value(self) -> None:
        assert OrderStatus.FILLED.value == "filled"

    def test_cancelled_value(self) -> None:
        assert OrderStatus.CANCELLED.value == "cancelled"

    def test_rejected_value(self) -> None:
        assert OrderStatus.REJECTED.value == "rejected"

    def test_str_enum_conversion(self) -> None:
        assert str(OrderStatus.FILLED) == "filled"
        assert OrderStatus("pending") == OrderStatus.PENDING

    def test_all_members(self) -> None:
        members = {m.value for m in OrderStatus}
        expected = {"pending", "submitted", "partial", "filled", "cancelled", "rejected"}
        assert members == expected


class TestEnumJsonSerialization:
    """Test that enums serialize correctly to JSON."""

    def test_asset_class_json(self) -> None:
        """AssetClass should serialize to its string value."""
        import json

        # str(Enum) returns the value for StrEnum
        assert json.dumps(AssetClass.FOREX.value) == '"forex"'

    def test_order_side_json(self) -> None:
        import json

        assert json.dumps(OrderSide.BUY.value) == '"buy"'

"""Enumeration types for the LIQ Stack.

All enums inherit from `StrEnum` to support string serialization
and comparison while maintaining type safety.
"""

from enum import StrEnum


class AssetClass(StrEnum):
    """Classification of tradeable asset types.

    Attributes:
        FOREX: Foreign exchange currency pairs (e.g., EUR_USD)
        CRYPTO: Cryptocurrency pairs (e.g., BTC-USD)
        EQUITY: Stock/equity instruments (e.g., AAPL)
        FUTURE: Futures contracts (deferred)
        OPTION: Options contracts (deferred)
    """

    FOREX = "forex"
    CRYPTO = "crypto"
    EQUITY = "equity"
    FUTURE = "future"
    OPTION = "option"


class OrderSide(StrEnum):
    """Direction of a trading order.

    Attributes:
        BUY: Purchase the instrument (go long or cover short)
        SELL: Sell the instrument (go short or close long)
    """

    BUY = "buy"
    SELL = "sell"


class OrderType(StrEnum):
    """Type of order execution.

    Attributes:
        MARKET: Execute immediately at best available price
        LIMIT: Execute at specified price or better
        STOP: Trigger market order when stop price is reached
        STOP_LIMIT: Trigger limit order when stop price is reached
    """

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class TimeInForce(StrEnum):
    """Duration for which an order remains active.

    Attributes:
        DAY: Valid until end of trading session
        GTC: Good til canceled - remains active until filled or canceled
        IOC: Immediate or cancel - fill immediately or cancel
        FOK: Fill or kill - fill entirely or cancel
    """

    DAY = "day"
    GTC = "gtc"
    IOC = "ioc"
    FOK = "fok"


class Provider(StrEnum):
    """Supported data and execution providers.

    Attributes:
        OANDA: Forex broker and data provider
        BINANCE: Cryptocurrency exchange
        COINBASE: Cryptocurrency exchange
        POLYGON: Market data provider
        ALPACA: Stock broker and data provider
        TRADESTATION: Stock/futures broker
        ROBINHOOD: Stock broker
    """

    OANDA = "oanda"
    BINANCE = "binance"
    COINBASE = "coinbase"
    POLYGON = "polygon"
    ALPACA = "alpaca"
    TRADESTATION = "tradestation"
    ROBINHOOD = "robinhood"


class Currency(StrEnum):
    """Supported currencies for account denomination and trading.

    Attributes:
        USD: US Dollar
        EUR: Euro
        GBP: British Pound
        JPY: Japanese Yen
        BTC: Bitcoin
        ETH: Ethereum
        USDT: Tether (USD stablecoin)
    """

    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    BTC = "BTC"
    ETH = "ETH"
    USDT = "USDT"


class Timeframe(StrEnum):
    """Bar/candle timeframe intervals.

    Attributes:
        M1: 1 minute bars
        M5: 5 minute bars
        M15: 15 minute bars
        M30: 30 minute bars
        H1: 1 hour bars
        H4: 4 hour bars
        D1: Daily bars
        W1: Weekly bars
        MO1: Monthly bars
    """

    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"
    MO1 = "1mo"


class OrderStatus(StrEnum):
    """Lifecycle status of an order.

    Attributes:
        PENDING: Order created but not yet submitted to broker
        SUBMITTED: Order sent to broker, awaiting fill
        PARTIAL: Order partially filled
        FILLED: Order fully executed
        CANCELLED: Order canceled by user or system
        REJECTED: Order rejected by broker
    """

    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

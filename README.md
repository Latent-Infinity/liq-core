# liq-core

Core data models and type definitions for the LIQ (Latent Infinity Quant) Stack.

## Overview

`liq-core` is the foundational library for the LIQ ecosystem, providing the shared type system that all other LIQ libraries import. This prevents type drift and ensures the entire ecosystem speaks the same language.

## Features

- **Immutable Models**: All models are frozen Pydantic v2 models, preventing accidental mutations
- **Strict Validation**: Comprehensive field validators ensure data integrity at construction time
- **Type Safety**: Full type hints with strict mypy compliance
- **Decimal Precision**: Financial calculations use `Decimal` to avoid floating-point errors
- **Symbol Normalization**: Consistent symbol formatting across asset classes

## Installation

```bash
pip install liq-core
```

Or for development:

```bash
pip install -e ".[dev]"
```

## Quick Start

### Creating a Bar (OHLCV)

```python
from liq.core import Bar
from datetime import datetime, UTC
from decimal import Decimal

bar = Bar(
    timestamp=datetime.now(UTC),
    symbol="EUR_USD",
    open=Decimal("1.1000"),
    high=Decimal("1.1050"),
    low=Decimal("1.0950"),
    close=Decimal("1.1025"),
    volume=Decimal("10000"),
)

# Computed properties
print(f"Range: {bar.range}")        # 0.0100
print(f"Midrange: {bar.midrange}")  # 1.1000
print(f"Body: {bar.body}")          # 0.0025
```

### Creating a Quote (Bid/Ask)

```python
from liq.core import Quote
from datetime import datetime, UTC
from decimal import Decimal

quote = Quote(
    timestamp=datetime.now(UTC),
    symbol="EUR_USD",
    bid=Decimal("1.1000"),
    ask=Decimal("1.1002"),
    bid_size=Decimal("1000000"),
    ask_size=Decimal("1500000"),
)

# Computed properties
print(f"Mid: {quote.mid}")              # 1.1001
print(f"Spread: {quote.spread}")        # 0.0002
print(f"Spread BPS: {quote.spread_bps}") # ~1.8 bps
```

### Creating an Order

```python
from liq.core import OrderRequest, OrderSide, OrderType
from datetime import datetime, UTC
from decimal import Decimal

# Market order
market_order = OrderRequest(
    symbol="EUR_USD",
    side=OrderSide.BUY,
    order_type=OrderType.MARKET,
    quantity=Decimal("10000"),
    timestamp=datetime.now(UTC),
)

# Limit order (requires limit_price)
limit_order = OrderRequest(
    symbol="EUR_USD",
    side=OrderSide.SELL,
    order_type=OrderType.LIMIT,
    quantity=Decimal("10000"),
    limit_price=Decimal("1.1050"),
    timestamp=datetime.now(UTC),
)
```

### Symbol Normalization

```python
from liq.core import normalize_symbol, AssetClass

# Forex: converts to underscore format
normalize_symbol("EUR/USD", AssetClass.FOREX)  # "EUR_USD"
normalize_symbol("eurusd", AssetClass.FOREX)   # "EUR_USD"

# Crypto: converts to hyphen format
normalize_symbol("btcusdt", AssetClass.CRYPTO) # "BTC-USDT"
normalize_symbol("BTC/USDT", AssetClass.CRYPTO) # "BTC-USDT"

# Equity: uppercase
normalize_symbol("aapl", AssetClass.EQUITY)    # "AAPL"
```

### Working with Positions

```python
from liq.core import Position
from decimal import Decimal

position = Position(
    symbol="EUR_USD",
    quantity=Decimal("10000"),
    avg_entry_price=Decimal("1.1000"),
    realized_pnl=Decimal("0"),
)

# Calculate unrealized P&L
current_price = Decimal("1.1050")
unrealized = position.unrealized_pnl(current_price)
print(f"Unrealized P&L: {unrealized}")  # 50.00 (in quote currency)

# Market value
print(f"Market Value: {position.market_value(current_price)}")  # 11050.00
```

## Available Models

| Model | Description |
|-------|-------------|
| `Bar` | OHLCV candlestick data with computed properties (range, body, midrange) |
| `Quote` | Bid/ask quote with computed spread metrics |
| `OrderRequest` | Order specification with type-specific validation |
| `Fill` | Executed trade with commission and slippage |
| `Position` | Current holding with P&L calculations |
| `PortfolioState` | Aggregated positions with cash and margin |
| `Instrument` | Instrument metadata (tick size, lot size, trading hours) |

## Available Enums

| Enum | Values |
|------|--------|
| `AssetClass` | FOREX, CRYPTO, EQUITY, FUTURES, OPTIONS |
| `OrderSide` | BUY, SELL |
| `OrderType` | MARKET, LIMIT, STOP, STOP_LIMIT |
| `OrderStatus` | PENDING, OPEN, FILLED, PARTIALLY_FILLED, CANCELLED, REJECTED, EXPIRED |
| `TimeInForce` | DAY, GTC, IOC, FOK |
| `Timeframe` | M1, M5, M15, M30, H1, H4, D1, W1, MN |
| `Provider` | OANDA, BINANCE, COINBASE, ALPACA, etc. |
| `Currency` | USD, EUR, GBP, JPY, etc. |

## Validation Examples

All models validate data at construction time:

```python
from liq.core import Bar
from datetime import datetime, UTC
from decimal import Decimal

# This raises ValidationError: high must be >= low
try:
    bar = Bar(
        timestamp=datetime.now(UTC),
        symbol="EUR_USD",
        open=Decimal("1.1000"),
        high=Decimal("1.0900"),  # Invalid: high < low
        low=Decimal("1.1000"),
        close=Decimal("1.0950"),
        volume=Decimal("10000"),
    )
except ValidationError as e:
    print(e)  # "high must be >= low"

# This raises ValidationError: limit_price required for LIMIT orders
try:
    OrderRequest(
        symbol="EUR_USD",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=Decimal("10000"),
        timestamp=datetime.now(UTC),
        # Missing limit_price!
    )
except ValidationError as e:
    print(e)  # "limit_price is required for LIMIT orders"
```

## JSON Serialization

All models support lossless JSON roundtrip:

```python
from liq.core import Bar

bar = Bar(...)
json_str = bar.model_dump_json()

# Deserialize back
bar2 = Bar.model_validate_json(json_str)
assert bar == bar2  # Exact equality, including Decimal precision
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=liq.core --cov-report=term-missing

# Type checking
mypy src/

# Linting
ruff check src/ tests/
```

## License

MIT License - see [LICENSE](LICENSE) for details.

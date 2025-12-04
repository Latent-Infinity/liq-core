"""Portfolio state data model for the LIQ Stack.

The PortfolioState model represents the complete state of a portfolio
at a point in time, including cash and all positions.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator

from liq.core.position import Position
from liq.core.symbols import validate_symbol


class PortfolioState(BaseModel):
    """Portfolio state representing cash and positions.

    Attributes:
        cash: Available cash balance (can be negative for margin)
        positions: Map of symbol to Position
        realized_pnl: Cumulative realized profit/loss
        timestamp: State snapshot time (UTC, timezone-aware)

    Computed Properties:
        total_market_value: Sum of all position market values
        equity: cash + total_market_value
        position_count: Number of positions
        symbols: List of symbols with positions

    Methods:
        get_position(symbol): Get position for symbol or None
        total_unrealized_pnl(prices): Calculate total unrealized P&L

    Validations:
        - timestamp must be timezone-aware (UTC)
    """

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
    )

    cash: Decimal
    unsettled_cash: Decimal = Decimal("0")
    positions: dict[str, Position]
    realized_pnl: Decimal = Decimal("0")
    buying_power: Decimal | None = None
    margin_used: Decimal | None = None
    day_trades_remaining: int | None = None
    timestamp: datetime

    @field_validator("positions", mode="before")
    @classmethod
    def normalize_position_keys(cls, v: dict[str, Position]) -> dict[str, Position]:
        """Normalize and validate position keys."""
        if not isinstance(v, dict):
            raise TypeError("positions must be a mapping of symbol to Position")

        normalized: dict[str, Position] = {}
        for symbol, position in v.items():
            normalized_symbol = symbol.strip().upper()
            if not validate_symbol(normalized_symbol):
                raise ValueError("position symbol keys must be canonical")
            normalized[normalized_symbol] = position
        return normalized

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp_timezone(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware."""
        if v.tzinfo is None or v.tzinfo.utcoffset(v) is None:
            raise ValueError("timestamp must be timezone-aware (UTC expected)")
        return v

    @property
    def total_market_value(self) -> Decimal:
        """Calculate total market value of all positions."""
        return sum(
            (pos.market_value for pos in self.positions.values()),
            Decimal("0"),
        )

    @property
    def equity(self) -> Decimal:
        """Calculate total equity: cash + unsettled_cash + total_market_value."""
        return self.cash + self.unsettled_cash + self.total_market_value

    @property
    def position_count(self) -> int:
        """Return number of positions."""
        return len(self.positions)

    @property
    def symbols(self) -> list[str]:
        """Return list of symbols with positions."""
        return list(self.positions.keys())

    def get_position(self, symbol: str) -> Position | None:
        """Get position for symbol.

        Args:
            symbol: Instrument symbol

        Returns:
            Position if exists, None otherwise
        """
        return self.positions.get(symbol)

    def total_unrealized_pnl(self, current_prices: dict[str, Decimal]) -> Decimal:
        """Calculate total unrealized P&L across all positions.

        Args:
            current_prices: Map of symbol to current price

        Returns:
            Total unrealized profit/loss

        Raises:
            KeyError: If price missing for any position
        """
        total = Decimal("0")
        for symbol, position in self.positions.items():
            current_price = current_prices[symbol]
            total += position.unrealized_pnl(current_price)
        return total

    @field_serializer("cash", "unsettled_cash", "realized_pnl", "buying_power", "margin_used")
    def serialize_decimal(self, v: Decimal | None) -> str | None:
        """Serialize Decimal as string to preserve precision."""
        return str(v) if v is not None else None

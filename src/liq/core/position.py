"""Position data model for the LIQ Stack.

The Position model represents a holding in a single instrument.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator

from liq.core.symbols import validate_symbol


class Position(BaseModel):
    """Position representing a holding in a single instrument.

    Attributes:
        symbol: Instrument symbol
        quantity: Position size (positive=long, negative=short, zero=flat)
        average_price: Average entry price (cost basis)
        realized_pnl: Cumulative realized profit/loss
        timestamp: Last update time (UTC, timezone-aware)

    Computed Properties:
        is_long: quantity > 0
        is_short: quantity < 0
        is_flat: quantity == 0
        market_value: abs(quantity) * average_price

    Methods:
        unrealized_pnl(current_price): (current_price - average_price) * quantity

    Validations:
        - average_price >= 0
        - timestamp must be timezone-aware (UTC)
    """

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
    )

    symbol: str
    quantity: Decimal
    average_price: Decimal
    realized_pnl: Decimal
    timestamp: datetime
    current_price: Decimal | None = None

    @field_validator("symbol")
    @classmethod
    def validate_symbol_format(cls, v: str) -> str:
        """Normalize and validate symbol format."""
        normalized = v.strip().upper()
        if not validate_symbol(normalized):
            raise ValueError("symbol must be canonical (uppercase with _ or -)")
        return normalized

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp_timezone(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware."""
        if v.tzinfo is None or v.tzinfo.utcoffset(v) is None:
            raise ValueError("timestamp must be timezone-aware (UTC expected)")
        return v

    @field_validator("average_price")
    @classmethod
    def validate_average_price_non_negative(cls, v: Decimal) -> Decimal:
        """Ensure average_price is non-negative."""
        if v < 0:
            raise ValueError("average_price must be >= 0")
        return v

    @field_validator("current_price")
    @classmethod
    def validate_current_price_non_negative(cls, v: Decimal | None) -> Decimal | None:
        """Ensure current_price is non-negative when provided."""
        if v is not None and v < 0:
            raise ValueError("current_price must be >= 0")
        return v

    @property
    def is_long(self) -> bool:
        """Check if position is long (positive quantity)."""
        return self.quantity > 0

    @property
    def is_short(self) -> bool:
        """Check if position is short (negative quantity)."""
        return self.quantity < 0

    @property
    def is_flat(self) -> bool:
        """Check if position is flat (zero quantity)."""
        return self.quantity == 0

    @property
    def market_value(self) -> Decimal:
        """Calculate market value: abs(quantity) * mark price."""
        mark_price = self.current_price if self.current_price is not None else self.average_price
        return abs(self.quantity) * mark_price

    def unrealized_pnl(self, current_price: Decimal) -> Decimal:
        """Calculate unrealized P&L given current price.

        For long positions: (current_price - average_price) * quantity
        For short positions: (current_price - average_price) * quantity
            (negative quantity makes this work correctly)

        Args:
            current_price: Current market price

        Returns:
            Unrealized profit/loss
        """
        return (current_price - self.average_price) * self.quantity

    @field_serializer("quantity", "average_price", "realized_pnl", "current_price")
    def serialize_decimal(self, v: Decimal | None) -> str | None:
        """Serialize Decimal as string to preserve precision."""
        return str(v) if v is not None else None

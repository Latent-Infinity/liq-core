"""Quote (bid/ask) data model for the LIQ Stack.

The Quote model represents a point-in-time snapshot of the best
bid and ask prices for an instrument.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    field_serializer,
    field_validator,
    model_validator,
)

from liq.core.symbols import validate_symbol


class Quote(BaseModel):
    """Best bid/ask snapshot for an instrument.

    Attributes:
        symbol: Instrument symbol
        timestamp: Quote time (UTC, timezone-aware)
        bid: Best bid price
        ask: Best ask price
        bid_size: Size available at bid
        ask_size: Size available at ask

    Computed Properties:
        mid: (bid + ask) / 2
        spread: ask - bid
        spread_bps: (spread / mid) * 10000
    """

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
    )

    symbol: str
    timestamp: datetime
    bid: Decimal
    ask: Decimal
    bid_size: Decimal
    ask_size: Decimal

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

    @field_validator("bid", "ask")
    @classmethod
    def validate_price_positive(cls, v: Decimal) -> Decimal:
        """Ensure bid/ask prices are positive."""
        if v <= 0:
            raise ValueError("bid/ask must be > 0")
        return v

    @field_validator("bid_size", "ask_size")
    @classmethod
    def validate_size_non_negative(cls, v: Decimal) -> Decimal:
        """Ensure sizes are non-negative."""
        if v < 0:
            raise ValueError("size must be >= 0")
        return v

    @model_validator(mode="after")
    def validate_spread(self) -> "Quote":
        """Ensure market is not crossed."""
        if self.ask < self.bid:
            raise ValueError("ask must be >= bid")
        return self

    @property
    def mid(self) -> Decimal:
        """Calculate mid price: (bid + ask) / 2."""
        return (self.bid + self.ask) / 2

    @property
    def spread(self) -> Decimal:
        """Calculate spread: ask - bid."""
        return self.ask - self.bid

    @property
    def spread_bps(self) -> Decimal:
        """Calculate spread in basis points: (spread / mid) * 10000."""
        if self.mid == 0:
            return Decimal("0")
        return (self.spread / self.mid) * 10000

    @field_serializer("bid", "ask", "bid_size", "ask_size")
    def serialize_decimal(self, v: Decimal) -> str:
        """Serialize Decimal as string to preserve precision."""
        return str(v)

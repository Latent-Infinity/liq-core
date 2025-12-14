"""Bar (OHLCV candle) data model for the LIQ Stack.

The Bar model represents a single time period of trading activity,
with Open, High, Low, Close prices and Volume.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    field_serializer,
    field_validator,
    model_validator,
)

from liq.core.symbols import validate_symbol


class Bar(BaseModel):
    """OHLCV bar (candle) representing a single time period of trading.

    Attributes:
        timestamp: Bar start time (UTC, timezone-aware)
        symbol: Canonical symbol (e.g., EUR_USD, BTC-USD, AAPL)
        open: Opening price
        high: Highest price during the period
        low: Lowest price during the period
        close: Closing price
        volume: Trading volume (>= 0)

    Computed Properties:
        midrange: (high + low) / 2
        range: high - low

    Validations:
        - high >= low
        - high >= open and high >= close
        - low <= open and low <= close
        - volume >= 0
        - timestamp must be timezone-aware (UTC)
    """

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
    )

    timestamp: datetime
    symbol: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal

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
        if v.utcoffset() != timezone.utc.utcoffset(v):
            raise ValueError("timestamp must be UTC")
        return v

    @field_validator("open", "high", "low", "close")
    @classmethod
    def validate_price_positive(cls, v: Decimal) -> Decimal:
        """Ensure OHLC prices are positive."""
        if v <= 0:
            raise ValueError("price fields must be > 0")
        return v

    @field_validator("volume")
    @classmethod
    def validate_volume_non_negative(cls, v: Decimal) -> Decimal:
        """Ensure volume is non-negative."""
        if v < 0:
            raise ValueError("volume must be >= 0")
        return v

    @model_validator(mode="after")
    def validate_ohlc_constraints(self) -> "Bar":
        """Validate OHLC price relationships."""
        if self.high < self.low:
            raise ValueError("high must be >= low")
        if self.high < self.open:
            raise ValueError("high must be >= open")
        if self.high < self.close:
            raise ValueError("high must be >= close")
        if self.low > self.open:
            raise ValueError("low must be <= open")
        if self.low > self.close:
            raise ValueError("low must be <= close")
        return self

    @property
    def midrange(self) -> Decimal:
        """Calculate midrange: (high + low) / 2.

        The midrange provides a range-invariant price reference point,
        useful for directional-change and range-bar strategies.
        """
        return (self.high + self.low) / 2

    @property
    def range(self) -> Decimal:
        """Calculate range: high - low.

        The range represents intrabar price movement.
        """
        return self.high - self.low

    def true_range_midrange(self, prev_midrange: Optional[Decimal]) -> Decimal:
        """Gap-aware true range using midrange vs prior bar."""
        current_mid = self.midrange
        if prev_midrange is None:
            return self.range
        return max(self.range, abs(current_mid - prev_midrange))

    def true_range_hl(
        self, prev_high: Optional[Decimal], prev_low: Optional[Decimal]
    ) -> Decimal:
        """Gap-aware true range using high/low vs prior bar."""
        candidates = [self.range]
        if prev_high is not None:
            candidates.append(abs(self.high - prev_high))
        if prev_low is not None:
            candidates.append(abs(self.low - prev_low))
        return max(candidates)

    @field_serializer("open", "high", "low", "close", "volume")
    def serialize_decimal(self, v: Decimal) -> str:
        """Serialize Decimal as string to preserve precision."""
        return str(v)

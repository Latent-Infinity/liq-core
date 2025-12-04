"""Instrument and provider metadata models for the LIQ Stack.

These models represent tradeable instruments and data provider configuration.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


class Instrument(BaseModel):
    """Represents a tradeable financial instrument.

    Instruments map provider-specific symbols to canonical symbols
    and provide metadata about each tradeable asset.

    Attributes:
        symbol: Provider-specific symbol (e.g., "EUR/USD" for OANDA)
        provider: Data provider name (e.g., "oanda", "binance")
        canonical_symbol: Normalized symbol (e.g., "EUR_USD", "BTC-USDT")
        asset_class: Asset class (e.g., "forex", "crypto", "equity")
        name: Human-readable instrument name
        base_currency: Base currency or ticker (e.g., "EUR", "BTC")
        quote_currency: Quote currency (e.g., "USD", "USDT")
        tick_size: Minimum price increment (must be > 0)
        lot_size: Minimum order size (must be > 0)
        active: Whether instrument is currently tradeable
        trading_hours: Optional market hours information

    Validations:
        - tick_size > 0
        - lot_size > 0
    """

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
    )

    symbol: str
    provider: str
    canonical_symbol: str
    asset_class: str
    name: str
    base_currency: str
    quote_currency: str
    tick_size: Decimal = Field(gt=0)
    lot_size: Decimal = Field(gt=0)
    active: bool
    trading_hours: dict[str, Any] | None = None

    @field_serializer("tick_size", "lot_size")
    def serialize_decimal(self, v: Decimal) -> str:
        """Serialize Decimal as string to preserve precision."""
        return str(v)


class ProviderMetadata(BaseModel):
    """Metadata about a data provider.

    Stores configuration and capabilities for each data provider.

    Attributes:
        provider_name: Unique provider identifier
        asset_classes: List of supported asset classes
        api_endpoint: Base URL for provider API
        rate_limit_per_minute: Maximum requests per minute (must be > 0)
        enabled: Whether provider is currently active
        priority: Provider priority (must be >= 1, lower = higher priority)
        authentication_required: Whether API key/auth is required
        rate_limit_per_day: Optional daily rate limit
        historical_data_limit_years: Optional limit on historical data
        last_successful_fetch: Optional timestamp of last successful fetch

    Validations:
        - rate_limit_per_minute > 0
        - priority >= 1
        - rate_limit_per_day > 0 (when provided)
    """

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
    )

    provider_name: str
    asset_classes: list[str]
    api_endpoint: str
    rate_limit_per_minute: int = Field(gt=0)
    enabled: bool
    priority: int = Field(ge=1)
    authentication_required: bool
    rate_limit_per_day: int | None = Field(default=None, gt=0)
    historical_data_limit_years: int | None = None
    last_successful_fetch: datetime | None = None

    @field_validator("last_successful_fetch")
    @classmethod
    def validate_timestamp_timezone(cls, v: datetime | None) -> datetime | None:
        """Ensure timestamp is timezone-aware when provided."""
        if v is not None and (v.tzinfo is None or v.tzinfo.utcoffset(v) is None):
            raise ValueError("last_successful_fetch must be timezone-aware (UTC expected)")
        return v

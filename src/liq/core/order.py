"""Order request data model for the LIQ Stack.

The OrderRequest model represents an intent to enter or exit a position.
It captures all parameters needed to submit an order to a broker.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)

from liq.core.enums import OrderSide, OrderType, TimeInForce
from liq.core.symbols import validate_symbol


class OrderRequest(BaseModel):
    """Order request representing an intent to trade.

    Attributes:
        client_order_id: Unique identifier for the order (auto-generated)
        symbol: Instrument symbol
        side: Buy or sell
        order_type: Market, limit, stop, or stop_limit
        quantity: Order quantity (must be > 0)
        limit_price: Required for limit and stop_limit orders
        stop_price: Required for stop and stop_limit orders
        time_in_force: Order duration (default: day)
        timestamp: Order creation time (UTC, timezone-aware)

    Validations:
        - quantity > 0
        - limit_price > 0 (when provided)
        - stop_price > 0 (when provided)
        - LIMIT orders require limit_price
        - STOP orders require stop_price
        - STOP_LIMIT orders require both limit_price and stop_price
        - timestamp must be timezone-aware (UTC)
    """

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
    )

    client_order_id: UUID = Field(default_factory=uuid4)
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    limit_price: Decimal | None = None
    stop_price: Decimal | None = None
    time_in_force: TimeInForce = TimeInForce.DAY
    timestamp: datetime
    strategy_id: str | None = None
    confidence: float | None = None
    tags: dict | None = None
    metadata: dict | None = None

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

    @field_validator("quantity")
    @classmethod
    def validate_quantity_positive(cls, v: Decimal) -> Decimal:
        """Ensure quantity is positive."""
        if v <= 0:
            raise ValueError("quantity must be > 0")
        return v

    @field_validator("limit_price")
    @classmethod
    def validate_limit_price_positive(cls, v: Decimal | None) -> Decimal | None:
        """Ensure limit_price is positive when provided."""
        if v is not None and v <= 0:
            raise ValueError("limit_price must be > 0")
        return v

    @field_validator("stop_price")
    @classmethod
    def validate_stop_price_positive(cls, v: Decimal | None) -> Decimal | None:
        """Ensure stop_price is positive when provided."""
        if v is not None and v <= 0:
            raise ValueError("stop_price must be > 0")
        return v

    @field_validator("confidence")
    @classmethod
    def validate_confidence_range(cls, v: float | None) -> float | None:
        """Ensure confidence is within [0, 1] when provided."""
        if v is None:
            return v
        if not 0.0 <= v <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        return v

    @model_validator(mode="after")
    def validate_price_requirements(self) -> "OrderRequest":
        """Validate that required prices are present based on order type."""
        if self.order_type == OrderType.LIMIT:
            if self.limit_price is None:
                raise ValueError("limit_price is required for LIMIT orders")
        elif self.order_type == OrderType.STOP:
            if self.stop_price is None:
                raise ValueError("stop_price is required for STOP orders")
        elif self.order_type == OrderType.STOP_LIMIT:
            if self.limit_price is None:
                raise ValueError("limit_price is required for STOP_LIMIT orders")
            if self.stop_price is None:
                raise ValueError("stop_price is required for STOP_LIMIT orders")
        return self

    @field_serializer("quantity", "limit_price", "stop_price")
    def serialize_decimal(self, v: Decimal | None) -> str | None:
        """Serialize Decimal as string to preserve precision."""
        return str(v) if v is not None else None

    @field_serializer("side")
    def serialize_side(self, v: OrderSide) -> str:
        """Serialize OrderSide as string."""
        return str(v)

    @field_serializer("order_type")
    def serialize_order_type(self, v: OrderType) -> str:
        """Serialize OrderType as string."""
        return str(v)

    @field_serializer("time_in_force")
    def serialize_time_in_force(self, v: TimeInForce) -> str:
        """Serialize TimeInForce as string."""
        return str(v)

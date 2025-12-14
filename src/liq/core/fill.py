"""Fill (execution) data model for the LIQ Stack.

The Fill model represents a completed execution of all or part of an order.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator

from liq.core.enums import OrderSide
from liq.core.symbols import validate_symbol


class Fill(BaseModel):
    """Fill representing a completed order execution.

    Attributes:
        fill_id: Unique identifier for this fill
        client_order_id: Reference to the originating order
        symbol: Instrument symbol
        side: Buy or sell
        quantity: Filled quantity (must be > 0)
        price: Execution price (must be > 0)
        commission: Commission paid (must be >= 0)
        slippage: Price slippage from expected (optional)
        timestamp: Fill execution time (UTC, timezone-aware)

    Computed Properties:
        notional_value: quantity * price
        total_cost: notional_value + commission (buy) or -notional_value + commission (sell)

    Validations:
        - quantity > 0
        - price > 0
        - commission >= 0
        - timestamp must be timezone-aware (UTC)
    """

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
    )

    fill_id: UUID
    client_order_id: UUID
    symbol: str
    side: OrderSide
    quantity: Decimal
    price: Decimal
    commission: Decimal
    slippage: Decimal | None = None
    realized_pnl: Decimal | None = None
    provider: str | None = None
    is_partial: bool | None = None
    timestamp: datetime

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

    @field_validator("price")
    @classmethod
    def validate_price_positive(cls, v: Decimal) -> Decimal:
        """Ensure price is positive."""
        if v <= 0:
            raise ValueError("price must be > 0")
        return v

    @field_validator("commission")
    @classmethod
    def validate_commission_non_negative(cls, v: Decimal) -> Decimal:
        """Ensure commission is non-negative."""
        if v < 0:
            raise ValueError("commission must be >= 0")
        return v

    @property
    def notional_value(self) -> Decimal:
        """Calculate notional value: quantity * price."""
        return self.quantity * self.price

    @property
    def total_cost(self) -> Decimal:
        """Calculate total cost including commission.

        For buys: +notional + commission (cash outflow)
        For sells: -notional + commission (net cash inflow)
        """
        if self.side == OrderSide.BUY:
            return self.notional_value + self.commission
        else:
            return -self.notional_value + self.commission

    @field_serializer("quantity", "price", "commission", "slippage", "realized_pnl")
    def serialize_decimal(self, v: Decimal | None) -> str | None:
        """Serialize Decimal as string to preserve precision."""
        return str(v) if v is not None else None

    @field_serializer("side")
    def serialize_side(self, v: OrderSide) -> str:
        """Serialize OrderSide as string."""
        return str(v)

    @field_serializer("provider")
    def serialize_provider(self, v: str | None) -> str | None:
        """Serialize provider."""
        return v

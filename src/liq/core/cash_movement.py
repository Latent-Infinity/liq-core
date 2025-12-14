"""Cash movement model for deposits, withdrawals, dividends, interest, fees."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from liq.core.enums import Currency


class CashMovement(BaseModel):
    """Represents a cash movement."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    timestamp: datetime
    amount: Decimal
    currency: Currency
    movement_type: str = Field(
        pattern="^(deposit|withdrawal|dividend|interest|fee)$"
    )
    description: str | None = None

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp_timezone(cls, v: datetime) -> datetime:
        if v.tzinfo is None or v.tzinfo.utcoffset(v) is None:
            raise ValueError("timestamp must be timezone-aware (UTC expected)")
        return v

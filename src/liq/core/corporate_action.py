"""Corporate action model for splits, dividends, spinoffs, mergers."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CorporateAction(BaseModel):
    """Represents a corporate action event."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    symbol: str
    ex_date: datetime
    action_type: str = Field(pattern="^(split|dividend|spinoff|merger)$")
    ratio: Decimal | None = None
    amount: Decimal | None = None

    @field_validator("ex_date")
    @classmethod
    def validate_timestamp_timezone(cls, v: datetime) -> datetime:
        if v.tzinfo is None or v.tzinfo.utcoffset(v) is None:
            raise ValueError("ex_date must be timezone-aware (UTC expected)")
        return v

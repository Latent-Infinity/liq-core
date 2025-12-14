"""Ledger entry model capturing fills, cash movements, and corporate actions."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from liq.core.cash_movement import CashMovement
from liq.core.corporate_action import CorporateAction
from liq.core.fill import Fill
from liq.core.portfolio import PortfolioState


class LedgerEntry(BaseModel):
    """Single ledger entry for analytics."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    timestamp: datetime
    entry_type: str = Field(pattern="^(fill|cash|corporate_action|margin_call)$")
    fill: Fill | None = None
    cash_movement: CashMovement | None = None
    corporate_action: CorporateAction | None = None
    portfolio_state_after: PortfolioState | None = None

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp_timezone(cls, v: datetime) -> datetime:
        if v.tzinfo is None or v.tzinfo.utcoffset(v) is None:
            raise ValueError("timestamp must be timezone-aware (UTC expected)")
        return v

    @field_validator("fill", "cash_movement", "corporate_action")
    @classmethod
    def validate_conditionals(cls, v, info):  # type: ignore[override]
        entry_type = info.data.get("entry_type")
        if entry_type == "fill" and info.field_name == "fill" and v is None:
            raise ValueError("fill is required when entry_type is fill")
        if entry_type == "cash" and info.field_name == "cash_movement" and v is None:
            raise ValueError("cash_movement is required when entry_type is cash")
        if entry_type == "corporate_action" and info.field_name == "corporate_action" and v is None:
            raise ValueError("corporate_action is required when entry_type is corporate_action")
        return v

    @field_validator("entry_type")
    @classmethod
    def validate_entry_type(cls, v: str) -> str:
        return v

    @model_validator(mode="after")
    def validate_required_payloads(self) -> "LedgerEntry":
        if self.entry_type == "fill" and self.fill is None:
            raise ValueError("fill is required when entry_type is fill")
        if self.entry_type == "cash" and self.cash_movement is None:
            raise ValueError("cash_movement is required when entry_type is cash")
        if self.entry_type == "corporate_action" and self.corporate_action is None:
            raise ValueError("corporate_action is required when entry_type is corporate_action")
        return self

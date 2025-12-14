"""Trade model representing a completed round-trip."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from liq.core.fill import Fill


class Trade(BaseModel):
    """Completed trade with entry/exit fills and summary metrics."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    symbol: str
    entry_fill: Fill
    exit_fill: Fill
    pnl: Decimal
    return_pct: Decimal
    holding_period: int = Field(gt=0)


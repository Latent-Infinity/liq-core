"""TraderOutput and action models (Sections 2.2, 2.3).

Defines SwapAction, RebalanceAction as discriminated union members, and
TraderOutput as the canonical decision output schema. NO_TRADE is
represented as actions=[] with no_trade_rationale.
"""

from decimal import Decimal
from typing import Annotated, Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SwapAction(BaseModel):
    """Exchange one asset for another.

    Decomposes to one or two OrderRequest objects (sell from + buy to).
    """

    model_config = ConfigDict(frozen=True)

    action_type: Literal["SWAP"] = "SWAP"
    from_asset: str
    to_asset: str
    notional: Decimal = Field(gt=0)
    max_slippage_bps: int | None = None


class RebalanceAction(BaseModel):
    """Adjust portfolio to target weights.

    Decomposes to OrderRequest objects for each weight delta above threshold.
    """

    model_config = ConfigDict(frozen=True)

    action_type: Literal["REBALANCE"] = "REBALANCE"
    target_weights: dict[str, float]
    max_slippage_bps: int | None = None

    @field_validator("target_weights")
    @classmethod
    def _validate_non_empty(cls, v: dict[str, float]) -> dict[str, float]:
        if not v:
            msg = "target_weights must not be empty"
            raise ValueError(msg)
        return v


Action = Annotated[
    SwapAction | RebalanceAction,
    Field(discriminator="action_type"),
]


class TraderOutput(BaseModel):
    """Canonical decision output schema.

    actions=[] is the NO_TRADE pattern and requires no_trade_rationale.
    Non-empty actions requires rationales (one per action).
    """

    model_config = ConfigDict(frozen=True)

    actions: list[Action]
    rationales: list[str] = Field(default_factory=list)
    no_trade_rationale: str | None = None

    # Stage-2 optional fields (not risk-bearing)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    invalidation_conditions: dict[str, Any] | None = None
    expected_slippage_bps: float | None = None
    expected_impact_bps: float | None = None

    @model_validator(mode="after")
    def _validate_rationales(self) -> Self:
        if not self.actions:
            # NO_TRADE: require no_trade_rationale
            if not self.no_trade_rationale or not self.no_trade_rationale.strip():
                msg = "no_trade_rationale is required when actions is empty"
                raise ValueError(msg)
        else:
            # Actions present: require rationales matching count
            if len(self.rationales) != len(self.actions):
                msg = (
                    f"rationales length ({len(self.rationales)}) must match "
                    f"actions length ({len(self.actions)})"
                )
                raise ValueError(msg)
        return self

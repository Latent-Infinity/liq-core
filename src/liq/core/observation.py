"""Observation model (Section 2.1).

Compact state snapshot for decision cycles. Includes market features,
portfolio state, risk counters, regime state, risk model outputs, optional
news/scare features, per-source freshness metadata, and degraded context flag.

Supports compact JSON serialization (null features omitted) and canonical
hashing per Section 0.10.
"""

import hashlib
import json
from typing import Any, Literal, Self

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

StalenessClassification = Literal["fresh", "stale", "missing"]

FreshnessStatusType = Literal["nominal", "degraded", "critical_stale"]


class SourceFreshness(BaseModel):
    """Per-source freshness metadata entry.

    Tracks UTC timestamp of last update and staleness classification
    for each data source feeding the observation.
    """

    model_config = ConfigDict(frozen=True)

    source_id: str
    last_update: AwareDatetime
    staleness_classification: StalenessClassification


class Observation(BaseModel):
    """Observation model — compact state snapshot for decision cycles.

    All required fields must be populated for a valid observation. Optional
    news/scare features are omitted from compact serialization when None.
    The ``degraded_context`` flag is auto-computed from freshness metadata
    (True when any source is non-fresh), but can also be explicitly set True.
    """

    model_config = ConfigDict(frozen=True)

    # --- Core features ---
    market_features: dict[str, float]
    portfolio_state: dict[str, Any]
    risk_counters: dict[str, Any]
    regime_state: dict[str, Any]
    risk_model_outputs: dict[str, Any]

    # --- Optional features ---
    news_features: dict[str, Any] | None = None
    scare_trade_features: dict[str, Any] | None = None

    # --- Freshness ---
    freshness_metadata: dict[str, SourceFreshness]
    freshness_status: FreshnessStatusType
    degraded_context: bool = False

    # --- Schema version ---
    schema_version: str = Field(default="1.0")

    @model_validator(mode="after")
    def _compute_degraded_context(self) -> Self:
        """Auto-set degraded_context=True when any source is non-fresh."""
        any_non_fresh = any(
            sf.staleness_classification != "fresh"
            for sf in self.freshness_metadata.values()
        )
        if any_non_fresh and not self.degraded_context:
            object.__setattr__(self, "degraded_context", True)
        return self

    # --- Compact serialization (Section 0.10) ---

    def compact_dump(self) -> dict[str, Any]:
        """Compact JSON-safe dict omitting all None fields."""
        return self.model_dump(mode="json", exclude_none=True)

    def canonical_json(self) -> str:
        """Deterministic JSON string for hashing.

        Uses sorted keys and no whitespace for reproducibility.
        """
        return json.dumps(self.compact_dump(), sort_keys=True, default=str)

    def serialization_hash(self) -> str:
        """SHA-256 hex digest of canonical JSON."""
        return hashlib.sha256(self.canonical_json().encode()).hexdigest()

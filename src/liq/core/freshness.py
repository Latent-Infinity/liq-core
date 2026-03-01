"""Data freshness configuration models (Section 10.2).

Defines per-source staleness rules, criticality tiers, coverage classes,
and global degradation parameters for the trading loop's data quality gate.
"""

from collections import defaultdict
from datetime import timedelta
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SourceFreshnessRule(BaseModel):
    """Per-source staleness rule.

    Each data source has its own staleness threshold rather than a single
    threshold per criticality tier, allowing fine-grained control.
    """

    model_config = ConfigDict(frozen=True)

    source_id: str
    criticality: Literal["critical", "important", "non_critical"]
    staleness_threshold: timedelta
    description: str
    coverage_class: str
    role: Literal["primary", "secondary"]

    @field_validator("staleness_threshold")
    @classmethod
    def validate_positive_threshold(cls, v: timedelta) -> timedelta:
        """staleness_threshold must be strictly positive."""
        if v <= timedelta(0):
            raise ValueError("staleness_threshold must be > 0")
        return v


class FreshnessConfig(BaseModel):
    """Structured per-source freshness configuration.

    Contains a dict of SourceFreshnessRule keyed by source_id, plus global
    degradation parameters. Validates that critical/important coverage classes
    have at least one primary source.
    """

    model_config = ConfigDict(frozen=True)

    sources: dict[str, SourceFreshnessRule]
    de_risk_on_stale: bool
    staleness_sizing_penalty: float = Field(ge=0.0, le=1.0)
    degraded_signal_threshold: float

    @model_validator(mode="after")
    def _validate_coverage_primaries(self) -> Self:
        """Critical/important coverage classes must have >= 1 primary source."""
        # Group sources by coverage_class for critical/important only
        coverage: dict[str, list[SourceFreshnessRule]] = defaultdict(list)
        for rule in self.sources.values():
            if rule.criticality in ("critical", "important"):
                coverage[rule.coverage_class].append(rule)

        for cc, rules in coverage.items():
            if not any(r.role == "primary" for r in rules):
                msg = (
                    f"coverage_class {cc!r} with criticality "
                    f"{rules[0].criticality!r} has no primary source"
                )
                raise ValueError(msg)

        return self

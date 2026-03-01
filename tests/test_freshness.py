"""Tests for FreshnessConfig and SourceFreshnessRule models (Task 0A.11).

Verifies per-source staleness rules, criticality tiers, global degradation
parameters, coverage_class/role validation, and serialization per Section 10.2.
"""

from datetime import timedelta

import pytest
from pydantic import ValidationError

from liq.core.freshness import FreshnessConfig, SourceFreshnessRule

# ---------------------------------------------------------------------------
# SourceFreshnessRule
# ---------------------------------------------------------------------------


class TestSourceFreshnessRule:
    """SourceFreshnessRule field validation."""

    def test_valid_rule(self) -> None:
        rule = SourceFreshnessRule(
            source_id="coinbase_ohlcv",
            criticality="critical",
            staleness_threshold=timedelta(seconds=30),
            description="Coinbase OHLCV bars",
            coverage_class="ohlcv:BTC/USD:1h",
            role="primary",
        )
        assert rule.source_id == "coinbase_ohlcv"
        assert rule.criticality == "critical"
        assert rule.staleness_threshold == timedelta(seconds=30)
        assert rule.role == "primary"

    @pytest.mark.parametrize("criticality", ["critical", "important", "non_critical"])
    def test_valid_criticality_values(self, criticality: str) -> None:
        rule = SourceFreshnessRule(
            source_id="test",
            criticality=criticality,
            staleness_threshold=timedelta(minutes=1),
            description="test source",
            coverage_class="test:class",
            role="primary",
        )
        assert rule.criticality == criticality

    def test_invalid_criticality_rejected(self) -> None:
        with pytest.raises(ValidationError):
            SourceFreshnessRule(
                source_id="test",
                criticality="invalid",  # type: ignore[arg-type]
                staleness_threshold=timedelta(minutes=1),
                description="test source",
                coverage_class="test:class",
                role="primary",
            )

    @pytest.mark.parametrize("role", ["primary", "secondary"])
    def test_valid_role_values(self, role: str) -> None:
        rule = SourceFreshnessRule(
            source_id="test",
            criticality="critical",
            staleness_threshold=timedelta(minutes=1),
            description="test source",
            coverage_class="test:class",
            role=role,
        )
        assert rule.role == role

    def test_invalid_role_rejected(self) -> None:
        with pytest.raises(ValidationError):
            SourceFreshnessRule(
                source_id="test",
                criticality="critical",
                staleness_threshold=timedelta(minutes=1),
                description="test source",
                coverage_class="test:class",
                role="invalid",  # type: ignore[arg-type]
            )

    def test_zero_staleness_threshold_rejected(self) -> None:
        with pytest.raises(ValidationError, match="staleness_threshold"):
            SourceFreshnessRule(
                source_id="test",
                criticality="critical",
                staleness_threshold=timedelta(0),
                description="test source",
                coverage_class="test:class",
                role="primary",
            )

    def test_negative_staleness_threshold_rejected(self) -> None:
        with pytest.raises(ValidationError, match="staleness_threshold"):
            SourceFreshnessRule(
                source_id="test",
                criticality="critical",
                staleness_threshold=timedelta(seconds=-10),
                description="test source",
                coverage_class="test:class",
                role="primary",
            )

    def test_round_trip_serialization(self) -> None:
        rule = SourceFreshnessRule(
            source_id="coinbase_ohlcv",
            criticality="critical",
            staleness_threshold=timedelta(seconds=30),
            description="Coinbase OHLCV bars",
            coverage_class="ohlcv:BTC/USD:1h",
            role="primary",
        )
        json_str = rule.model_dump_json()
        rule2 = SourceFreshnessRule.model_validate_json(json_str)
        assert rule2 == rule

    def test_json_schema_export(self) -> None:
        schema = SourceFreshnessRule.model_json_schema()
        assert "properties" in schema
        assert "source_id" in schema["properties"]
        assert "criticality" in schema["properties"]
        assert "staleness_threshold" in schema["properties"]
        assert "coverage_class" in schema["properties"]
        assert "role" in schema["properties"]


# ---------------------------------------------------------------------------
# FreshnessConfig
# ---------------------------------------------------------------------------


class TestFreshnessConfig:
    """FreshnessConfig validation and structure."""

    def _make_rule(
        self,
        source_id: str = "test_source",
        criticality: str = "critical",
        threshold_s: int = 30,
        coverage_class: str = "test:class",
        role: str = "primary",
    ) -> SourceFreshnessRule:
        return SourceFreshnessRule(
            source_id=source_id,
            criticality=criticality,
            staleness_threshold=timedelta(seconds=threshold_s),
            description=f"Test source {source_id}",
            coverage_class=coverage_class,
            role=role,
        )

    def test_valid_config(self) -> None:
        rule = self._make_rule()
        config = FreshnessConfig(
            sources={rule.source_id: rule},
            de_risk_on_stale=True,
            staleness_sizing_penalty=0.5,
            degraded_signal_threshold=0.7,
        )
        assert config.de_risk_on_stale is True
        assert config.staleness_sizing_penalty == 0.5
        assert config.degraded_signal_threshold == 0.7
        assert "test_source" in config.sources

    def test_staleness_sizing_penalty_bounds(self) -> None:
        rule = self._make_rule()
        # Valid: 0
        FreshnessConfig(
            sources={rule.source_id: rule},
            de_risk_on_stale=False,
            staleness_sizing_penalty=0.0,
            degraded_signal_threshold=0.5,
        )
        # Valid: 1
        FreshnessConfig(
            sources={rule.source_id: rule},
            de_risk_on_stale=False,
            staleness_sizing_penalty=1.0,
            degraded_signal_threshold=0.5,
        )
        # Invalid: > 1
        with pytest.raises(ValidationError):
            FreshnessConfig(
                sources={rule.source_id: rule},
                de_risk_on_stale=False,
                staleness_sizing_penalty=1.5,
                degraded_signal_threshold=0.5,
            )
        # Invalid: < 0
        with pytest.raises(ValidationError):
            FreshnessConfig(
                sources={rule.source_id: rule},
                de_risk_on_stale=False,
                staleness_sizing_penalty=-0.1,
                degraded_signal_threshold=0.5,
            )

    def test_coverage_class_requires_primary_for_critical(self) -> None:
        """Critical coverage_class must have at least one primary source."""
        rule = self._make_rule(
            criticality="critical", coverage_class="price:BTC/USD", role="secondary"
        )
        with pytest.raises(ValidationError, match="primary"):
            FreshnessConfig(
                sources={rule.source_id: rule},
                de_risk_on_stale=False,
                staleness_sizing_penalty=0.5,
                degraded_signal_threshold=0.5,
            )

    def test_coverage_class_requires_primary_for_important(self) -> None:
        """Important coverage_class must have at least one primary source."""
        rule = self._make_rule(
            criticality="important", coverage_class="features:derived", role="secondary"
        )
        with pytest.raises(ValidationError, match="primary"):
            FreshnessConfig(
                sources={rule.source_id: rule},
                de_risk_on_stale=False,
                staleness_sizing_penalty=0.5,
                degraded_signal_threshold=0.5,
            )

    def test_coverage_class_non_critical_allows_no_primary(self) -> None:
        """Non-critical sources don't require a primary."""
        rule = self._make_rule(
            criticality="non_critical", coverage_class="news:feed", role="secondary"
        )
        config = FreshnessConfig(
            sources={rule.source_id: rule},
            de_risk_on_stale=False,
            staleness_sizing_penalty=0.5,
            degraded_signal_threshold=0.5,
        )
        assert len(config.sources) == 1

    def test_multiple_sources_same_coverage_class(self) -> None:
        """Multiple sources can cover the same class if one is primary."""
        primary = self._make_rule(
            source_id="source_a",
            criticality="critical",
            coverage_class="price:BTC/USD",
            role="primary",
        )
        secondary = self._make_rule(
            source_id="source_b",
            criticality="critical",
            coverage_class="price:BTC/USD",
            role="secondary",
        )
        config = FreshnessConfig(
            sources={primary.source_id: primary, secondary.source_id: secondary},
            de_risk_on_stale=True,
            staleness_sizing_penalty=0.5,
            degraded_signal_threshold=0.5,
        )
        assert len(config.sources) == 2

    def test_round_trip_serialization(self) -> None:
        rule = self._make_rule()
        config = FreshnessConfig(
            sources={rule.source_id: rule},
            de_risk_on_stale=True,
            staleness_sizing_penalty=0.5,
            degraded_signal_threshold=0.7,
        )
        json_str = config.model_dump_json()
        config2 = FreshnessConfig.model_validate_json(json_str)
        assert config2.de_risk_on_stale == config.de_risk_on_stale
        assert config2.staleness_sizing_penalty == config.staleness_sizing_penalty
        assert len(config2.sources) == len(config.sources)

    def test_json_schema_export(self) -> None:
        schema = FreshnessConfig.model_json_schema()
        assert "properties" in schema
        assert "sources" in schema["properties"]
        assert "de_risk_on_stale" in schema["properties"]
        assert "staleness_sizing_penalty" in schema["properties"]
        assert "degraded_signal_threshold" in schema["properties"]

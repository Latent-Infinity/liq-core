"""Tests for Observation model (Task 0A.17).

Section 2.1 — Observation space with market_features, portfolio_state,
risk_counters, regime_state, risk_model_outputs, optional news/scare features,
per-source freshness_metadata, freshness_status, degraded_context flag,
compact JSON serialization (omit nulls), and canonical hashing.
"""

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

# Verify type aliases are importable
from liq.core.observation import (  # noqa: F401
    FreshnessStatusType,
    Observation,
    SourceFreshness,
    StalenessClassification,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NOW = datetime.now(UTC)


def _fresh_source(source_id: str = "coinbase_ohlcv") -> SourceFreshness:
    return SourceFreshness(
        source_id=source_id,
        last_update=_NOW,
        staleness_classification="fresh",
    )


def _stale_source(source_id: str = "liq_features") -> SourceFreshness:
    return SourceFreshness(
        source_id=source_id,
        last_update=_NOW - timedelta(hours=1),
        staleness_classification="stale",
    )


def _missing_source(source_id: str = "news_feed") -> SourceFreshness:
    return SourceFreshness(
        source_id=source_id,
        last_update=_NOW - timedelta(days=1),
        staleness_classification="missing",
    )


def _make_observation(**overrides) -> Observation:
    """Build an Observation with sensible defaults."""
    defaults: dict = {
        "market_features": {"midrange_ret": 0.02, "range_ret": 0.05, "rsi": 55.0},
        "portfolio_state": {"cash": "10000.00", "positions": {}},
        "risk_counters": {"trades_today": 2, "realized_loss_today": "50.00"},
        "regime_state": {"volatility": "low", "trend": "neutral"},
        "risk_model_outputs": {"sigma": 0.15, "var_95": 250.0, "cvar_95": 320.0},
        "freshness_metadata": {"coinbase_ohlcv": _fresh_source()},
        "freshness_status": "nominal",
    }
    defaults.update(overrides)
    return Observation(**defaults)


# ---------------------------------------------------------------------------
# SourceFreshness
# ---------------------------------------------------------------------------


class TestSourceFreshness:
    """SourceFreshness sub-model validation."""

    def test_valid_fresh(self) -> None:
        sf = _fresh_source()
        assert sf.source_id == "coinbase_ohlcv"
        assert sf.staleness_classification == "fresh"
        assert sf.last_update.tzinfo is not None

    def test_valid_stale(self) -> None:
        sf = _stale_source()
        assert sf.staleness_classification == "stale"

    def test_valid_missing(self) -> None:
        sf = _missing_source()
        assert sf.staleness_classification == "missing"

    def test_invalid_classification_rejected(self) -> None:
        with pytest.raises(ValidationError):
            SourceFreshness(
                source_id="test",
                last_update=_NOW,
                staleness_classification="unknown",  # type: ignore[arg-type]
            )

    def test_naive_datetime_rejected(self) -> None:
        with pytest.raises(ValidationError):
            SourceFreshness(
                source_id="test",
                last_update=datetime(2024, 1, 1, 12, 0, 0),  # noqa: DTZ001
                staleness_classification="fresh",
            )

    def test_frozen(self) -> None:
        sf = _fresh_source()
        with pytest.raises(ValidationError):
            sf.source_id = "other"  # type: ignore[misc]

    def test_round_trip(self) -> None:
        sf = _fresh_source()
        json_str = sf.model_dump_json()
        sf2 = SourceFreshness.model_validate_json(json_str)
        assert sf2.source_id == sf.source_id
        assert sf2.staleness_classification == sf.staleness_classification


# ---------------------------------------------------------------------------
# Observation — required fields
# ---------------------------------------------------------------------------


class TestObservationRequiredFields:
    """All required fields must be present."""

    def test_all_required_fields_present(self) -> None:
        obs = _make_observation()
        assert obs.market_features["midrange_ret"] == 0.02
        assert obs.portfolio_state["cash"] == "10000.00"
        assert obs.risk_counters["trades_today"] == 2
        assert obs.regime_state["volatility"] == "low"
        assert obs.risk_model_outputs["sigma"] == 0.15
        assert "coinbase_ohlcv" in obs.freshness_metadata
        assert obs.freshness_status == "nominal"

    def test_missing_market_features_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_observation(market_features=None)  # type: ignore[arg-type]

    def test_missing_portfolio_state_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_observation(portfolio_state=None)  # type: ignore[arg-type]

    def test_missing_risk_counters_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_observation(risk_counters=None)  # type: ignore[arg-type]

    def test_missing_regime_state_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_observation(regime_state=None)  # type: ignore[arg-type]

    def test_missing_risk_model_outputs_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_observation(risk_model_outputs=None)  # type: ignore[arg-type]

    def test_missing_freshness_metadata_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_observation(freshness_metadata=None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Observation — optional fields
# ---------------------------------------------------------------------------


class TestObservationOptionalFields:
    """news_features and scare_trade_features are optional."""

    def test_news_features_optional_default_none(self) -> None:
        obs = _make_observation()
        assert obs.news_features is None

    def test_news_features_present(self) -> None:
        obs = _make_observation(
            news_features={"headlines": ["market rally"], "sentiment": 0.8}
        )
        assert obs.news_features is not None
        assert obs.news_features["sentiment"] == 0.8

    def test_scare_trade_features_optional_default_none(self) -> None:
        obs = _make_observation()
        assert obs.scare_trade_features is None

    def test_scare_trade_features_present(self) -> None:
        obs = _make_observation(
            scare_trade_features={
                "trigger_confidence": 0.9,
                "contagion_breadth": 3,
                "category": "earnings_miss",
            }
        )
        assert obs.scare_trade_features is not None
        assert obs.scare_trade_features["trigger_confidence"] == 0.9


# ---------------------------------------------------------------------------
# Freshness metadata — per-source UTC timestamps + staleness classification
# ---------------------------------------------------------------------------


class TestFreshnessMetadata:
    """Per-source freshness_metadata with UTC timestamps + staleness."""

    def test_single_fresh_source(self) -> None:
        obs = _make_observation()
        src = obs.freshness_metadata["coinbase_ohlcv"]
        assert src.last_update.tzinfo is not None
        assert src.staleness_classification == "fresh"

    def test_multiple_sources(self) -> None:
        metadata = {
            "coinbase_ohlcv": _fresh_source("coinbase_ohlcv"),
            "liq_features": _stale_source("liq_features"),
            "news_feed": _missing_source("news_feed"),
        }
        obs = _make_observation(
            freshness_metadata=metadata,
            freshness_status="degraded",
            degraded_context=True,
        )
        assert len(obs.freshness_metadata) == 3
        assert (
            obs.freshness_metadata["coinbase_ohlcv"].staleness_classification == "fresh"
        )
        assert (
            obs.freshness_metadata["liq_features"].staleness_classification == "stale"
        )
        assert obs.freshness_metadata["news_feed"].staleness_classification == "missing"

    def test_freshness_status_nominal(self) -> None:
        obs = _make_observation(freshness_status="nominal")
        assert obs.freshness_status == "nominal"

    def test_freshness_status_degraded(self) -> None:
        obs = _make_observation(
            freshness_status="degraded",
            freshness_metadata={
                "source_a": _fresh_source("source_a"),
                "source_b": _stale_source("source_b"),
            },
            degraded_context=True,
        )
        assert obs.freshness_status == "degraded"

    def test_freshness_status_critical_stale(self) -> None:
        obs = _make_observation(
            freshness_status="critical_stale",
            freshness_metadata={
                "source_a": _stale_source("source_a"),
            },
            degraded_context=True,
        )
        assert obs.freshness_status == "critical_stale"

    def test_invalid_freshness_status_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_observation(freshness_status="invalid")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# degraded_context flag
# ---------------------------------------------------------------------------


class TestDegradedContext:
    """degraded_context flag computed from freshness."""

    def test_defaults_false_when_all_fresh(self) -> None:
        obs = _make_observation(
            freshness_metadata={"source_a": _fresh_source("source_a")},
            freshness_status="nominal",
        )
        assert obs.degraded_context is False

    def test_auto_true_when_stale_source_present(self) -> None:
        """degraded_context auto-computed True when any source is stale."""
        obs = _make_observation(
            freshness_metadata={
                "source_a": _fresh_source("source_a"),
                "source_b": _stale_source("source_b"),
            },
            freshness_status="degraded",
        )
        assert obs.degraded_context is True

    def test_auto_true_when_missing_source_present(self) -> None:
        """degraded_context auto-computed True when any source is missing."""
        obs = _make_observation(
            freshness_metadata={
                "source_a": _fresh_source("source_a"),
                "source_b": _missing_source("source_b"),
            },
            freshness_status="degraded",
        )
        assert obs.degraded_context is True

    def test_explicit_true_overrides(self) -> None:
        """Can explicitly set degraded_context=True even with all fresh sources."""
        obs = _make_observation(
            freshness_metadata={"source_a": _fresh_source("source_a")},
            freshness_status="nominal",
            degraded_context=True,
        )
        assert obs.degraded_context is True


# ---------------------------------------------------------------------------
# Compact JSON serialization
# ---------------------------------------------------------------------------


class TestCompactSerialization:
    """Compact JSON serialization (omit null features) per Section 0.10."""

    def test_compact_dump_omits_none_fields(self) -> None:
        obs = _make_observation()
        compact = obs.compact_dump()
        assert "news_features" not in compact
        assert "scare_trade_features" not in compact
        assert "market_features" in compact

    def test_compact_dump_includes_present_optional(self) -> None:
        obs = _make_observation(
            news_features={"headline": "test"},
        )
        compact = obs.compact_dump()
        assert "news_features" in compact
        assert compact["news_features"]["headline"] == "test"

    def test_canonical_json_deterministic(self) -> None:
        obs1 = _make_observation()
        obs2 = _make_observation()
        assert obs1.canonical_json() == obs2.canonical_json()

    def test_canonical_json_sorted_keys(self) -> None:
        import json

        obs = _make_observation()
        canonical = obs.canonical_json()
        parsed = json.loads(canonical)
        # Top-level keys should be sorted
        keys = list(parsed.keys())
        assert keys == sorted(keys)

    def test_serialization_hash_sha256(self) -> None:
        obs = _make_observation()
        h = obs.serialization_hash()
        assert len(h) == 64  # SHA-256 hex length
        assert all(c in "0123456789abcdef" for c in h)

    def test_serialization_hash_deterministic(self) -> None:
        obs1 = _make_observation()
        obs2 = _make_observation()
        assert obs1.serialization_hash() == obs2.serialization_hash()

    def test_serialization_hash_changes_with_data(self) -> None:
        obs1 = _make_observation(market_features={"rsi": 50.0})
        obs2 = _make_observation(market_features={"rsi": 60.0})
        assert obs1.serialization_hash() != obs2.serialization_hash()


# ---------------------------------------------------------------------------
# Round-trip serialization and JSON Schema export
# ---------------------------------------------------------------------------


class TestObservationSerialization:
    """Round-trip serialization and JSON Schema export."""

    def test_round_trip_json(self) -> None:
        obs = _make_observation(
            news_features={"headline": "test"},
            scare_trade_features={"trigger_confidence": 0.9},
        )
        json_str = obs.model_dump_json()
        obs2 = Observation.model_validate_json(json_str)
        assert obs2.market_features == obs.market_features
        assert obs2.freshness_status == obs.freshness_status
        assert obs2.degraded_context == obs.degraded_context
        assert obs2.news_features == obs.news_features

    def test_round_trip_dict(self) -> None:
        obs = _make_observation()
        d = obs.model_dump()
        obs2 = Observation.model_validate(d)
        assert obs2.market_features == obs.market_features

    def test_json_schema_export(self) -> None:
        schema = Observation.model_json_schema()
        assert isinstance(schema, dict)
        assert "properties" in schema
        props = schema["properties"]
        assert "market_features" in props
        assert "portfolio_state" in props
        assert "risk_counters" in props
        assert "regime_state" in props
        assert "risk_model_outputs" in props
        assert "news_features" in props
        assert "scare_trade_features" in props
        assert "freshness_metadata" in props
        assert "freshness_status" in props
        assert "degraded_context" in props
        assert "schema_version" in props

    def test_schema_version_default(self) -> None:
        obs = _make_observation()
        assert obs.schema_version == "1.0"

    def test_frozen(self) -> None:
        obs = _make_observation()
        with pytest.raises(ValidationError):
            obs.market_features = {}  # type: ignore[misc]

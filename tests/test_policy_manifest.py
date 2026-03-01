"""Tests for PolicyManifest model (Task 0A.15).

Section 2.6 — retrieval sub-model, engine_type, provider_id, model_id,
cross-field validation, index_ids canonical keys, hash computation.
"""

from typing import get_args

import pytest
from pydantic import ValidationError

from liq.core.policy_manifest import (
    PolicyManifest,
    RetrievalConfig,
    RetrievalParams,
)

# ---------------------------------------------------------------------------
# RetrievalParams
# ---------------------------------------------------------------------------


class TestRetrievalParams:
    """RetrievalParams fields and hash computation."""

    def test_valid_params(self) -> None:
        params = RetrievalParams(
            top_k=5,
            filters={"asset": "BTC/USD"},
        )
        assert params.top_k == 5
        assert params.filters == {"asset": "BTC/USD"}

    def test_round_trip(self) -> None:
        params = RetrievalParams(
            top_k=10,
            filters={"regime": "high_vol"},
            score_thresholds={"min_score": 0.7},
        )
        json_str = params.model_dump_json()
        params2 = RetrievalParams.model_validate_json(json_str)
        assert params2.top_k == params.top_k
        assert params2.filters == params.filters


# ---------------------------------------------------------------------------
# RetrievalConfig cross-field validation
# ---------------------------------------------------------------------------


class TestRetrievalConfig:
    """Cross-field validation per Section 2.6 table."""

    def test_disabled_no_requirements(self) -> None:
        """enabled=False, required=False, empty modes — valid."""
        rc = RetrievalConfig(enabled=False)
        assert rc.enabled is False
        assert rc.required is False
        assert rc.modes == []

    def test_disabled_required_invalid(self) -> None:
        """enabled=False, required=True — invalid."""
        with pytest.raises(ValidationError, match="require.*disabled"):
            RetrievalConfig(enabled=False, required=True)

    def test_enabled_empty_modes_invalid(self) -> None:
        """enabled=True, modes=[] — invalid."""
        with pytest.raises(ValidationError, match="mode"):
            RetrievalConfig(
                enabled=True,
                modes=[],
                vector_store_version="snap_v1",
                index_ids={"few_shot": "liq_trade_few_shot"},
                embedding_model_id="Qwen/Qwen3-Embedding-0.6B",
                embedding_model_version="0.6B",
                prompt_injection_budget_tokens=500,
                retrieval_params=RetrievalParams(top_k=5, filters={}),
            )

    def test_enabled_no_vector_store_version_invalid(self) -> None:
        """enabled=True, vector_store_version absent — invalid."""
        with pytest.raises(ValidationError, match="vector_store_version"):
            RetrievalConfig(
                enabled=True,
                modes=["few_shot"],
                index_ids={"few_shot": "liq_trade_few_shot"},
                embedding_model_id="Qwen/Qwen3-Embedding-0.6B",
                embedding_model_version="0.6B",
                prompt_injection_budget_tokens=500,
                retrieval_params=RetrievalParams(top_k=5, filters={}),
            )

    def test_enabled_valid_graceful(self) -> None:
        """enabled=True, required=False, non-empty modes, version present — valid."""
        rc = RetrievalConfig(
            enabled=True,
            required=False,
            modes=["few_shot"],
            vector_store_version="snap_v1",
            index_ids={"few_shot": "liq_trade_few_shot"},
            embedding_model_id="Qwen/Qwen3-Embedding-0.6B",
            embedding_model_version="0.6B",
            prompt_injection_budget_tokens=500,
            retrieval_params=RetrievalParams(top_k=5, filters={}),
        )
        assert rc.enabled is True
        assert rc.required is False

    def test_enabled_valid_mandatory(self) -> None:
        """enabled=True, required=True — valid."""
        rc = RetrievalConfig(
            enabled=True,
            required=True,
            modes=["few_shot", "decision_history"],
            vector_store_version="snap_v2",
            index_ids={
                "few_shot": "liq_trade_few_shot",
                "decision_history": "liq_trade_decisions",
            },
            embedding_model_id="Qwen/Qwen3-Embedding-0.6B",
            embedding_model_version="0.6B",
            prompt_injection_budget_tokens=500,
            retrieval_params=RetrievalParams(top_k=5, filters={}),
        )
        assert rc.required is True

    def test_index_ids_must_cover_modes(self) -> None:
        """Every mode must have a corresponding index_ids key."""
        with pytest.raises(ValidationError, match="index_ids"):
            RetrievalConfig(
                enabled=True,
                modes=["few_shot", "news_event"],
                vector_store_version="snap_v1",
                index_ids={"few_shot": "liq_trade_few_shot"},  # missing news_event
                embedding_model_id="Qwen/Qwen3-Embedding-0.6B",
                embedding_model_version="0.6B",
                prompt_injection_budget_tokens=500,
                retrieval_params=RetrievalParams(top_k=5, filters={}),
            )

    def test_retrieval_params_hash_is_sha256(self) -> None:
        """retrieval_params_hash is auto-computed SHA-256."""
        rc = RetrievalConfig(
            enabled=True,
            modes=["few_shot"],
            vector_store_version="snap_v1",
            index_ids={"few_shot": "liq_trade_few_shot"},
            embedding_model_id="Qwen/Qwen3-Embedding-0.6B",
            embedding_model_version="0.6B",
            prompt_injection_budget_tokens=500,
            retrieval_params=RetrievalParams(top_k=5, filters={}),
        )
        assert rc.retrieval_params_hash is not None
        assert len(rc.retrieval_params_hash) == 64  # SHA-256 hex length
        assert all(c in "0123456789abcdef" for c in rc.retrieval_params_hash)

    def test_hash_deterministic(self) -> None:
        """Same params produce same hash."""
        kwargs = {
            "enabled": True,
            "modes": ["few_shot"],
            "vector_store_version": "snap_v1",
            "index_ids": {"few_shot": "liq_trade_few_shot"},
            "embedding_model_id": "Qwen/Qwen3-Embedding-0.6B",
            "embedding_model_version": "0.6B",
            "prompt_injection_budget_tokens": 500,
            "retrieval_params": RetrievalParams(top_k=5, filters={"a": "b"}),
        }
        rc1 = RetrievalConfig(**kwargs)
        rc2 = RetrievalConfig(**kwargs)
        assert rc1.retrieval_params_hash == rc2.retrieval_params_hash

    def test_round_trip(self) -> None:
        rc = RetrievalConfig(
            enabled=True,
            required=True,
            modes=["few_shot"],
            vector_store_version="snap_v1",
            index_ids={"few_shot": "liq_trade_few_shot"},
            embedding_model_id="Qwen/Qwen3-Embedding-0.6B",
            embedding_model_version="0.6B",
            prompt_injection_budget_tokens=500,
            retrieval_params=RetrievalParams(top_k=5, filters={}),
        )
        json_str = rc.model_dump_json()
        rc2 = RetrievalConfig.model_validate_json(json_str)
        assert rc2.enabled == rc.enabled
        assert rc2.retrieval_params_hash == rc.retrieval_params_hash


# ---------------------------------------------------------------------------
# PolicyManifest
# ---------------------------------------------------------------------------


class TestPolicyManifest:
    """PolicyManifest top-level fields and engine_type validation."""

    def _make_manifest(self, **overrides) -> PolicyManifest:
        defaults = {
            "policy_id": "policy_v1",
            "engine_type": "llm",
            "provider_id": "anthropic",
            "model_id": "claude-sonnet-4-20250514",
            "prompt_manifest_hash": "abc123",
            "features_config_hash": "def456",
            "risk_config_hash": "ghi789",
            "regime_model_id": "regime_v1",
            "attribution_model_id": "attr_v1",
            "retrieval": RetrievalConfig(enabled=False),
        }
        defaults.update(overrides)
        return PolicyManifest(**defaults)

    def test_valid_llm_manifest(self) -> None:
        m = self._make_manifest()
        assert m.engine_type == "llm"
        assert m.provider_id == "anthropic"

    def test_valid_rl_manifest(self) -> None:
        m = self._make_manifest(
            engine_type="rl",
            provider_id=None,
            model_weights_ref="checkpoints/rl_v1.pt",
        )
        assert m.engine_type == "rl"
        assert m.provider_id is None

    def test_valid_rules_manifest(self) -> None:
        m = self._make_manifest(
            engine_type="rules",
            provider_id=None,
        )
        assert m.engine_type == "rules"

    def test_engine_type_validates(self) -> None:
        with pytest.raises(ValidationError):
            self._make_manifest(engine_type="invalid")

    def test_engine_type_literal_values(self) -> None:
        from liq.core.policy_manifest import EngineType

        values = set(get_args(EngineType))
        assert values == {"llm", "rl", "rules"}

    def test_llm_requires_provider_id(self) -> None:
        """engine_type='llm' must have provider_id."""
        with pytest.raises(ValidationError, match="provider_id"):
            self._make_manifest(engine_type="llm", provider_id=None)

    def test_json_schema_export(self) -> None:
        schema = PolicyManifest.model_json_schema()
        assert "properties" in schema
        assert "engine_type" in schema["properties"]
        assert "retrieval" in schema["properties"]

    def test_round_trip(self) -> None:
        m = self._make_manifest()
        json_str = m.model_dump_json()
        m2 = PolicyManifest.model_validate_json(json_str)
        assert m2.policy_id == m.policy_id
        assert m2.engine_type == m.engine_type

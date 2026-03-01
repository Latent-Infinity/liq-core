"""Policy manifest model (Section 2.6, Section 0.11).

PolicyManifest is the versioned identity of a trading policy: prompt + features
+ sizing rules + risk config + risk model + regime model + attribution model +
retrieval config + corpus snapshot.
"""

import hashlib
import json
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

EngineType = Literal["llm", "rl", "rules"]

RetrievalMode = Literal["few_shot", "decision_history", "news_event", "scare_case"]


class RetrievalParams(BaseModel):
    """Structured retrieval parameters for vector store queries."""

    model_config = ConfigDict(frozen=True)

    top_k: int = Field(gt=0)
    filters: dict[str, Any]
    reranker: dict[str, Any] | None = None
    score_thresholds: dict[str, Any] | None = None
    dedupe_rules: dict[str, Any] | None = None


class RetrievalConfig(BaseModel):
    """Retrieval sub-model of PolicyManifest.

    Cross-field validation enforces the invariant table from Section 2.6.
    """

    model_config = ConfigDict(frozen=True)

    enabled: bool = False
    required: bool = False
    modes: list[RetrievalMode] = Field(default_factory=list)
    vector_store_version: str | None = None
    index_ids: dict[str, str] = Field(default_factory=dict)
    embedding_model_id: str | None = None
    embedding_model_version: str | None = None
    prompt_injection_budget_tokens: int | None = None
    retrieval_params: RetrievalParams | None = None
    retrieval_params_hash: str | None = None

    @model_validator(mode="after")
    def _validate_cross_fields(self) -> Self:
        # Cannot require retrieval that is disabled
        if not self.enabled and self.required:
            msg = "Cannot require retrieval that is disabled"
            raise ValueError(msg)

        if self.enabled:
            # Enabled retrieval must specify at least one mode
            if not self.modes:
                msg = "Enabled retrieval must specify at least one mode"
                raise ValueError(msg)

            # Enabled retrieval must bind to a snapshot version
            if not self.vector_store_version:
                msg = "vector_store_version is required when retrieval is enabled"
                raise ValueError(msg)

            # Every mode must have a corresponding index_ids key
            missing = {m for m in self.modes if m not in self.index_ids}
            if missing:
                msg = f"index_ids missing keys for modes: {sorted(missing)}"
                raise ValueError(msg)

            # Auto-compute retrieval_params_hash
            if self.retrieval_params is not None and self.retrieval_params_hash is None:
                params_json = json.dumps(
                    self.retrieval_params.model_dump(),
                    sort_keys=True,
                    default=str,
                )
                h = hashlib.sha256(params_json.encode()).hexdigest()
                object.__setattr__(self, "retrieval_params_hash", h)

        return self


class PolicyManifest(BaseModel):
    """Versioned policy identity.

    Includes engine type, provider/model references, component hashes,
    and retrieval configuration.
    """

    model_config = ConfigDict(frozen=True)

    policy_id: str
    engine_type: EngineType
    provider_id: str | None = None
    model_id: str | None = None
    model_weights_ref: str | None = None
    prompt_manifest_hash: str | None = None
    features_config_hash: str | None = None
    risk_config_hash: str | None = None
    regime_model_id: str | None = None
    attribution_model_id: str | None = None
    retrieval: RetrievalConfig = Field(default_factory=lambda: RetrievalConfig())

    @model_validator(mode="after")
    def _validate_engine_requirements(self) -> Self:
        # LLM engines require provider_id
        if self.engine_type == "llm" and not self.provider_id:
            msg = "provider_id is required when engine_type='llm'"
            raise ValueError(msg)
        return self

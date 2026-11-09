"""UTC normalization for shared model timestamps."""

from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

import pytest
from pydantic import BaseModel, ValidationError

from liq.core.cash_movement import CashMovement
from liq.core.corporate_action import CorporateAction
from liq.core.fill import Fill
from liq.core.instrument import ProviderMetadata
from liq.core.ledger import LedgerEntry
from liq.core.observation import Observation, SourceFreshness
from liq.core.portfolio import PortfolioState
from liq.core.position import Position
from liq.core.quote import Quote

_MODELS: list[tuple[type[BaseModel], str, dict[str, Any]]] = [
    (
        Quote,
        "timestamp",
        {"symbol": "AAPL", "bid": 1, "ask": 1, "bid_size": 1, "ask_size": 1},
    ),
    (
        Fill,
        "timestamp",
        {
            "fill_id": UUID(int=1),
            "client_order_id": UUID(int=2),
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 1,
            "price": 1,
            "commission": 0,
        },
    ),
    (
        Position,
        "timestamp",
        {"symbol": "AAPL", "quantity": 1, "average_price": 1, "realized_pnl": 0},
    ),
    (PortfolioState, "timestamp", {"cash": Decimal("1"), "positions": {}}),
    (
        CashMovement,
        "timestamp",
        {"amount": 1, "currency": "USD", "movement_type": "deposit"},
    ),
    (CorporateAction, "ex_date", {"symbol": "AAPL", "action_type": "split"}),
    (LedgerEntry, "timestamp", {"entry_type": "margin_call"}),
    (
        ProviderMetadata,
        "last_successful_fetch",
        {
            "provider_name": "example",
            "asset_classes": ["equity"],
            "api_endpoint": "https://example.com",
            "rate_limit_per_minute": 1,
            "enabled": True,
            "priority": 1,
            "authentication_required": False,
        },
    ),
    (
        SourceFreshness,
        "last_update",
        {"source_id": "example", "staleness_classification": "fresh"},
    ),
]


@pytest.mark.parametrize("model,field,values", _MODELS)
@pytest.mark.parametrize("offset", [-5, 5])
def test_timestamp_normalizes_across_utc_midnight(
    model: type[BaseModel], field: str, values: dict[str, Any], offset: int
) -> None:
    instant = datetime(2024, 1, 2, 1 if offset < 0 else 23, tzinfo=UTC)
    local_time = instant.astimezone(timezone(timedelta(hours=offset)))
    result = model.model_validate({**values, field: local_time})
    assert getattr(result, field).tzinfo == UTC
    assert getattr(result, field) == instant
    assert result.model_dump(mode="json")[field] == instant.isoformat().replace(
        "+00:00", "Z"
    )


@pytest.mark.parametrize("model,field,values", _MODELS)
def test_timestamp_rejects_naive_input(
    model: type[BaseModel], field: str, values: dict[str, Any]
) -> None:
    with pytest.raises(ValidationError):
        model.model_validate({**values, field: datetime(2024, 1, 1)})


def test_provider_optional_timestamp_remains_none() -> None:
    model, field, values = _MODELS[7]
    assert getattr(model.model_validate({**values, field: None}), field) is None


def test_observation_hash_matches_for_equivalent_instants() -> None:
    instant = datetime(2024, 1, 2, 1, tzinfo=UTC)
    observations = []
    for timestamp in (instant, instant.astimezone(timezone(timedelta(hours=-5)))):
        source = SourceFreshness(
            source_id="example", last_update=timestamp, staleness_classification="fresh"
        )
        observations.append(
            Observation(
                market_features={},
                portfolio_state={},
                risk_counters={},
                regime_state={},
                risk_model_outputs={},
                freshness_metadata={"example": source},
                freshness_status="nominal",
            )
        )
    assert observations[0].canonical_json() == observations[1].canonical_json()
    assert observations[0].serialization_hash() == observations[1].serialization_hash()
    assert "2024-01-02T01:00:00Z" in observations[0].canonical_json()

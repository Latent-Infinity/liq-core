"""Contract tests for shared regime labels."""

from __future__ import annotations

import json

from liq.core import RegimeId as PublicRegimeId
from liq.core.enums import RegimeId


def test_regime_id_members_and_values_are_stable() -> None:
    assert [(member.name, member.value) for member in RegimeId] == [
        ("trend", "trend"),
        ("range", "range"),
        ("neutral", "neutral"),
        ("fallback", "fallback"),
        ("no_trade", "no_trade"),
        ("empty", "empty"),
    ]


def test_regime_id_uses_str_enum_semantics() -> None:
    assert RegimeId.trend == "trend"
    assert json.loads(json.dumps({"regime": RegimeId.range})) == {"regime": "range"}


def test_regime_id_public_export_matches_enum_class() -> None:
    assert PublicRegimeId is RegimeId

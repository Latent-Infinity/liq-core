"""Tests for TraderOutput, SwapAction, RebalanceAction (Task 0A.19).

Sections 2.2, 2.3 — discriminated union actions, NO_TRADE pattern,
per-action rationales, optional Stage-2 fields, round-trip serialization.
"""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from liq.core.trader_output import RebalanceAction, SwapAction, TraderOutput

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _swap(**overrides) -> SwapAction:
    defaults: dict = {
        "from_asset": "USDC",
        "to_asset": "BTC",
        "notional": Decimal("1000.00"),
    }
    defaults.update(overrides)
    return SwapAction(**defaults)


def _rebalance(**overrides) -> RebalanceAction:
    defaults: dict = {
        "target_weights": {"BTC": 0.6, "ETH": 0.3, "USDC": 0.1},
    }
    defaults.update(overrides)
    return RebalanceAction(**defaults)


def _no_trade_output(**overrides) -> TraderOutput:
    defaults: dict = {
        "actions": [],
        "no_trade_rationale": "Risk budget exhausted",
    }
    defaults.update(overrides)
    return TraderOutput(**defaults)


def _trade_output(**overrides) -> TraderOutput:
    defaults: dict = {
        "actions": [_swap()],
        "rationales": ["Momentum signal strong for BTC"],
    }
    defaults.update(overrides)
    return TraderOutput(**defaults)


# ---------------------------------------------------------------------------
# SwapAction fields
# ---------------------------------------------------------------------------


class TestSwapAction:
    """SWAP action fields: from_asset, to_asset, notional, max_slippage_bps."""

    def test_valid_swap(self) -> None:
        action = _swap()
        assert action.action_type == "SWAP"
        assert action.from_asset == "USDC"
        assert action.to_asset == "BTC"
        assert action.notional == Decimal("1000.00")
        assert action.max_slippage_bps is None

    def test_swap_with_slippage(self) -> None:
        action = _swap(max_slippage_bps=50)
        assert action.max_slippage_bps == 50

    def test_swap_notional_must_be_positive(self) -> None:
        with pytest.raises(ValidationError, match="notional"):
            _swap(notional=Decimal("0"))

    def test_swap_negative_notional_rejected(self) -> None:
        with pytest.raises(ValidationError, match="notional"):
            _swap(notional=Decimal("-100"))

    def test_swap_from_asset_required(self) -> None:
        with pytest.raises(ValidationError):
            SwapAction(to_asset="BTC", notional=Decimal("100"))  # type: ignore[call-arg]

    def test_swap_to_asset_required(self) -> None:
        with pytest.raises(ValidationError):
            SwapAction(from_asset="USDC", notional=Decimal("100"))  # type: ignore[call-arg]

    def test_swap_frozen(self) -> None:
        action = _swap()
        with pytest.raises(ValidationError):
            action.notional = Decimal("999")  # type: ignore[misc]

    def test_swap_round_trip(self) -> None:
        action = _swap(max_slippage_bps=25)
        json_str = action.model_dump_json()
        action2 = SwapAction.model_validate_json(json_str)
        assert action2.from_asset == action.from_asset
        assert action2.notional == action.notional
        assert action2.max_slippage_bps == action.max_slippage_bps


# ---------------------------------------------------------------------------
# RebalanceAction fields
# ---------------------------------------------------------------------------


class TestRebalanceAction:
    """REBALANCE action fields: target_weights, max_slippage_bps."""

    def test_valid_rebalance(self) -> None:
        action = _rebalance()
        assert action.action_type == "REBALANCE"
        assert action.target_weights == {"BTC": 0.6, "ETH": 0.3, "USDC": 0.1}
        assert action.max_slippage_bps is None

    def test_rebalance_with_slippage(self) -> None:
        action = _rebalance(max_slippage_bps=30)
        assert action.max_slippage_bps == 30

    def test_rebalance_empty_weights_rejected(self) -> None:
        with pytest.raises(ValidationError, match="target_weights"):
            _rebalance(target_weights={})

    def test_rebalance_frozen(self) -> None:
        action = _rebalance()
        with pytest.raises(ValidationError):
            action.target_weights = {}  # type: ignore[misc]

    def test_rebalance_round_trip(self) -> None:
        action = _rebalance(max_slippage_bps=10)
        json_str = action.model_dump_json()
        action2 = RebalanceAction.model_validate_json(json_str)
        assert action2.target_weights == action.target_weights
        assert action2.max_slippage_bps == action.max_slippage_bps


# ---------------------------------------------------------------------------
# TraderOutput — NO_TRADE pattern
# ---------------------------------------------------------------------------


class TestNoTradePattern:
    """actions=[] requires no_trade_rationale."""

    def test_valid_no_trade(self) -> None:
        output = _no_trade_output()
        assert output.actions == []
        assert output.no_trade_rationale == "Risk budget exhausted"

    def test_no_trade_missing_rationale_rejected(self) -> None:
        with pytest.raises(ValidationError, match="no_trade_rationale"):
            TraderOutput(actions=[])

    def test_no_trade_empty_rationale_rejected(self) -> None:
        with pytest.raises(ValidationError, match="no_trade_rationale"):
            TraderOutput(actions=[], no_trade_rationale="")

    def test_no_trade_whitespace_rationale_rejected(self) -> None:
        with pytest.raises(ValidationError, match="no_trade_rationale"):
            TraderOutput(actions=[], no_trade_rationale="   ")


# ---------------------------------------------------------------------------
# TraderOutput — actions present, rationales per action
# ---------------------------------------------------------------------------


class TestActionsWithRationales:
    """actions=[...] requires rationales array of matching length."""

    def test_valid_single_action(self) -> None:
        output = _trade_output()
        assert len(output.actions) == 1
        assert len(output.rationales) == 1

    def test_valid_multiple_actions(self) -> None:
        output = TraderOutput(
            actions=[_swap(), _rebalance()],
            rationales=["Swap for momentum", "Rebalance for risk"],
        )
        assert len(output.actions) == 2
        assert len(output.rationales) == 2

    def test_missing_rationales_when_actions_present(self) -> None:
        with pytest.raises(ValidationError, match="rationale"):
            TraderOutput(actions=[_swap()])

    def test_rationale_count_mismatch_rejected(self) -> None:
        with pytest.raises(ValidationError, match="rationale"):
            TraderOutput(
                actions=[_swap(), _rebalance()],
                rationales=["Only one rationale"],
            )

    def test_mixed_action_types(self) -> None:
        output = TraderOutput(
            actions=[_swap(), _rebalance()],
            rationales=["Swap rationale", "Rebalance rationale"],
        )
        assert output.actions[0].action_type == "SWAP"
        assert output.actions[1].action_type == "REBALANCE"


# ---------------------------------------------------------------------------
# Optional Stage-2 fields
# ---------------------------------------------------------------------------


class TestOptionalFields:
    """confidence, invalidation_conditions, etc. accepted but not required."""

    def test_confidence_optional_default_none(self) -> None:
        output = _trade_output()
        assert output.confidence is None

    def test_confidence_accepted(self) -> None:
        output = _trade_output(confidence=0.85)
        assert output.confidence == 0.85

    def test_confidence_bounds_zero_to_one(self) -> None:
        _trade_output(confidence=0.0)
        _trade_output(confidence=1.0)
        with pytest.raises(ValidationError):
            _trade_output(confidence=1.5)
        with pytest.raises(ValidationError):
            _trade_output(confidence=-0.1)

    def test_invalidation_conditions_optional(self) -> None:
        output = _trade_output()
        assert output.invalidation_conditions is None

    def test_invalidation_conditions_accepted(self) -> None:
        output = _trade_output(
            invalidation_conditions={"price_reversal": True, "timeout_s": 300}
        )
        assert output.invalidation_conditions is not None

    def test_expected_slippage_bps_optional(self) -> None:
        output = _trade_output()
        assert output.expected_slippage_bps is None

    def test_expected_slippage_bps_accepted(self) -> None:
        output = _trade_output(expected_slippage_bps=12.5)
        assert output.expected_slippage_bps == 12.5

    def test_expected_impact_bps_optional(self) -> None:
        output = _trade_output()
        assert output.expected_impact_bps is None

    def test_expected_impact_bps_accepted(self) -> None:
        output = _trade_output(expected_impact_bps=5.0)
        assert output.expected_impact_bps == 5.0


# ---------------------------------------------------------------------------
# Discriminated union parsing
# ---------------------------------------------------------------------------


class TestDiscriminatedUnion:
    """JSON → correct action type via discriminated union."""

    def test_swap_from_json(self) -> None:
        import json

        data = {
            "actions": [
                {
                    "action_type": "SWAP",
                    "from_asset": "USDC",
                    "to_asset": "ETH",
                    "notional": "500.00",
                }
            ],
            "rationales": ["ETH momentum"],
        }
        output = TraderOutput.model_validate_json(json.dumps(data))
        assert isinstance(output.actions[0], SwapAction)
        assert output.actions[0].from_asset == "USDC"

    def test_rebalance_from_json(self) -> None:
        import json

        data = {
            "actions": [
                {
                    "action_type": "REBALANCE",
                    "target_weights": {"BTC": 0.5, "ETH": 0.5},
                }
            ],
            "rationales": ["Equal weight rebalance"],
        }
        output = TraderOutput.model_validate_json(json.dumps(data))
        assert isinstance(output.actions[0], RebalanceAction)
        assert output.actions[0].target_weights["BTC"] == 0.5

    def test_mixed_actions_from_json(self) -> None:
        import json

        data = {
            "actions": [
                {
                    "action_type": "SWAP",
                    "from_asset": "USDC",
                    "to_asset": "BTC",
                    "notional": "100",
                },
                {
                    "action_type": "REBALANCE",
                    "target_weights": {"BTC": 0.7, "USDC": 0.3},
                },
            ],
            "rationales": ["Buy BTC", "Rebalance"],
        }
        output = TraderOutput.model_validate_json(json.dumps(data))
        assert isinstance(output.actions[0], SwapAction)
        assert isinstance(output.actions[1], RebalanceAction)


# ---------------------------------------------------------------------------
# Round-trip serialization and JSON Schema
# ---------------------------------------------------------------------------


class TestTraderOutputSerialization:
    """Round-trip serialization and JSON Schema export."""

    def test_round_trip_json_no_trade(self) -> None:
        output = _no_trade_output()
        json_str = output.model_dump_json()
        output2 = TraderOutput.model_validate_json(json_str)
        assert output2.no_trade_rationale == output.no_trade_rationale
        assert output2.actions == []

    def test_round_trip_json_with_actions(self) -> None:
        output = _trade_output(
            confidence=0.9,
            expected_slippage_bps=10.0,
        )
        json_str = output.model_dump_json()
        output2 = TraderOutput.model_validate_json(json_str)
        assert len(output2.actions) == 1
        assert output2.actions[0].action_type == "SWAP"
        assert output2.confidence == 0.9

    def test_round_trip_dict(self) -> None:
        output = _trade_output()
        d = output.model_dump()
        output2 = TraderOutput.model_validate(d)
        assert output2.rationales == output.rationales

    def test_json_schema_export(self) -> None:
        schema = TraderOutput.model_json_schema()
        assert isinstance(schema, dict)
        assert "properties" in schema
        props = schema["properties"]
        assert "actions" in props
        assert "rationales" in props
        assert "no_trade_rationale" in props
        assert "confidence" in props
        assert "invalidation_conditions" in props
        assert "expected_slippage_bps" in props
        assert "expected_impact_bps" in props

    def test_swap_schema_export(self) -> None:
        schema = SwapAction.model_json_schema()
        assert "properties" in schema
        assert "from_asset" in schema["properties"]
        assert "to_asset" in schema["properties"]
        assert "notional" in schema["properties"]

    def test_rebalance_schema_export(self) -> None:
        schema = RebalanceAction.model_json_schema()
        assert "properties" in schema
        assert "target_weights" in schema["properties"]

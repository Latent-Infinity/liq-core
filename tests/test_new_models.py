"""Tests for newly added PRD models."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from liq.core.cash_movement import CashMovement
from liq.core.corporate_action import CorporateAction
from liq.core.ledger import LedgerEntry
from liq.core.trade import Trade
from liq.core.fill import Fill


def sample_fill(ts: datetime) -> Fill:
    return Fill(
        fill_id=uuid4(),
        client_order_id=uuid4(),
        symbol="EUR_USD",
        side="buy",
        quantity=Decimal("100"),
        price=Decimal("1.1000"),
        commission=Decimal("0.1"),
        provider="oanda",
        timestamp=ts,
    )


def test_trade_model() -> None:
    ts = datetime(2024, 1, 1, tzinfo=UTC)
    entry = sample_fill(ts)
    exit_fill = sample_fill(ts.replace(hour=2))
    trade = Trade(
        symbol="EUR_USD",
        entry_fill=entry,
        exit_fill=exit_fill,
        pnl=Decimal("10.0"),
        return_pct=Decimal("0.01"),
        holding_period=5,
    )
    assert trade.pnl == Decimal("10.0")
    assert trade.holding_period == 5


def test_cash_movement_requires_timezone() -> None:
    with pytest.raises(ValidationError):
        CashMovement(
            timestamp=datetime(2024, 1, 1),  # naive
            amount=Decimal("100"),
            currency="USD",
            movement_type="deposit",
        )


def test_cash_movement_valid() -> None:
    cm = CashMovement(
        timestamp=datetime(2024, 1, 1, tzinfo=UTC),
        amount=Decimal("100"),
        currency="USD",
        movement_type="deposit",
    )
    assert cm.amount == Decimal("100")


def test_corporate_action_requires_timezone() -> None:
    with pytest.raises(ValidationError):
        CorporateAction(
            symbol="AAPL",
            ex_date=datetime(2024, 1, 1),
            action_type="split",
            ratio=Decimal("2"),
        )


def test_ledger_entry_conditionals() -> None:
    ts = datetime(2024, 1, 1, tzinfo=UTC)
    with pytest.raises(ValidationError):
        LedgerEntry(timestamp=ts, entry_type="fill")  # missing fill

    entry = LedgerEntry(timestamp=ts, entry_type="fill", fill=sample_fill(ts))
    assert entry.fill is not None

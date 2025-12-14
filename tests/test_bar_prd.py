"""PRD-aligned tests for Bar derived fields."""

from decimal import Decimal
from datetime import datetime, timezone

from liq.core.bar import Bar


def test_true_range_midrange() -> None:
    bar = Bar(
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
        symbol="EUR_USD",
        open=Decimal("1.0"),
        high=Decimal("2.0"),
        low=Decimal("0.5"),
        close=Decimal("1.5"),
        volume=Decimal("10"),
    )
    prev_mid = Decimal("1.2")
    assert bar.true_range_midrange(prev_mid) == Decimal("1.5")  # max(range=1.5, |1.25-1.2|=0.05)


def test_true_range_hl() -> None:
    bar = Bar(
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
        symbol="EUR_USD",
        open=Decimal("1.0"),
        high=Decimal("2.0"),
        low=Decimal("0.5"),
        close=Decimal("1.5"),
        volume=Decimal("10"),
    )
    assert bar.true_range_hl(Decimal("1.8"), Decimal("0.4")) == Decimal("1.5")

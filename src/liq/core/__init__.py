"""
liq-core: Core data models for the LIQ Stack.

This package provides the foundational data structures, enums, and type
definitions used across the entire LIQ ecosystem.
"""

from liq.core.bar import Bar
from liq.core.cash_movement import CashMovement
from liq.core.corporate_action import CorporateAction
from liq.core.enums import (
    AssetClass,
    Currency,
    OrderSide,
    OrderStatus,
    OrderType,
    Provider,
    Timeframe,
    TimeInForce,
)
from liq.core.fill import Fill
from liq.core.instrument import Instrument, ProviderMetadata
from liq.core.ledger import LedgerEntry
from liq.core.order import OrderRequest
from liq.core.portfolio import PortfolioState
from liq.core.position import Position
from liq.core.quote import Quote
from liq.core.results import BatchResult, FetchResult, UpdateResult
from liq.core.trade import Trade
from liq.core.symbols import normalize_symbol, parse_symbol, validate_symbol
from liq.core.validation import ValidationResult

__all__ = [
    # Models
    "Bar",
    "BatchResult",
    "CashMovement",
    "CorporateAction",
    "FetchResult",
    "Fill",
    "Instrument",
    "LedgerEntry",
    "OrderRequest",
    "PortfolioState",
    "Position",
    "ProviderMetadata",
    "Quote",
    "Trade",
    "UpdateResult",
    "ValidationResult",
    # Enums
    "AssetClass",
    "Currency",
    "OrderSide",
    "OrderStatus",
    "OrderType",
    "Provider",
    "Timeframe",
    "TimeInForce",
    # Symbol utilities
    "normalize_symbol",
    "parse_symbol",
    "validate_symbol",
]

__version__ = "0.2.0"

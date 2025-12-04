"""Symbol normalization utilities for the LIQ Stack.

Provides functions to normalize, parse, and validate trading symbols
across different asset classes and providers.
"""

import re

from liq.core.enums import AssetClass

# Known quote currencies for crypto parsing (ordered by length, longest first)
_CRYPTO_QUOTES = ["USDT", "USDC", "BUSD", "USD", "BTC", "ETH", "EUR", "GBP"]

# Regex pattern for valid normalized symbols
_VALID_SYMBOL_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9_-]{0,18}[A-Z0-9]$|^[A-Z0-9]{2}$")


def normalize_symbol(symbol: str, asset_class: AssetClass) -> str:
    """Normalize a symbol to canonical format.

    Args:
        symbol: Raw symbol string from any provider
        asset_class: Type of asset (FOREX, CRYPTO, EQUITY)

    Returns:
        Normalized symbol in canonical format:
        - FOREX: BASE_QUOTE (e.g., EUR_USD)
        - CRYPTO: BASE-QUOTE (e.g., BTC-USD)
        - EQUITY: TICKER (e.g., AAPL)

    Examples:
        >>> normalize_symbol("EUR/USD", AssetClass.FOREX)
        'EUR_USD'
        >>> normalize_symbol("btcusdt", AssetClass.CRYPTO)
        'BTC-USDT'
        >>> normalize_symbol("aapl", AssetClass.EQUITY)
        'AAPL'
    """
    # Strip whitespace and uppercase
    symbol = symbol.strip().upper()

    # Remove exchange prefix (e.g., "BINANCE:BTCUSDT" -> "BTCUSDT")
    if ":" in symbol:
        symbol = symbol.split(":")[-1]

    if asset_class == AssetClass.FOREX:
        return _normalize_forex(symbol)
    elif asset_class == AssetClass.CRYPTO:
        return _normalize_crypto(symbol)
    else:
        # Equity and others: just uppercase ticker
        return symbol


def _normalize_forex(symbol: str) -> str:
    """Normalize forex pair to BASE_QUOTE format."""
    # Replace common separators with underscore
    symbol = symbol.replace("/", "_").replace("-", "_")

    # If no separator, try to split 6-char pairs
    if "_" not in symbol and len(symbol) == 6:
        return f"{symbol[:3]}_{symbol[3:]}"

    return symbol


def _normalize_crypto(symbol: str) -> str:
    """Normalize crypto pair to BASE-QUOTE format."""
    # Replace underscore with hyphen
    symbol = symbol.replace("_", "-")

    # If already has hyphen, just return
    if "-" in symbol:
        return symbol

    # Try to find quote currency and split
    for quote in _CRYPTO_QUOTES:
        if symbol.endswith(quote):
            base = symbol[: -len(quote)]
            if base:  # Ensure we have a base currency
                return f"{base}-{quote}"

    # Fallback: assume 3-char base if symbol is 6+ chars
    if len(symbol) >= 6:
        return f"{symbol[:3]}-{symbol[3:]}"

    return symbol


def parse_symbol(canonical: str) -> tuple[str, str]:
    """Parse a canonical symbol into base and quote components.

    Args:
        canonical: Normalized symbol string

    Returns:
        Tuple of (base, quote). For equity symbols, quote is empty string.

    Examples:
        >>> parse_symbol("EUR_USD")
        ('EUR', 'USD')
        >>> parse_symbol("BTC-USD")
        ('BTC', 'USD')
        >>> parse_symbol("AAPL")
        ('AAPL', '')
    """
    # Try underscore (forex)
    if "_" in canonical:
        parts = canonical.split("_", 1)
        return (parts[0], parts[1])

    # Try hyphen (crypto)
    if "-" in canonical:
        parts = canonical.split("-", 1)
        return (parts[0], parts[1])

    # Equity or single asset
    return (canonical, "")


def validate_symbol(symbol: str) -> bool:
    """Validate that a symbol matches the canonical format.

    Valid symbols:
    - Contain only uppercase letters, digits, underscore, or hyphen
    - Are between 2-20 characters
    - Start and end with alphanumeric

    Args:
        symbol: Symbol string to validate

    Returns:
        True if symbol is valid, False otherwise

    Examples:
        >>> validate_symbol("EUR_USD")
        True
        >>> validate_symbol("BTC-USD")
        True
        >>> validate_symbol("eur/usd")
        False
    """
    if not symbol:
        return False

    if len(symbol) < 2 or len(symbol) > 20:
        return False

    return bool(_VALID_SYMBOL_PATTERN.match(symbol))

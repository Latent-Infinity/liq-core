"""Tests for liq.core.symbols module."""

from liq.core.enums import AssetClass
from liq.core.symbols import normalize_symbol, parse_symbol, validate_symbol


class TestNormalizeSymbol:
    """Tests for normalize_symbol function."""

    # Forex normalization
    def test_normalize_forex_with_slash(self) -> None:
        assert normalize_symbol("EUR/USD", AssetClass.FOREX) == "EUR_USD"

    def test_normalize_forex_lowercase(self) -> None:
        assert normalize_symbol("eur_usd", AssetClass.FOREX) == "EUR_USD"

    def test_normalize_forex_mixed_case(self) -> None:
        assert normalize_symbol("Eur_Usd", AssetClass.FOREX) == "EUR_USD"

    def test_normalize_forex_already_normalized(self) -> None:
        assert normalize_symbol("EUR_USD", AssetClass.FOREX) == "EUR_USD"

    def test_normalize_forex_usd_jpy(self) -> None:
        assert normalize_symbol("usd/jpy", AssetClass.FOREX) == "USD_JPY"

    def test_normalize_forex_gbp_chf(self) -> None:
        assert normalize_symbol("GBP-CHF", AssetClass.FOREX) == "GBP_CHF"

    # Crypto normalization
    def test_normalize_crypto_btc_usd(self) -> None:
        assert normalize_symbol("BTCUSD", AssetClass.CRYPTO) == "BTC-USD"

    def test_normalize_crypto_lowercase(self) -> None:
        assert normalize_symbol("btcusdt", AssetClass.CRYPTO) == "BTC-USDT"

    def test_normalize_crypto_with_exchange_prefix(self) -> None:
        assert normalize_symbol("BINANCE:BTCUSDT", AssetClass.CRYPTO) == "BTC-USDT"

    def test_normalize_crypto_already_hyphenated(self) -> None:
        assert normalize_symbol("BTC-USD", AssetClass.CRYPTO) == "BTC-USD"

    def test_normalize_crypto_eth_btc(self) -> None:
        assert normalize_symbol("ethbtc", AssetClass.CRYPTO) == "ETH-BTC"

    def test_normalize_crypto_sol_usdc(self) -> None:
        assert normalize_symbol("SOLUSDC", AssetClass.CRYPTO) == "SOL-USDC"

    # Equity normalization
    def test_normalize_equity_uppercase(self) -> None:
        assert normalize_symbol("AAPL", AssetClass.EQUITY) == "AAPL"

    def test_normalize_equity_lowercase(self) -> None:
        assert normalize_symbol("aapl", AssetClass.EQUITY) == "AAPL"

    def test_normalize_equity_mixed_case(self) -> None:
        assert normalize_symbol("Googl", AssetClass.EQUITY) == "GOOGL"

    def test_normalize_equity_tsla(self) -> None:
        assert normalize_symbol("tsla", AssetClass.EQUITY) == "TSLA"


class TestParseSymbol:
    """Tests for parse_symbol function."""

    def test_parse_forex_symbol(self) -> None:
        base, quote = parse_symbol("EUR_USD")
        assert base == "EUR"
        assert quote == "USD"

    def test_parse_crypto_symbol(self) -> None:
        base, quote = parse_symbol("BTC-USD")
        assert base == "BTC"
        assert quote == "USD"

    def test_parse_forex_usd_jpy(self) -> None:
        base, quote = parse_symbol("USD_JPY")
        assert base == "USD"
        assert quote == "JPY"

    def test_parse_crypto_eth_btc(self) -> None:
        base, quote = parse_symbol("ETH-BTC")
        assert base == "ETH"
        assert quote == "BTC"

    def test_parse_equity_returns_symbol_and_empty(self) -> None:
        """Equity symbols have no quote currency."""
        base, quote = parse_symbol("AAPL")
        assert base == "AAPL"
        assert quote == ""

    def test_parse_symbol_preserves_case(self) -> None:
        """Parsing should preserve case of input."""
        base, quote = parse_symbol("EUR_USD")
        assert base == "EUR"
        assert quote == "USD"


class TestValidateSymbol:
    """Tests for validate_symbol function."""

    # Valid symbols
    def test_validate_forex_symbol(self) -> None:
        assert validate_symbol("EUR_USD") is True

    def test_validate_crypto_symbol(self) -> None:
        assert validate_symbol("BTC-USD") is True

    def test_validate_equity_symbol(self) -> None:
        assert validate_symbol("AAPL") is True

    def test_validate_numeric_in_symbol(self) -> None:
        assert validate_symbol("BRK-A") is True

    def test_validate_symbol_with_numbers(self) -> None:
        assert validate_symbol("ES2024") is True

    # Invalid symbols
    def test_validate_lowercase_invalid(self) -> None:
        assert validate_symbol("eur_usd") is False

    def test_validate_slash_invalid(self) -> None:
        assert validate_symbol("EUR/USD") is False

    def test_validate_space_invalid(self) -> None:
        assert validate_symbol("EUR USD") is False

    def test_validate_special_chars_invalid(self) -> None:
        assert validate_symbol("EUR@USD") is False

    def test_validate_empty_invalid(self) -> None:
        assert validate_symbol("") is False

    def test_validate_colon_invalid(self) -> None:
        assert validate_symbol("BINANCE:BTCUSDT") is False


class TestSymbolRoundTrip:
    """Integration tests for symbol normalization round-trips."""

    def test_forex_normalize_then_validate(self) -> None:
        """Normalized forex symbols should be valid."""
        raw = "eur/usd"
        normalized = normalize_symbol(raw, AssetClass.FOREX)
        assert validate_symbol(normalized) is True

    def test_crypto_normalize_then_validate(self) -> None:
        """Normalized crypto symbols should be valid."""
        raw = "BINANCE:btcusdt"
        normalized = normalize_symbol(raw, AssetClass.CRYPTO)
        assert validate_symbol(normalized) is True

    def test_equity_normalize_then_validate(self) -> None:
        """Normalized equity symbols should be valid."""
        raw = "aapl"
        normalized = normalize_symbol(raw, AssetClass.EQUITY)
        assert validate_symbol(normalized) is True

    def test_normalize_then_parse_forex(self) -> None:
        """Normalized forex symbols should be parseable."""
        normalized = normalize_symbol("EUR/USD", AssetClass.FOREX)
        base, quote = parse_symbol(normalized)
        assert base == "EUR"
        assert quote == "USD"

    def test_normalize_then_parse_crypto(self) -> None:
        """Normalized crypto symbols should be parseable."""
        normalized = normalize_symbol("BTCUSDT", AssetClass.CRYPTO)
        base, quote = parse_symbol(normalized)
        assert base == "BTC"
        assert quote == "USDT"


class TestEdgeCases:
    """Edge case tests for symbol handling."""

    def test_normalize_three_letter_crypto(self) -> None:
        """Three-letter base currencies should work."""
        assert normalize_symbol("BTCUSD", AssetClass.CRYPTO) == "BTC-USD"

    def test_normalize_four_letter_crypto(self) -> None:
        """Four-letter currencies like USDT should work."""
        assert normalize_symbol("ETHUSDT", AssetClass.CRYPTO) == "ETH-USDT"

    def test_normalize_strips_whitespace(self) -> None:
        """Leading/trailing whitespace should be stripped."""
        assert normalize_symbol("  EUR_USD  ", AssetClass.FOREX) == "EUR_USD"

    def test_validate_single_char_invalid(self) -> None:
        """Single character symbols are invalid."""
        assert validate_symbol("A") is False

    def test_validate_very_long_symbol(self) -> None:
        """Very long symbols should be invalid (arbitrary limit)."""
        assert validate_symbol("A" * 50) is False

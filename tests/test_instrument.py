"""Tests for liq.core.instrument module."""

from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from liq.core.instrument import Instrument, ProviderMetadata


class TestInstrumentCreation:
    """Tests for Instrument model creation."""

    def test_create_forex_instrument(self) -> None:
        instrument = Instrument(
            symbol="EUR/USD",
            provider="oanda",
            canonical_symbol="EUR_USD",
            asset_class="forex",
            name="Euro vs US Dollar",
            base_currency="EUR",
            quote_currency="USD",
            tick_size=Decimal("0.00001"),
            lot_size=Decimal("1000"),
            active=True,
        )
        assert instrument.symbol == "EUR/USD"
        assert instrument.canonical_symbol == "EUR_USD"
        assert instrument.asset_class == "forex"
        assert instrument.base_currency == "EUR"
        assert instrument.quote_currency == "USD"

    def test_create_crypto_instrument(self) -> None:
        instrument = Instrument(
            symbol="BTCUSDT",
            provider="binance",
            canonical_symbol="BTC-USDT",
            asset_class="crypto",
            name="Bitcoin vs Tether",
            base_currency="BTC",
            quote_currency="USDT",
            tick_size=Decimal("0.01"),
            lot_size=Decimal("0.001"),
            active=True,
        )
        assert instrument.canonical_symbol == "BTC-USDT"
        assert instrument.asset_class == "crypto"

    def test_create_equity_instrument(self) -> None:
        instrument = Instrument(
            symbol="AAPL",
            provider="polygon",
            canonical_symbol="AAPL",
            asset_class="equity",
            name="Apple Inc.",
            base_currency="AAPL",
            quote_currency="USD",
            tick_size=Decimal("0.01"),
            lot_size=Decimal("1"),
            active=True,
        )
        assert instrument.canonical_symbol == "AAPL"
        assert instrument.asset_class == "equity"

    def test_instrument_with_trading_hours(self) -> None:
        trading_hours = {
            "market_open": "09:30",
            "market_close": "16:00",
            "timezone": "America/New_York",
        }
        instrument = Instrument(
            symbol="AAPL",
            provider="polygon",
            canonical_symbol="AAPL",
            asset_class="equity",
            name="Apple Inc.",
            base_currency="AAPL",
            quote_currency="USD",
            tick_size=Decimal("0.01"),
            lot_size=Decimal("1"),
            active=True,
            trading_hours=trading_hours,
        )
        assert instrument.trading_hours is not None
        assert instrument.trading_hours["market_open"] == "09:30"

    def test_instrument_inactive(self) -> None:
        instrument = Instrument(
            symbol="DELISTED",
            provider="polygon",
            canonical_symbol="DELISTED",
            asset_class="equity",
            name="Delisted Company",
            base_currency="DELISTED",
            quote_currency="USD",
            tick_size=Decimal("0.01"),
            lot_size=Decimal("1"),
            active=False,
        )
        assert not instrument.active


class TestInstrumentValidation:
    """Tests for Instrument validation."""

    def test_rejects_non_positive_tick_size(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            Instrument(
                symbol="EUR/USD",
                provider="oanda",
                canonical_symbol="EUR_USD",
                asset_class="forex",
                name="Euro vs US Dollar",
                base_currency="EUR",
                quote_currency="USD",
                tick_size=Decimal("0"),
                lot_size=Decimal("1000"),
                active=True,
            )
        assert "tick_size" in str(exc_info.value).lower()

    def test_rejects_negative_tick_size(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            Instrument(
                symbol="EUR/USD",
                provider="oanda",
                canonical_symbol="EUR_USD",
                asset_class="forex",
                name="Euro vs US Dollar",
                base_currency="EUR",
                quote_currency="USD",
                tick_size=Decimal("-0.00001"),
                lot_size=Decimal("1000"),
                active=True,
            )
        assert "tick_size" in str(exc_info.value).lower()

    def test_rejects_non_positive_lot_size(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            Instrument(
                symbol="EUR/USD",
                provider="oanda",
                canonical_symbol="EUR_USD",
                asset_class="forex",
                name="Euro vs US Dollar",
                base_currency="EUR",
                quote_currency="USD",
                tick_size=Decimal("0.00001"),
                lot_size=Decimal("0"),
                active=True,
            )
        assert "lot_size" in str(exc_info.value).lower()


class TestInstrumentSerialization:
    """Tests for Instrument serialization."""

    def test_json_serialization(self) -> None:
        instrument = Instrument(
            symbol="EUR/USD",
            provider="oanda",
            canonical_symbol="EUR_USD",
            asset_class="forex",
            name="Euro vs US Dollar",
            base_currency="EUR",
            quote_currency="USD",
            tick_size=Decimal("0.00001"),
            lot_size=Decimal("1000"),
            active=True,
        )
        json_str = instrument.model_dump_json()
        assert "EUR_USD" in json_str
        assert "forex" in json_str

    def test_json_roundtrip(self) -> None:
        instrument = Instrument(
            symbol="EUR/USD",
            provider="oanda",
            canonical_symbol="EUR_USD",
            asset_class="forex",
            name="Euro vs US Dollar",
            base_currency="EUR",
            quote_currency="USD",
            tick_size=Decimal("0.00001"),
            lot_size=Decimal("1000"),
            active=True,
        )
        json_str = instrument.model_dump_json()
        instrument2 = Instrument.model_validate_json(json_str)
        assert instrument.symbol == instrument2.symbol
        assert instrument.canonical_symbol == instrument2.canonical_symbol
        assert instrument.tick_size == instrument2.tick_size


class TestProviderMetadataCreation:
    """Tests for ProviderMetadata model creation."""

    def test_create_provider_metadata(self) -> None:
        metadata = ProviderMetadata(
            provider_name="oanda",
            asset_classes=["forex"],
            api_endpoint="https://api-fxpractice.oanda.com",
            rate_limit_per_minute=120,
            enabled=True,
            priority=1,
            authentication_required=True,
        )
        assert metadata.provider_name == "oanda"
        assert "forex" in metadata.asset_classes
        assert metadata.rate_limit_per_minute == 120
        assert metadata.enabled
        assert metadata.priority == 1

    def test_create_provider_with_multiple_asset_classes(self) -> None:
        metadata = ProviderMetadata(
            provider_name="alpaca",
            asset_classes=["equity", "crypto"],
            api_endpoint="https://api.alpaca.markets",
            rate_limit_per_minute=200,
            enabled=True,
            priority=2,
            authentication_required=True,
        )
        assert len(metadata.asset_classes) == 2
        assert "equity" in metadata.asset_classes
        assert "crypto" in metadata.asset_classes

    def test_create_provider_with_optional_fields(self, sample_timestamp: datetime) -> None:
        metadata = ProviderMetadata(
            provider_name="polygon",
            asset_classes=["equity"],
            api_endpoint="https://api.polygon.io",
            rate_limit_per_minute=5,
            enabled=True,
            priority=3,
            authentication_required=True,
            rate_limit_per_day=10000,
            historical_data_limit_years=5,
            last_successful_fetch=sample_timestamp,
        )
        assert metadata.rate_limit_per_day == 10000
        assert metadata.historical_data_limit_years == 5
        assert metadata.last_successful_fetch == sample_timestamp

    def test_disabled_provider(self) -> None:
        metadata = ProviderMetadata(
            provider_name="deprecated",
            asset_classes=["forex"],
            api_endpoint="https://old.api.com",
            rate_limit_per_minute=60,
            enabled=False,
            priority=99,
            authentication_required=False,
        )
        assert not metadata.enabled


class TestProviderMetadataValidation:
    """Tests for ProviderMetadata validation."""

    def test_rejects_non_positive_rate_limit(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ProviderMetadata(
                provider_name="test",
                asset_classes=["forex"],
                api_endpoint="https://api.test.com",
                rate_limit_per_minute=0,
                enabled=True,
                priority=1,
                authentication_required=True,
            )
        assert "rate_limit" in str(exc_info.value).lower()

    def test_rejects_zero_priority(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ProviderMetadata(
                provider_name="test",
                asset_classes=["forex"],
                api_endpoint="https://api.test.com",
                rate_limit_per_minute=60,
                enabled=True,
                priority=0,
                authentication_required=True,
            )
        assert "priority" in str(exc_info.value).lower()

    def test_rejects_negative_priority(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ProviderMetadata(
                provider_name="test",
                asset_classes=["forex"],
                api_endpoint="https://api.test.com",
                rate_limit_per_minute=60,
                enabled=True,
                priority=-1,
                authentication_required=True,
            )
        assert "priority" in str(exc_info.value).lower()


class TestProviderMetadataSerialization:
    """Tests for ProviderMetadata serialization."""

    def test_json_serialization(self) -> None:
        metadata = ProviderMetadata(
            provider_name="oanda",
            asset_classes=["forex"],
            api_endpoint="https://api-fxpractice.oanda.com",
            rate_limit_per_minute=120,
            enabled=True,
            priority=1,
            authentication_required=True,
        )
        json_str = metadata.model_dump_json()
        assert "oanda" in json_str
        assert "forex" in json_str

    def test_json_roundtrip(self) -> None:
        metadata = ProviderMetadata(
            provider_name="oanda",
            asset_classes=["forex", "crypto"],
            api_endpoint="https://api-fxpractice.oanda.com",
            rate_limit_per_minute=120,
            enabled=True,
            priority=1,
            authentication_required=True,
            rate_limit_per_day=5000,
        )
        json_str = metadata.model_dump_json()
        metadata2 = ProviderMetadata.model_validate_json(json_str)
        assert metadata.provider_name == metadata2.provider_name
        assert metadata.asset_classes == metadata2.asset_classes
        assert metadata.rate_limit_per_day == metadata2.rate_limit_per_day

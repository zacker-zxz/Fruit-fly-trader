"""Unit tests verifying security fixes and parameter bounds validation."""

import os
import pytest
from pydantic import ValidationError
from starlette.middleware.cors import CORSMiddleware

from api.server import (
    app,
    SimulationStartRequest,
    SpeedUpdateRequest,
    MultiplierUpdateRequest,
)
from market.dataset_manager import (
    validate_dataset_path,
    load_candles_with_offset,
    DATA_RAW_DIR,
)
from trading.micro_trading import MicroTradingEngine, DEFAULT_USD_INR_RATE


class TestPathTraversalPrevention:
    """Tests that arbitrary file reading and path traversal are strictly prevented."""

    @pytest.mark.parametrize("malicious_path", [
        "../../etc/passwd",
        "..\\..\\windows\\win.ini",
        "../secrets.json",
        "sub/dataset.csv",
        "C:\\Windows\\System32\\calc.exe",
        "/etc/shadow",
        "....//....//file.csv",
        "malicious.txt",
        "",
        "   ",
    ])
    def test_validate_dataset_path_rejects_traversal(self, malicious_path):
        with pytest.raises(ValueError):
            validate_dataset_path(malicious_path)

    def test_validate_dataset_path_accepts_valid_csv(self):
        # ensure_datasets_exist should provide BTC_USD_1m.csv
        path = validate_dataset_path("BTC_USD_1m.csv")
        assert os.path.isabs(path)
        assert path.endswith("BTC_USD_1m.csv")
        assert os.path.realpath(path).startswith(os.path.realpath(DATA_RAW_DIR))

    def test_load_candles_with_offset_rejects_traversal(self):
        with pytest.raises(ValueError):
            load_candles_with_offset("../../../test.csv")


class TestCORSConfiguration:
    """Tests that CORS does not expose credentials with wildcard origins."""

    def test_cors_middleware_installed(self):
        cors_middlewares = [
            m for m in app.user_middleware
            if m.cls == CORSMiddleware
        ]
        assert len(cors_middlewares) >= 1
        cors_options = cors_middlewares[0].kwargs
        # Either origins are explicit (not '*'), or allow_credentials must be False
        origins = cors_options.get("allow_origins", [])
        allow_credentials = cors_options.get("allow_credentials", False)
        if "*" in origins:
            assert allow_credentials is False, "allow_credentials MUST be False when allow_origins contains '*'"
        else:
            assert all(o.startswith("http") for o in origins)


class TestConfigBoundsValidation:
    """Tests that strict Pydantic bounds prevent resource exhaustion / DoS."""

    def test_valid_request(self):
        req = SimulationStartRequest(
            dataset="BTC_USD_1m.csv",
            max_neurons=800,
            multiplier=10,
            speed=5,
            initial_capital_inr=500000.0,
            usd_inr_rate=84.50,
        )
        assert req.max_neurons == 800
        assert req.multiplier == 10
        assert req.usd_inr_rate == 84.50

    def test_max_neurons_bounds(self):
        # > 5000 should raise ValidationError (prevents DoS)
        with pytest.raises(ValidationError):
            SimulationStartRequest(dataset="BTC_USD_1m.csv", max_neurons=1000000)

        # < 50 should raise ValidationError
        with pytest.raises(ValidationError):
            SimulationStartRequest(dataset="BTC_USD_1m.csv", max_neurons=10)

    def test_speed_and_multiplier_bounds(self):
        with pytest.raises(ValidationError):
            SpeedUpdateRequest(speed=200)

        with pytest.raises(ValidationError):
            SpeedUpdateRequest(speed=0)

        with pytest.raises(ValidationError):
            MultiplierUpdateRequest(multiplier=100)

        with pytest.raises(ValidationError):
            MultiplierUpdateRequest(multiplier=0)

    def test_pydantic_rejects_path_traversal_in_dataset(self):
        with pytest.raises(ValidationError):
            SimulationStartRequest(dataset="../../secret.csv")

        with pytest.raises(ValidationError):
            SimulationStartRequest(dataset="secret.txt")


class TestConfigurableExchangeRate:
    """Tests that USD/INR rate is configurable and properly converts metrics."""

    def test_custom_exchange_rate_in_trading_engine(self):
        custom_rate = 90.0
        engine = MicroTradingEngine(
            initial_capital_inr=900000.0,
            usd_inr_rate=custom_rate,
        )
        summary = engine.get_wallet_summary()
        assert summary["usd_inr_rate"] == custom_rate
        # 900,000 INR at 90.0 rate = 10,000 USD
        assert summary["equity_usd"] == pytest.approx(10000.0, rel=1e-2)

    def test_dynamic_exchange_rate_update(self):
        engine = MicroTradingEngine(
            initial_capital_inr=837500.0,
            usd_inr_rate=DEFAULT_USD_INR_RATE,
        )
        summary1 = engine.get_wallet_summary()
        assert summary1["equity_usd"] == pytest.approx(10000.0, rel=1e-2)

        # Update FX rate dynamically
        engine.set_usd_inr_rate(100.0)
        summary2 = engine.get_wallet_summary()
        assert summary2["usd_inr_rate"] == 100.0
        assert summary2["equity_usd"] == pytest.approx(8375.0, rel=1e-2)

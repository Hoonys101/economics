import pytest
from unittest.mock import MagicMock
from modules.finance.engines.monetary_engine import MonetaryEngine
from modules.finance.engines.api import MonetaryStateDTO, MarketSnapshotDTO

@pytest.fixture
def mock_config():
    config = MagicMock()
    config.CB_TAYLOR_ALPHA = 1.5
    config.CB_TAYLOR_BETA = 0.5
    return config

@pytest.fixture
def monetary_engine(mock_config):
    return MonetaryEngine(mock_config)

class TestMonetaryEngine:
    def test_calculate_rate_neutral(self, monetary_engine):
        # Neutral: Inflation = Target, Gap = 0
        # Rate should be r* + pi = 0.02 + 0.02 = 0.04

        state: MonetaryStateDTO = {
            "tick": 100,
            "current_base_rate": 0.04,
            "potential_gdp": 1000.0,
            "inflation_target": 0.02
        }

        market: MarketSnapshotDTO = {
            "tick": 100,
            "inflation_rate_annual": 0.02,
            "current_gdp": 1000.0
        }

        decision = monetary_engine.calculate_rate(state, market)

        assert decision["new_base_rate"] == pytest.approx(0.04)

    def test_calculate_rate_high_inflation(self, monetary_engine):
        # Inflation 4% (>2%), Gap 0
        # Taylor = 0.02 + 0.04 + 1.5*(0.04-0.02) + 0.5*0
        #        = 0.06 + 1.5*0.02
        #        = 0.06 + 0.03 = 0.09

        state: MonetaryStateDTO = {
            "tick": 100,
            "current_base_rate": 0.04,
            "potential_gdp": 1000.0,
            "inflation_target": 0.02
        }

        market: MarketSnapshotDTO = {
            "tick": 100,
            "inflation_rate_annual": 0.04,
            "current_gdp": 1000.0
        }

        decision = monetary_engine.calculate_rate(state, market)

        # Should be smoothed. Target 0.09. Current 0.04. Delta 0.05. Max change 0.0025.
        # Result 0.04 + 0.0025 = 0.0425

        assert decision["new_base_rate"] == pytest.approx(0.0425)

    def test_calculate_rate_recession(self, monetary_engine):
        # Inflation 2%, Gap -10% (-0.1)
        # Taylor = 0.02 + 0.02 + 1.5*0 + 0.5*-0.1
        #        = 0.04 - 0.05 = -0.01
        # ZLB -> 0.0

        state: MonetaryStateDTO = {
            "tick": 100,
            "current_base_rate": 0.04,
            "potential_gdp": 1000.0,
            "inflation_target": 0.02
        }

        market: MarketSnapshotDTO = {
            "tick": 100,
            "inflation_rate_annual": 0.02,
            "current_gdp": 900.0
        }

        decision = monetary_engine.calculate_rate(state, market)

        # Target 0.0. Current 0.04. Delta -0.04.
        # Result 0.04 - 0.0025 = 0.0375

        assert decision["new_base_rate"] == pytest.approx(0.0375)

    def test_strategy_override(self, monetary_engine):
        state: MonetaryStateDTO = {
            "tick": 100,
            "current_base_rate": 0.05,
            "potential_gdp": 1000.0,
            "inflation_target": 0.02,
            "override_target_rate": 0.10
        }

        market: MarketSnapshotDTO = {
            "tick": 100,
            "inflation_rate_annual": 0.02,
            "current_gdp": 1000.0
        }

        decision = monetary_engine.calculate_rate(state, market)

        # Target overridden to 0.10. Current 0.05.
        # Smoothing applies. 0.05 + 0.0025 = 0.0525

        assert decision["new_base_rate"] == pytest.approx(0.0525)

    def test_rate_multiplier(self, monetary_engine):
        # Normal Taylor = 0.04 (Neutral). Multiplier 2.0 -> 0.08.
        state: MonetaryStateDTO = {
            "tick": 100,
            "current_base_rate": 0.04,
            "potential_gdp": 1000.0,
            "inflation_target": 0.02,
            "rate_multiplier": 2.0
        }

        market: MarketSnapshotDTO = {
            "tick": 100,
            "inflation_rate_annual": 0.02,
            "current_gdp": 1000.0
        }

        decision = monetary_engine.calculate_rate(state, market)

        # Target 0.08. Current 0.04.
        # Smoothed -> 0.0425

        assert decision["new_base_rate"] == pytest.approx(0.0425)

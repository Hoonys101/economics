import pytest
from unittest.mock import MagicMock
from collections import deque
from modules.household.econ_component import EconComponent
from simulation.ai.api import Personality

class TestEconComponent:
    @pytest.fixture
    def mock_owner(self):
        owner = MagicMock()
        owner.goods_info_map = {
            "food": {"id": "food", "initial_price": 10.0},
            "water": {"id": "water", "initial_price": 5.0}
        }
        owner.personality = Personality.CONSERVATIVE
        owner.logger = MagicMock()
        return owner

    @pytest.fixture
    def mock_config(self):
        config = MagicMock()
        config.ADAPTATION_RATE_NORMAL = 0.2
        config.ADAPTATION_RATE_IMPULSIVE = 0.5
        config.ADAPTATION_RATE_CONSERVATIVE = 0.1
        config.PERCEIVED_PRICE_UPDATE_FACTOR = 0.1
        return config

    def test_update_perceived_prices_basic(self, mock_owner, mock_config):
        econ = EconComponent(mock_owner, mock_config)

        # Setup initial state
        econ.price_history["food"].append(10.0)
        econ.expected_inflation["food"] = 0.0
        econ.perceived_avg_prices["food"] = 10.0

        market_data = {
            "goods_market": {
                "food_avg_traded_price": 11.0
            }
        }

        econ.update_perceived_prices(market_data)

        # Verify Price History
        assert len(econ.price_history["food"]) == 2
        assert econ.price_history["food"][-1] == 11.0

        # Verify Expected Inflation
        # Inflation = (11 - 10) / 10 = 0.1
        # New Expectation = 0.0 + 0.1 * (0.1 - 0.0) = 0.01 (Conservative adaptation rate 0.1)
        assert econ.expected_inflation["food"] == pytest.approx(0.01)

        # Verify Perceived Price
        # New Perceived = 0.1 * 11 + 0.9 * 10 = 1.1 + 9.0 = 10.1
        assert econ.perceived_avg_prices["food"] == pytest.approx(10.1)

    def test_update_perceived_prices_hyperinflation(self, mock_owner, mock_config):
        econ = EconComponent(mock_owner, mock_config)
        econ.adaptation_rate = 0.2 # Force a rate override just to be sure, or rely on init

        # Override adaptation rate logic for test isolation or rely on mock_owner having CONSERVATIVE (0.1)
        # But here let's assume we want to test the multiplier logic.
        # Econ initialized with CONSERVATIVE -> 0.1
        # To match the calculation in comment (0.2), I should set adaptation_rate to 0.2
        econ.adaptation_rate = 0.2

        econ.price_history["food"].append(100.0)
        econ.expected_inflation["food"] = 0.05

        market_data = {
            "goods_market": {
                "food_avg_traded_price": 120.0
            }
        }

        stress_config = MagicMock()
        stress_config.is_active = True
        stress_config.scenario_name = 'hyperinflation'
        stress_config.inflation_expectation_multiplier = 2.0

        econ.update_perceived_prices(market_data, stress_scenario_config=stress_config)

        # Inflation = (120 - 100) / 100 = 0.2
        # Adaptive Rate = 0.2 * 2.0 = 0.4
        # New Expectation = 0.05 + 0.4 * (0.2 - 0.05) = 0.05 + 0.4 * 0.15 = 0.05 + 0.06 = 0.11
        assert econ.expected_inflation["food"] == pytest.approx(0.11)

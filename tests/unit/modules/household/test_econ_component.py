import pytest
from unittest.mock import MagicMock
from collections import deque, defaultdict
from modules.household.econ_component import EconComponent
from modules.household.dtos import EconStateDTO
from simulation.ai.api import Personality
from simulation.models import Talent
from simulation.portfolio import Portfolio
from tests.utils.factories import create_household_config_dto

class TestEconComponent:
    @pytest.fixture
    def mock_config(self):
        return create_household_config_dto(
            perceived_price_update_factor=0.1,
            adaptation_rate_normal=0.1,
            adaptation_rate_impulsive=0.2,
            adaptation_rate_conservative=0.05
        )

    @pytest.fixture
    def econ_state(self):
        # Create a basic EconStateDTO
        return EconStateDTO(
            assets=1000.0,
            inventory={},
            inventory_quality={},
            durable_assets=[],
            portfolio=Portfolio(1),
            is_employed=False,
            employer_id=None,
            current_wage=0.0,
            wage_modifier=1.0,
            labor_skill=1.0,
            education_xp=0.0,
            education_level=0,
            expected_wage=10.0,
            talent=Talent(base_learning_rate=0.5, max_potential=1.0),
            skills={},
            aptitude=0.5,
            owned_properties=[],
            residing_property_id=None,
            is_homeless=True,
            home_quality_score=1.0,
            housing_target_mode="RENT",
            housing_price_history=deque(),
            market_wage_history=deque(),
            shadow_reservation_wage=10.0,
            last_labor_offer_tick=0,
            last_fired_tick=-1,
            job_search_patience=0,
            current_consumption=0.0,
            current_food_consumption=0.0,
            expected_inflation=defaultdict(float),
            perceived_avg_prices=defaultdict(float),
            price_history=defaultdict(lambda: deque(maxlen=10)),
            price_memory_length=10,
            adaptation_rate=0.1,
            labor_income_this_tick=0.0,
            capital_income_this_tick=0.0
        )

    def test_update_perceived_prices_basic(self, econ_state, mock_config):
        econ = EconComponent()

        # Setup initial state
        econ_state.price_history["food"].append(10.0)
        econ_state.expected_inflation["food"] = 0.0
        econ_state.perceived_avg_prices["food"] = 10.0
        econ_state.adaptation_rate = 0.1 # Conservative/Normal

        market_data = {
            "goods_market": {
                "food_avg_traded_price": 11.0
            }
        }

        goods_info_map = {
            "food": {"id": "food"}
        }

        new_state = econ.update_perceived_prices(econ_state, market_data, goods_info_map, None, mock_config)

        # Verify Price History
        assert len(new_state.price_history["food"]) == 2
        assert new_state.price_history["food"][-1] == 11.0

        # Verify Expected Inflation
        # Inflation = (11 - 10) / 10 = 0.1
        # New Expectation = 0.0 + 0.1 * (0.1 - 0.0) = 0.01
        assert new_state.expected_inflation["food"] == pytest.approx(0.01)

        # Verify Perceived Price
        # New Perceived = 0.1 * 11 + 0.9 * 10 = 1.1 + 9.0 = 10.1
        assert new_state.perceived_avg_prices["food"] == pytest.approx(10.1)

    def test_update_perceived_prices_hyperinflation(self, econ_state, mock_config):
        econ = EconComponent()

        econ_state.adaptation_rate = 0.2
        econ_state.price_history["food"].append(100.0)
        econ_state.expected_inflation["food"] = 0.05
        econ_state.perceived_avg_prices["food"] = 100.0

        market_data = {
            "goods_market": {
                "food_avg_traded_price": 120.0
            }
        }

        goods_info_map = {
            "food": {"id": "food"}
        }

        stress_config = MagicMock()
        stress_config.is_active = True
        stress_config.scenario_name = 'hyperinflation'
        stress_config.inflation_expectation_multiplier = 2.0

        new_state = econ.update_perceived_prices(econ_state, market_data, goods_info_map, stress_config, mock_config)

        # Inflation = (120 - 100) / 100 = 0.2
        # Adaptive Rate = 0.2 * 2.0 = 0.4
        # New Expectation = 0.05 + 0.4 * (0.2 - 0.05) = 0.05 + 0.4 * 0.15 = 0.05 + 0.06 = 0.11
        assert new_state.expected_inflation["food"] == pytest.approx(0.11)

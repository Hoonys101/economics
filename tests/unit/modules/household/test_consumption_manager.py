import pytest
from unittest.mock import MagicMock
from collections import deque, defaultdict
from modules.household.consumption_manager import ConsumptionManager
from modules.household.dtos import EconStateDTO
from simulation.models import Talent
from simulation.portfolio import Portfolio
from tests.utils.factories import create_household_config_dto
from modules.finance.wallet.wallet import Wallet

class TestConsumptionManager:
    @pytest.fixture
    def mock_config(self):
        return create_household_config_dto(
            learning_efficiency=0.5,
            default_fallback_price=10.0,
            need_medium_threshold=50.0,
            survival_need_consumption_threshold=50.0
        )

    @pytest.fixture
    def econ_state(self):
        wallet = Wallet(1, {})
        wallet.add(1000)
        return EconStateDTO(
            wallet=wallet,
            inventory={"food": 10.0, "water": 5.0},
            inventory_quality={"food": 1.0, "water": 1.0},
            durable_assets=[],
            portfolio=Portfolio(1),
            is_employed=False,
            employer_id=None,
            current_wage_pennies=0,
            wage_modifier=1.0,
            labor_skill=1.0,
            education_xp=0.0,
            education_level=0,
            expected_wage_pennies=1000,
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
            shadow_reservation_wage_pennies=1000,

            last_labor_offer_tick=0,
            last_fired_tick=-1,
            job_search_patience=0,
            employment_start_tick=-1,
            current_consumption=0.0,
            current_food_consumption=0.0,
            expected_inflation=defaultdict(float),
            perceived_avg_prices={"food": 10.0, "water": 5.0},
            price_history=defaultdict(lambda: deque(maxlen=10)),
            price_memory_length=10,
            adaptation_rate=0.1,
            labor_income_this_tick_pennies=0,
            capital_income_this_tick_pennies=0,
            consumption_expenditure_this_tick_pennies=0,
            food_expenditure_this_tick_pennies=0
        )

    def test_consume_basic(self, econ_state, mock_config):
        manager = ConsumptionManager()
        needs = {"survival": 60.0} # Above threshold, but consume takes explicit quantity

        item_id = "food"
        quantity = 2.0
        current_time = 100
        goods_info = {
            "id": "food",
            "is_service": False,
            "utility_effects": {"survival": 5.0}
        }

        new_state, new_needs, result = manager.consume(
            econ_state, needs, item_id, quantity, current_time, goods_info, mock_config
        )

        # Inventory check
        assert new_state.inventory["food"] == 8.0 # 10 - 2

        # Needs check
        # Utility gained = 5.0 * 2.0 = 10.0
        # New need = 60.0 - 10.0 = 50.0
        assert new_needs["survival"] == 50.0

        # Consumption Result
        assert result.items_consumed["food"] == 2.0
        assert result.satisfaction == 10.0

        # Consumption tracking
        # Value = 2.0 * 10.0 = 20.0
        assert new_state.current_consumption == 20.0
        assert new_state.current_food_consumption == 20.0

    def test_consume_service(self, econ_state, mock_config):
        manager = ConsumptionManager()
        needs = {"learning": 100.0}

        item_id = "education_service"
        quantity = 1.0
        current_time = 100
        goods_info = {
            "id": "education_service",
            "is_service": True,
            "utility_effects": {"learning": 10.0}
        }

        new_state, new_needs, result = manager.consume(
            econ_state, needs, item_id, quantity, current_time, goods_info, mock_config
        )

        # Inventory should NOT change for service (it's not in inventory usually, or doesn't deplete if is_service=True)
        # But we didn't have it in inventory anyway.
        assert "education_service" not in new_state.inventory

        # XP check
        # Gain = 1.0 * 0.5 (efficiency) = 0.5
        assert new_state.education_xp == 0.5

    def test_decide_and_consume(self, econ_state, mock_config):
        manager = ConsumptionManager()
        needs = {"survival": 60.0} # Threshold is 50.0

        current_time = 100
        goods_info_map = {
            "food": {
                "id": "food",
                "is_service": False,
                "utility_effects": {"survival": 5.0}
            },
            "water": {
                "id": "water",
                "is_service": False,
                "utility_effects": {"survival": 2.0}
            }
        }

        # Should consume food (first in inventory iteration usually, or both?)
        # Logic iterates all inventory items.
        # Food: need 60 > 50 -> consume 1.0 (min(qty, 1.0))
        # After food: need = 60 - 5 = 55.
        # Water: need 55 > 50 -> consume 1.0.
        # After water: need = 55 - 2 = 53.

        new_state, final_needs, consumed = manager.decide_and_consume(
            econ_state, needs, current_time, goods_info_map, mock_config
        )

        assert consumed.get("food", 0.0) == 1.0
        assert consumed.get("water", 0.0) == 1.0
        assert final_needs["survival"] == 53.0

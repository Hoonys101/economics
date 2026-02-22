import pytest
from unittest.mock import MagicMock, PropertyMock
from collections import deque, defaultdict
from modules.household.engines.lifecycle import LifecycleEngine
from modules.household.dtos import BioStateDTO
from modules.household.engines.needs import NeedsEngine
from modules.household.engines.budget import BudgetEngine
from modules.household.dtos import EconStateDTO, HouseholdSnapshotDTO
from modules.household.api import NeedsInputDTO, BudgetInputDTO, PrioritizedNeed
from simulation.models import Order

class TestHealthMechanics:
    @pytest.fixture
    def bio_state(self):
        return BioStateDTO(
            id=1, age=25, gender="M", generation=0, is_active=True, needs={},
            health_status=1.0, has_disease=False, survival_need_high_turns=0
        )

    @pytest.fixture
    def econ_state(self):
        wallet_mock = MagicMock()
        wallet_mock.get_balance.return_value = 1000000 # Rich
        wallet_mock.get_all_balances.return_value = {"USD": 1000000}
        wallet_mock.owner_id = 1

        # Proper initialization of price_history
        price_history = defaultdict(lambda: deque(maxlen=10))

        return EconStateDTO(
            wallet=wallet_mock,
            inventory={}, inventory_quality={}, durable_assets=[], portfolio=MagicMock(),
            is_employed=True, employer_id=None, current_wage_pennies=1000,
            wage_modifier=1.0, labor_skill=1.0, education_xp=0.0, education_level=0,
            owned_properties=[], residing_property_id=None, is_homeless=False,
            home_quality_score=1.0, housing_target_mode="RENT",
            housing_price_history=deque(maxlen=10), market_wage_history=deque(maxlen=10),
            shadow_reservation_wage_pennies=0, last_labor_offer_tick=0, last_fired_tick=-1,
            job_search_patience=0, employment_start_tick=0,
            current_consumption=0.0, current_food_consumption=0.0,
            expected_inflation={}, perceived_avg_prices={},
            price_history=price_history, # FIX: Proper object
            price_memory_length=10, adaptation_rate=0.1,
            labor_income_this_tick_pennies=0, capital_income_this_tick_pennies=0,
            consumption_expenditure_this_tick_pennies=0, food_expenditure_this_tick_pennies=0
        )

    def test_sickness_probability(self, bio_state):
        engine = LifecycleEngine()
        config = MagicMock()
        config.HEALTH_SHOCK_BASE_PROB = 1.0 # Force sickness

        engine._check_health_shock(bio_state, config)

        assert bio_state.has_disease is True
        assert bio_state.health_status == 0.5

    def test_medical_need_injection(self, bio_state, econ_state):
        bio_state.has_disease = True

        engine = NeedsEngine()
        social_state = MagicMock()
        social_state.desire_weights = {}
        config = MagicMock()
        config.base_desire_growth = 0.0
        config.max_desire_value = 100.0
        config.survival_need_death_threshold = 100.0
        config.survival_need_death_ticks_threshold = 10

        input_dto = NeedsInputDTO(
            bio_state=bio_state,
            econ_state=econ_state,
            social_state=social_state,
            config=config,
            current_tick=0,
            goods_data={}
        )

        output = engine.evaluate_needs(input_dto)

        assert len(output.prioritized_needs) > 0
        top_need = output.prioritized_needs[0]
        assert top_need.need_id == "medical"
        assert top_need.urgency == 999.0

    def test_budget_allocation_medical(self, econ_state):
        engine = BudgetEngine()

        # Mock Medical Need
        needs = [PrioritizedNeed(need_id="medical", urgency=999.0, deficit=100.0)]

        market_snapshot = MagicMock()
        market_snapshot.goods = {} # No market data, defaults used

        input_dto = BudgetInputDTO(
            econ_state=econ_state,
            prioritized_needs=needs,
            abstract_plan=[],
            market_snapshot=market_snapshot,
            config=MagicMock(),
            current_tick=0
        )

        output = engine.allocate_budget(input_dto)

        # Should generate order for medical_service
        medical_orders = [o for o in output.budget_plan.orders if o.item_id == "medical_service"]
        assert len(medical_orders) == 1
        order = medical_orders[0]
        assert order.side == "BUY"
        assert order.quantity == 1.0
        assert order.price_pennies > 0 # Should allocate budget

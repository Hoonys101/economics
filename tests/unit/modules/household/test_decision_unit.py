import pytest
from unittest.mock import MagicMock
from collections import deque, defaultdict
from modules.household.decision_unit import DecisionUnit
from modules.household.dtos import EconStateDTO
from modules.household.api import OrchestrationContextDTO
from modules.system.api import MarketSnapshotDTO, HousingMarketSnapshotDTO, LoanMarketSnapshotDTO, LaborMarketSnapshotDTO
from simulation.models import Talent, Order
from simulation.portfolio import Portfolio
from tests.utils.factories import create_household_config_dto

class TestDecisionUnit:
    @pytest.fixture
    def mock_config(self):
        return create_household_config_dto(
            ticks_per_year=365,
            housing_expectation_cap=0.1,
            household_min_wage_demand=7.0
        )

    @pytest.fixture
    def econ_state(self):
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
            talent=Talent(base_learning_rate=0.5, max_potential={"general": 1.0}),
            skills={},
            aptitude=0.5,
            owned_properties=[],
            residing_property_id=None,
            is_homeless=True,
            home_quality_score=1.0,
            housing_target_mode="RENT",
            housing_price_history=deque([100.0, 110.0]),
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

    def test_orchestrate_housing_buy(self, econ_state, mock_config):
        decision_unit = DecisionUnit()

        # Setup state for BUY decision
        econ_state.assets = 5000.0
        econ_state.is_homeless = True

        # Construct DTOs
        housing_snapshot = HousingMarketSnapshotDTO(
            for_sale_units=[
                {"unit_id": "unit_1", "price": 10000.0, "quality": 1.0}
            ],
            avg_rent_price=500.0,
            avg_sale_price=10000.0
        )
        loan_snapshot = LoanMarketSnapshotDTO(interest_rate=0.05)
        labor_snapshot = LaborMarketSnapshotDTO(avg_wage=10.0)

        market_snapshot = MarketSnapshotDTO(
            housing=housing_snapshot,
            loan=loan_snapshot,
            labor=labor_snapshot
        )

        context = OrchestrationContextDTO(
            market_snapshot=market_snapshot,
            current_time=30,
            stress_scenario_config=None,
            config=mock_config
        )

        initial_orders = []

        # Run
        new_state, refined_orders = decision_unit.orchestrate_economic_decisions(
            econ_state, context, initial_orders
        )

        # Verify
        assert new_state.housing_target_mode == "BUY"
        assert len(refined_orders) == 1
        assert refined_orders[0].item_id == "unit_1"
        assert refined_orders[0].price_limit == 10000.0
        assert refined_orders[0].side == "BUY"

    def test_shadow_wage_update(self, econ_state, mock_config):
        decision_unit = DecisionUnit()

        # Setup state
        econ_state.is_employed = False
        econ_state.shadow_reservation_wage = 10.0

        # Construct DTOs
        # Housing doesn't matter for this test
        housing_snapshot = HousingMarketSnapshotDTO(
            for_sale_units=[], avg_rent_price=100.0, avg_sale_price=20000.0
        )
        loan_snapshot = LoanMarketSnapshotDTO(interest_rate=0.05)
        labor_snapshot = LaborMarketSnapshotDTO(avg_wage=12.0)

        market_snapshot = MarketSnapshotDTO(
            housing=housing_snapshot,
            loan=loan_snapshot,
            labor=labor_snapshot
        )

        context = OrchestrationContextDTO(
            market_snapshot=market_snapshot,
            current_time=100,
            stress_scenario_config=None,
            config=mock_config
        )

        initial_orders = []

        # Run
        new_state, _ = decision_unit.orchestrate_economic_decisions(
            econ_state, context, initial_orders
        )

        # Verify Shadow Wage Logic
        # Not employed -> shadow wage decay
        # 10.0 * (1.0 - 0.02) = 9.8
        assert new_state.shadow_reservation_wage == 9.8
        # Check market wage history update
        assert len(new_state.market_wage_history) == 1
        assert new_state.market_wage_history[0] == 12.0

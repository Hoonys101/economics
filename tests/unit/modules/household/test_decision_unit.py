import pytest
from unittest.mock import MagicMock, call
from collections import deque, defaultdict
from modules.household.decision_unit import DecisionUnit
from modules.household.dtos import EconStateDTO
from simulation.models import Talent, Order
from simulation.portfolio import Portfolio
from simulation.dtos import DecisionContext
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
            talent=Talent(base_learning_rate=0.5, max_potential=1.0),
            skills={},
            aptitude=0.5,
            owned_properties=[],
            residing_property_id=None,
            is_homeless=True,
            home_quality_score=1.0,
            housing_target_mode="RENT",
            housing_price_history=deque([100.0, 110.0]), # Some history for growth calc
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

    def test_make_decision_flow(self, econ_state, mock_config):
        decision_unit = DecisionUnit()

        # Mocks
        mock_engine = MagicMock()
        initial_orders = [Order(agent_id=1, side="BUY", item_id="food", quantity=1.0, price_limit=10.0, market_id="goods")]
        mock_engine.make_decisions.return_value = (initial_orders, ("TACTIC", "AGGRESSIVE"))

        mock_context = MagicMock(spec=DecisionContext)
        mock_context.current_time = 100
        mock_context.market_data = {
            "housing_market": {"avg_rent_price": 50.0, "avg_sale_price": 10000.0},
            "loan_market": {"interest_rate": 0.05}
        }
        mock_context.stress_scenario_config = None

        mock_macro_context = MagicMock()
        mock_markets = {"housing": MagicMock()}

        # Call
        new_state, refined_orders, tactic = decision_unit.make_decision(
            econ_state,
            mock_engine,
            mock_context,
            mock_macro_context,
            mock_markets,
            mock_context.market_data,
            mock_config
        )

        # Verification
        mock_engine.make_decisions.assert_called_once()

        # Check if orders are preserved
        assert len(refined_orders) >= 1
        assert refined_orders[0].item_id == "food"

        # Check if state updated (e.g. shadow wage logic)
        # Shadow wage logic runs:
        # if not employed: shadow_wage *= 0.98. min demand 7.0.
        # 10.0 * 0.98 = 9.8
        assert new_state.shadow_reservation_wage == 9.8

    def test_orchestrate_housing_buy(self, econ_state, mock_config):
        decision_unit = DecisionUnit()

        # Setup state for BUY decision
        # Needs plenty of assets for down payment (20% of 10000 = 2000)
        econ_state.assets = 5000.0
        econ_state.is_homeless = True

        # Mock Markets
        mock_housing_market = MagicMock()
        # Mock sell orders: item_id -> list of Orders
        mock_housing_market.sell_orders = {
            "unit_1": [Order(agent_id=99, side="SELL", item_id="unit_1", quantity=1.0, price_limit=10000.0, market_id="housing")]
        }

        markets = {"housing": mock_housing_market}

        # Mock Context Data
        # Ensure NPV favors BUY.
        # High rent (income flow), Low price.
        # Rent 500/mo. Price 10000. Yield = 6000/10000 = 60%. Risk free 5%. Definitely BUY.
        market_data = {
            "housing_market": {"avg_rent_price": 500.0, "avg_sale_price": 10000.0},
            "loan_market": {"interest_rate": 0.05}
        }

        # Mock Context DTO
        # We need EconContextDTO, but make_decision takes DecisionContext and creates EconContextDTO internally.
        # But we can test make_decision which calls orchestrate.

        mock_engine = MagicMock()
        mock_engine.make_decisions.return_value = ([], ("TACTIC", "AGGRESSIVE"))

        mock_context = MagicMock(spec=DecisionContext)
        mock_context.current_time = 30 # Trigger tick
        mock_context.market_data = market_data
        mock_context.stress_scenario_config = None

        new_state, refined_orders, _ = decision_unit.make_decision(
            econ_state,
            mock_engine,
            mock_context,
            None,
            markets,
            market_data,
            mock_config
        )

        # Check if BUY order generated
        # Logic:
        # 1. System 2 decides BUY (due to high rent vs price)
        # 2. Finds unit_1 at 10000
        # 3. Checks assets >= 2000 (True, 5000)
        # 4. Appends BUY order

        assert new_state.housing_target_mode == "BUY"
        assert len(refined_orders) == 1
        assert refined_orders[0].item_id == "unit_1"
        assert refined_orders[0].price_limit == 10000.0


import pytest
from unittest.mock import MagicMock, patch
from simulation.systems.event_system import EventSystem
from simulation.systems.commerce_system import CommerceSystem
from simulation.dtos.scenario import StressScenarioConfig
from simulation.core_agents import Household, Personality
from simulation.systems.api import EventContext, CommerceContext

class TestPhase28StressScenarios:

    @pytest.fixture
    def mock_households(self):
        h1 = MagicMock(spec=Household)
        h1.id = 1
        h1._assets = 1000.0
        h1.inventory = {}
        h1.is_active = True
        h1.is_employed = False
        # Personality.NORMAL is invalid, use CONSERVATIVE or another valid member
        h1.personality = Personality.CONSERVATIVE
        h1.adaptation_rate = 0.1
        h1.price_history = {"item1": []}
        h1.expected_inflation = {"item1": 0.0}

        h2 = MagicMock(spec=Household)
        h2.id = 2
        h2._assets = 5000.0 # Wealthy
        h2.is_active = True

        return [h1, h2]

    @pytest.fixture
    def mock_firms(self):
        f1 = MagicMock()
        f1.id = 101
        f1.type = "Farm"
        f1.productivity_factor = 1.0
        f1._assets = 10000.0
        return [f1]

    @pytest.fixture
    def event_system(self):
        config = MagicMock()
        return EventSystem(config)

    @pytest.fixture
    def commerce_system(self):
        config = MagicMock()
        reflux = MagicMock()
        return CommerceSystem(config, reflux)

    # --- Scenario 1: Hyperinflation ---

    def test_hyperinflation_trigger(self, event_system, mock_households, mock_firms):
        """Verify Cash Injection Trigger"""
        config = StressScenarioConfig(
            is_active=True,
            scenario_name='hyperinflation',
            start_tick=10,
            demand_shock_cash_injection=0.5
        )

        context: EventContext = {
            "households": mock_households,
            "firms": mock_firms,
            "markets": {}
        }

        # Trigger event
        event_system.execute_scheduled_events(10, context, config)

        # Check household assets increased by 50%
        # mock_households[0].assets is a property on a mock, so we check if it was set
        # Since we mocked the object but not the attribute access completely for calc:
        # If we use MagicMock, operations like *= are recorded but values might not update if not real objects.
        # But here we used MagicMock which returns new MagicMocks on operations.
        # We need real objects or better mocks for calculation verification.
        # Let's verify the attribute set call.

        # Actually, for math operations on Mocks to work effectively for assertion,
        # we often need side_effect or specific setup.
        # Let's check if __imul__ was called with 1.5
        # Or simpler: configure the mock to behave like a float? No.

        # Let's inspect the code: `h.assets *= (1 + ...)`
        # This calls `h.assets.__imul__(1.5)`.
        # However, `h.assets` is likely a primitive in the real code, but here it's a Mock or float.
        # If I set h1._assets = 1000.0 (float), then `h1.assets *= 1.5` updates the attribute on the mock object instance.

        assert mock_households[0].assets == 1500.0
        assert mock_households[1].assets == 7500.0

    # --- Scenario 2: Deflation ---

    def test_deflation_asset_shock(self, event_system, mock_households, mock_firms):
        """Verify Asset Reduction Trigger"""
        config = StressScenarioConfig(
            is_active=True,
            scenario_name='deflation',
            start_tick=20,
            asset_shock_reduction=0.2
        )

        context: EventContext = {
            "households": mock_households,
            "firms": mock_firms,
            "markets": {}
        }

        event_system.execute_scheduled_events(20, context, config)

        # 1000 * 0.8 = 800
        assert mock_households[0].assets == 800.0
        # Firm: 10000 * 0.8 = 8000
        assert mock_firms[0].assets == 8000.0

    def test_consumption_pessimism(self, commerce_system, mock_households):
        """Verify Consumption Collapse for Unemployed"""
        config = StressScenarioConfig(
            is_active=True,
            scenario_name='deflation',
            consumption_pessimism_factor=0.3 # 30% reduction
        )

        # Setup Breeding Planner Mock to return consumption decisions
        planner = MagicMock()
        # Returns dict with lists matching household indices
        planner.decide_consumption_batch.return_value = {
            'consume': [10.0, 10.0],
            'buy': [0.0, 0.0],
            'price': 1.0
        }

        # Household 1: Unemployed -> Should be reduced
        mock_households[0].is_employed = False
        # Household 2: Employed -> Should NOT be reduced (mock doesn't have employed set, default False?)
        mock_households[1].is_employed = True

        context: CommerceContext = {
            "households": mock_households,
            "agents": {},
            "breeding_planner": planner,
            "household_time_allocation": {},
            "reflux_system": MagicMock(),
            "market_data": {},
            "config": MagicMock(),
            "time": 100
        }

        commerce_system.execute_consumption_and_leisure(context, config)

        # Verify consume calls
        # Household 1: 10.0 * 0.7 = 7.0
        mock_households[0].consume.assert_called_with("basic_food", 7.0, 100)
        # Household 2: 10.0 (No reduction)
        mock_households[1].consume.assert_called_with("basic_food", 10.0, 100)

    # --- Scenario 3: Supply Shock ---

    def test_supply_shock(self, event_system, mock_firms):
        config = StressScenarioConfig(
            is_active=True,
            scenario_name='supply_shock',
            start_tick=30,
            exogenous_productivity_shock={"Farm": 0.5}
        )

        context: EventContext = {
            "households": [],
            "firms": mock_firms,
            "markets": {}
        }

        event_system.execute_scheduled_events(30, context, config)

        # Firm 1 is Farm, Prod 1.0 -> 0.5
        assert mock_firms[0].productivity_factor == 0.5

    # --- Behavioral Tests ---

    def test_panic_selling_order_generation(self):
        """Verify Panic Selling Order Generation when assets are low."""
        # Arrange
        config_module = MagicMock()
        config_module.PANIC_SELLING_ASSET_THRESHOLD = 500.0
        config_module.STOCK_MARKET_ENABLED = True

        household = Household(
            id=1,
            talent=MagicMock(),
            goods_data=[],
            initial_assets=400.0, # Below threshold
            initial_needs={},
            decision_engine=MagicMock(),
            value_orientation="wealth_and_needs",
            personality=Personality.CONSERVATIVE,
            config_module=config_module
        )
        household.portfolio = MagicMock()
        household.portfolio.holdings = {101: 10.0} # Owns 10 shares of firm 101

        stress_config = StressScenarioConfig(
            is_active=True,
            scenario_name='deflation',
            panic_selling_enabled=True
        )

        # Act
        # We need to mock make_decision dependencies
        markets = {}
        # We don't need detailed markets as we are testing order generation logic in Household.make_decision wrapper
        # Household.make_decision calls decision_engine.make_decisions first.
        household.decision_engine.make_decisions.return_value = ([], None) # Normal engine returns nothing

        orders, _ = household.make_decision(markets, [], {}, 100, stress_scenario_config=stress_config)

        # Assert
        assert len(orders) == 1
        order = orders[0]
        assert order.order_type == "SELL"
        assert order.item_id == "stock_101"
        assert order.quantity == 10.0
        assert order.price == 0.0 # Market sell

    def test_hoarding_amplification(self):
        """Verify Hoarding amplifies buy quantity."""
        # Arrange
        config_module = MagicMock()
        config_module.GOODS = {"basic_food": {"utility_effects": {"survival": 10}}}
        config_module.HOUSEHOLD_CONSUMABLE_GOODS = ["basic_food"]
        config_module.HOUSEHOLD_MAX_PURCHASE_QUANTITY = 5.0
        config_module.BULK_BUY_NEED_THRESHOLD = 1000.0 # Don't trigger normal bulk buy
        config_module.BULK_BUY_AGG_THRESHOLD = 1.0
        config_module.MIN_PURCHASE_QUANTITY = 0.1
        config_module.BUDGET_LIMIT_NORMAL_RATIO = 1.0
        config_module.MARKET_PRICE_FALLBACK = 5.0
        config_module.NEED_FACTOR_BASE = 1.0
        config_module.NEED_FACTOR_SCALE = 100.0
        config_module.VALUATION_MODIFIER_BASE = 1.0
        config_module.VALUATION_MODIFIER_RANGE = 0.0
        config_module.DSR_CRITICAL_THRESHOLD = 1.0
        config_module.PANIC_BUYING_THRESHOLD = 0.05
        config_module.DEFLATION_WAIT_THRESHOLD = -0.05
        config_module.HOARDING_FACTOR = 0.5
        config_module.DELAY_FACTOR = 0.5
        config_module.BUDGET_LIMIT_URGENT_NEED = 80.0
        config_module.WAGE_RECOVERY_RATE = 0.01
        config_module.WAGE_RECOVERY_RATE = 0.01

        # Import real engine for logic test
        from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine
        from simulation.dtos import DecisionContext

        ai_engine = MagicMock()
        # Return aggressive consumption
        from simulation.schemas import HouseholdActionVector
        vector = HouseholdActionVector()
        vector.consumption_aggressiveness = {"basic_food": 0.5}
        ai_engine.decide_action_vector.return_value = vector

        decision_engine = AIDrivenHouseholdDecisionEngine(ai_engine, config_module)

        household = MagicMock()
        household.id = 1
        household._assets = 1000.0
        household.inventory = {}
        household.needs = {"survival": 50.0}
        household.get_agent_data.return_value = {}
        household.expected_inflation = {} # Empty dict
        household.preference_asset = 1.0
        household.preference_social = 1.0
        household.preference_growth = 1.0
        household.current_wage = 10.0
        household.wage_modifier = 1.0 # Fix TypeError in min() comparison
        # Fix ZeroDivisionError in _calculate_savings_roi
        # Mocks can be truthy but empty. Explicitly set to empty dict which is falsy in bool context?
        # No, Mock objects are truthy.
        # We need to make sure bool(household.expected_inflation) is False OR it has values.
        # Since it is a property on a MagicMock, we can set it to a real dict.
        household.expected_inflation = {}

        stress_config = StressScenarioConfig(
            is_active=True,
            scenario_name='hyperinflation',
            hoarding_propensity_factor=0.5 # 50% more
        )

        context = DecisionContext(
            household=household,
            markets={},
            goods_data=[],
            market_data={"goods_market": {"basic_food_current_sell_price": 5.0}},
            current_time=100,
            stress_scenario_config=stress_config
        )

        # Act
        orders, _ = decision_engine.make_decisions(context)

        # Assert
        # Base quantity logic is complex, but we know hoarding applies a multiplier.
        # Let's compare with and without stress config?
        # Or simpler: trust the logic flow if we can calculate expected.
        # Logic: target_quantity = 1.0 (since not bulk) * (1 + 0.5) = 1.5

        assert len(orders) == 1
        # The engine logic:
        # target_quantity starts at 1.0 (if needs not extreme)
        # Hoarding factor adds 0.5 -> 1.5
        assert orders[0].quantity == pytest.approx(1.5)

    def test_debt_repayment_priority(self):
        """Verify Debt Repayment generation in Deflation."""
        # Arrange
        config_module = MagicMock()
        config_module.GOODS = {}
        config_module.DEBT_REPAYMENT_RATIO = 0.5
        config_module.DEBT_REPAYMENT_CAP = 1.1
        config_module.DEBT_LIQUIDITY_RATIO = 0.9
        config_module.DSR_CRITICAL_THRESHOLD = 1.0

        from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine
        from simulation.dtos import DecisionContext
        from simulation.schemas import HouseholdActionVector

        ai_engine = MagicMock()
        ai_engine.decide_action_vector.return_value = HouseholdActionVector()

        decision_engine = AIDrivenHouseholdDecisionEngine(ai_engine, config_module)
        # Mock _manage_portfolio to do nothing to isolate debt logic
        decision_engine._manage_portfolio = MagicMock(return_value=[])
        decision_engine._check_emergency_liquidity = MagicMock(return_value=[])

        household = MagicMock()
        household.id = 1
        household._assets = 1000.0
        household.current_wage = 10.0 # Fix TypeError
        household.preference_asset = 1.0 # Fix
        household.expected_inflation = {} # Avoid ZeroDivisionError
        household.wage_modifier = 1.0 # Fix TypeError
        household.wage_modifier = 1.0 # Fix TypeError

        stress_config = StressScenarioConfig(
            is_active=True,
            scenario_name='deflation',
            debt_aversion_multiplier=2.0 # Double priority
        )

        # Market data with debt
        market_data = {
            "debt_data": {
                1: {"total_principal": 500.0}
            },
            "loan_market": {"interest_rate": 0.05}
        }

        context = DecisionContext(
            household=household,
            markets={},
            goods_data=[],
            market_data=market_data,
            current_time=100,
            stress_scenario_config=stress_config
        )

        # Act
        orders, _ = decision_engine.make_decisions(context)

        # Assert
        # Repay calc: assets(1000) * ratio(0.5) * multiplier(2.0) = 1000.0
        # Caps: principal(500) * cap(1.1) = 550.0
        # Liquidity: assets(1000) * 0.9 = 900.0
        # Min of (1000, 550, 900) = 550.0

        repayment_orders = [o for o in orders if o.order_type == "REPAYMENT"]
        assert len(repayment_orders) == 1
        assert repayment_orders[0].quantity == 550.0

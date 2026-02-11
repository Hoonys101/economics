
import pytest
from unittest.mock import MagicMock, patch
from simulation.systems.event_system import EventSystem
from simulation.systems.commerce_system import CommerceSystem
from simulation.dtos.scenario import StressScenarioConfig
from simulation.core_agents import Household, Personality
from simulation.systems.api import EventContext, CommerceContext
from simulation.dtos.config_dtos import HouseholdConfigDTO
from modules.household.dtos import HouseholdStateDTO
from simulation.models import Share

class TestPhase28StressScenarios:

    @pytest.fixture
    def mock_households(self):
        h1 = MagicMock(spec=Household)
        h1.id = 1

        # Setup nested states
        h1._econ_state = MagicMock()
        h1._econ_state.assets = 1000.0
        h1._econ_state.inventory = {}
        h1._econ_state.is_employed = False
        h1._econ_state.perceived_avg_prices = {"item1": 10.0}
        h1._econ_state.expected_inflation = {"item1": 0.0}

        h1._bio_state = MagicMock()
        h1._bio_state.is_active = True
        h1._bio_state.needs = {}

        h1._social_state = MagicMock()
        # Set primitive values for serialization safety
        h1._social_state.conformity = 0.5
        h1._social_state.social_rank = 0.5
        h1._social_state.approval_rating = 1.0
        h1._social_state.optimism = 0.5
        h1._social_state.ambition = 0.5

        # Sync top-level properties (Legacy/Convenience)
        h1.assets = 1000.0
        h1.wallet = MagicMock()
        h1.wallet.get_balance.return_value = 1000.0
        h1.inventory = {}
        h1.is_active = True
        h1.is_employed = False
        # Personality.NORMAL is invalid, use CONSERVATIVE or another valid member
        h1.personality = Personality.CONSERVATIVE
        h1.adaptation_rate = 0.1
        h1.price_history = {"item1": []}
        h1.expected_inflation = {"item1": 0.0}
        # Wire consume to use consumption manager or simple mock
        h1.consume = MagicMock()

        h2 = MagicMock(spec=Household)
        h2.id = 2

        h2._econ_state = MagicMock()
        h2._econ_state.assets = 5000.0
        h2._econ_state.inventory = {}

        h2._bio_state = MagicMock()
        h2._bio_state.is_active = True
        h2._bio_state.needs = {}

        h2._social_state = MagicMock()
        # Set primitive values for serialization safety
        h2._social_state.conformity = 0.5
        h2._social_state.social_rank = 0.5
        h2._social_state.approval_rating = 1.0
        h2._social_state.optimism = 0.5
        h2._social_state.ambition = 0.5

        h2.assets = 5000.0 # Wealthy
        h2.wallet = MagicMock()
        h2.wallet.get_balance.return_value = 5000.0
        h2.is_active = True
        h2.consume = MagicMock()

        return [h1, h2]

    @pytest.fixture
    def mock_firms(self):
        f1 = MagicMock()
        f1.id = 101
        f1.type = "Farm"
        f1.productivity_factor = 1.0
        f1.assets = 10000.0
        f1.wallet = MagicMock()
        f1.wallet.get_balance.return_value = 10000.0
        return [f1]

    @pytest.fixture
    def event_system(self):
        config = MagicMock()
        settlement_system = MagicMock()
        es = EventSystem(config, settlement_system)
        return es

    @pytest.fixture
    def commerce_system(self):
        config = MagicMock()
        return CommerceSystem(config)

    # --- Scenario 1: Hyperinflation ---

    def test_hyperinflation_trigger(self, event_system, mock_households, mock_firms):
        """Verify Cash Injection Trigger"""
        config = StressScenarioConfig(
            is_active=True,
            scenario_name='hyperinflation',
            start_tick=10,
            demand_shock_cash_injection=0.5
        )

        # Need Central Bank for injection
        central_bank = MagicMock()
        context: EventContext = {
            "households": mock_households,
            "firms": mock_firms,
            "markets": {},
            "central_bank": central_bank
        }

        # Trigger event
        event_system.execute_scheduled_events(10, context, config)

        # Verify settlement system calls
        # 1000 * 0.5 = 500
        # 5000 * 0.5 = 2500
        assert event_system.settlement_system.create_and_transfer.call_count == 2

        # Check call args for first household
        calls = event_system.settlement_system.create_and_transfer.call_args_list
        # Note: order depends on list iteration
        # h1: amount=500
        # h2: amount=2500
        amounts = sorted([c.kwargs['amount'] for c in calls])
        assert amounts == [500.0, 2500.0]

    # --- Scenario 2: Deflation ---

    def test_deflation_asset_shock(self, event_system, mock_households, mock_firms):
        """Verify Asset Reduction Trigger"""
        config = StressScenarioConfig(
            is_active=True,
            scenario_name='deflation',
            start_tick=20,
            asset_shock_reduction=0.2
        )

        central_bank = MagicMock()
        context: EventContext = {
            "households": mock_households,
            "firms": mock_firms,
            "markets": {},
            "central_bank": central_bank
        }

        event_system.execute_scheduled_events(20, context, config)

        # Verify destruction
        # h1: 1000 * 0.2 = 200
        # h2: 5000 * 0.2 = 1000
        # f1: 10000 * 0.2 = 2000
        assert event_system.settlement_system.transfer_and_destroy.call_count == 3

        amounts = sorted([c.kwargs['amount'] for c in event_system.settlement_system.transfer_and_destroy.call_args_list])
        assert amounts == [200.0, 1000.0, 2000.0]

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

        planned, txs = commerce_system.plan_consumption_and_leisure(context, config)
        commerce_system.finalize_consumption_and_leisure(context, planned)

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

        # Add Value Orientation Mapping (Required by Household.__init__)
        config_module.value_orientation_mapping = {
            "wealth_and_needs": {"preference_asset": 1.0, "preference_social": 1.0, "preference_growth": 1.0}
        }
        # Add required ranges for SocialState
        config_module.conformity_ranges = {}
        config_module.initial_household_assets_mean = 1000.0
        config_module.quality_pref_snob_min = 0.8
        config_module.quality_pref_miser_max = 0.2
        config_module.price_memory_length = 10
        config_module.wage_memory_length = 10
        config_module.ticks_per_year = 100
        config_module.adaptation_rate_normal = 0.1

        # Use ConfigDTO mock
        config_dto = MagicMock(spec=HouseholdConfigDTO)
        config_dto.value_orientation_mapping = config_module.value_orientation_mapping
        config_dto.conformity_ranges = config_module.conformity_ranges
        config_dto.initial_household_assets_mean = config_module.initial_household_assets_mean
        config_dto.quality_pref_snob_min = config_module.quality_pref_snob_min
        config_dto.quality_pref_miser_max = config_module.quality_pref_miser_max
        config_dto.price_memory_length = config_module.price_memory_length
        config_dto.wage_memory_length = config_module.wage_memory_length
        config_dto.ticks_per_year = config_module.ticks_per_year
        config_dto.adaptation_rate_normal = config_module.adaptation_rate_normal
        config_dto.adaptation_rate_conservative = 0.05
        config_dto.adaptation_rate_impulsive = 0.2
        config_dto.social_status_asset_weight = 0.5
        config_dto.social_status_luxury_weight = 0.5
        config_dto.base_desire_growth = 0.1
        config_dto.max_desire_value = 100.0
        config_dto.initial_wage = 10.0
        config_dto.household_low_asset_threshold = 100.0
        config_dto.household_low_asset_wage = 5.0
        config_dto.household_default_wage = 10.0
        config_dto.survival_need_consumption_threshold = 10.0
        config_dto.wage_decay_rate = 0.01
        config_dto.reservation_wage_floor = 1.0
        config_dto.household_min_wage_demand = 1.0
        config_dto.panic_selling_asset_threshold = 50000
        config_dto.initial_household_age_range = (20, 50)
        config_dto.initial_aptitude_distribution = (0.5, 0.1)


        from modules.system.api import DEFAULT_CURRENCY
        from modules.simulation.api import AgentCoreConfigDTO

        core_config = AgentCoreConfigDTO(
            id=1,
            name="HH_1",
            initial_needs={},
            logger=MagicMock(),
            value_orientation="wealth_and_needs",
            memory_interface=None
        )

        household = Household(
            core_config=core_config,
            engine=MagicMock(),
            talent=MagicMock(),
            goods_data=[],
            initial_assets_record=40000, # Below threshold
            personality=Personality.CONSERVATIVE,
            config_dto=config_dto, # Pass DTO
        )
        household.deposit(40000, DEFAULT_CURRENCY)
        household._econ_state.portfolio = MagicMock()
        share_mock = MagicMock(spec=Share)
        share_mock.quantity = 10.0
        household._econ_state.portfolio.holdings = {101: share_mock}

        stress_config = StressScenarioConfig(
            is_active=True,
            scenario_name='deflation',
            panic_selling_enabled=True
        )

        # Act
        # We need to mock make_decision dependencies
        markets = {}
        household.decision_engine.make_decisions.return_value = ([], None) # Normal engine returns nothing

        from simulation.dtos.api import DecisionInputDTO, MarketSnapshotDTO
        input_dto = DecisionInputDTO(
            market_snapshot=MarketSnapshotDTO(
                tick=100,
                housing=MagicMock(),
                labor=MagicMock(avg_wage=10.0),
                market_signals={}
            ),
            goods_data=[],
            market_data=markets,
            current_time=100,
            stress_scenario_config=stress_config,
            agent_registry={}
        )

        orders, _ = household.make_decision(input_dto)

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
        config_module = MagicMock(spec=HouseholdConfigDTO) # Use spec
        config_module.GOODS = {"basic_food": {"utility_effects": {"survival": 10}}}
        config_module.goods = config_module.GOODS
        config_module.HOUSEHOLD_CONSUMABLE_GOODS = ["basic_food"]
        config_module.household_consumable_goods = ["basic_food"]
        config_module.HOUSEHOLD_MAX_PURCHASE_QUANTITY = 5.0
        config_module.household_max_purchase_quantity = 5.0
        config_module.BULK_BUY_NEED_THRESHOLD = 1000.0
        config_module.bulk_buy_need_threshold = 1000.0
        config_module.BULK_BUY_AGG_THRESHOLD = 1.0
        config_module.bulk_buy_agg_threshold = 1.0
        config_module.MIN_PURCHASE_QUANTITY = 0.1
        config_module.min_purchase_quantity = 0.1
        config_module.BUDGET_LIMIT_NORMAL_RATIO = 1.0
        config_module.budget_limit_normal_ratio = 1.0
        config_module.BUDGET_LIMIT_URGENT_NEED = 80.0
        config_module.budget_limit_urgent_need = 80.0
        config_module.labor_market_min_wage = 5.0
        config_module.job_quit_threshold_base = 0.5
        config_module.job_quit_prob_base = 0.1
        config_module.job_quit_prob_scale = 0.1
        config_module.stock_market_enabled = False
        config_module.household_min_assets_for_investment = 100.0
        config_module.stock_investment_equity_delta_threshold = 10.0
        config_module.stock_investment_diversification_count = 2
        config_module.expected_startup_roi = 0.15
        config_module.startup_cost = 30000.0
        config_module.debt_repayment_ratio = 0.5
        config_module.debt_repayment_cap = 1.0
        config_module.debt_liquidity_ratio = 0.5
        config_module.MARKET_PRICE_FALLBACK = 5.0
        config_module.market_price_fallback = 5.0
        config_module.NEED_FACTOR_BASE = 1.0
        config_module.need_factor_base = 1.0
        config_module.NEED_FACTOR_SCALE = 100.0
        config_module.need_factor_scale = 100.0
        config_module.VALUATION_MODIFIER_BASE = 1.0
        config_module.valuation_modifier_base = 1.0
        config_module.VALUATION_MODIFIER_RANGE = 0.0
        config_module.valuation_modifier_range = 0.0
        config_module.DSR_CRITICAL_THRESHOLD = 1.0
        config_module.dsr_critical_threshold = 1.0
        config_module.PANIC_BUYING_THRESHOLD = 0.05
        config_module.DEFLATION_WAIT_THRESHOLD = -0.05
        config_module.HOARDING_FACTOR = 0.5
        config_module.DELAY_FACTOR = 0.5
        config_module.BUDGET_LIMIT_URGENT_NEED = 80.0
        config_module.WAGE_RECOVERY_RATE = 0.01
        config_module.max_willingness_to_pay_multiplier = 2.5

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

        # Mock State DTO instead of Agent
        state_dto = MagicMock(spec=HouseholdStateDTO)
        state_dto.id = 1
        state_dto.assets = 1000.0
        state_dto.inventory = {}
        state_dto.needs = {"survival": 50.0}
        state_dto.expected_inflation = {}
        state_dto.perceived_prices = {}
        state_dto.preference_asset = 1.0
        state_dto.preference_social = 1.0
        state_dto.preference_growth = 1.0
        state_dto.current_wage = 10.0
        state_dto.wage_modifier = 1.0
        state_dto.is_employed = True # Add missing attr if needed by engine logic
        state_dto.residing_property_id = None
        state_dto.owned_properties = []
        state_dto.is_homeless = True
        state_dto.personality = Personality.CONSERVATIVE # Enum
        state_dto.risk_aversion = 1.0
        state_dto.conformity = 0.5
        state_dto.optimism = 0.5
        state_dto.ambition = 0.5
        state_dto.agent_data = {}
        state_dto.demand_elasticity = 1.0

        stress_config = StressScenarioConfig(
            is_active=True,
            scenario_name='hyperinflation',
            hoarding_propensity_factor=0.5 # 50% more
        )

        context = DecisionContext(
            state=state_dto, # Pass state
            config=config_module, # Pass config
            goods_data=[],
            market_data={"goods_market": {"basic_food_current_sell_price": 5.0}},
            current_time=100,
            stress_scenario_config=stress_config
        )

        # Act
        output = decision_engine.make_decisions(context)
        orders = [o for o in output.orders if o.item_id == "basic_food"]

        # Assert
        assert len(orders) == 1
        # Quantity calculation:
        # max_need_value (50.0) * (1 - (avg_price(5.0) / max_affordable(12.5))) ** elastic(1.0)
        # = 50.0 * (1 - 0.4) = 30.0
        assert orders[0].quantity == pytest.approx(30.0)

    def test_debt_repayment_priority(self):
        """Verify Debt Repayment generation in Deflation."""
        # Arrange
        config_module = MagicMock(spec=HouseholdConfigDTO)
        config_module.GOODS = {}
        config_module.goods = {}
        config_module.DEBT_REPAYMENT_RATIO = 0.5
        config_module.debt_repayment_ratio = 0.5
        config_module.DEBT_REPAYMENT_CAP = 1.1
        config_module.debt_repayment_cap = 1.1
        config_module.DEBT_LIQUIDITY_RATIO = 0.9
        config_module.debt_liquidity_ratio = 0.9
        config_module.DSR_CRITICAL_THRESHOLD = 1.0
        config_module.dsr_critical_threshold = 1.0
        config_module.labor_market_min_wage = 5.0

        from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine
        from simulation.dtos import DecisionContext
        from simulation.schemas import HouseholdActionVector

        ai_engine = MagicMock()
        ai_engine.decide_action_vector.return_value = HouseholdActionVector()

        decision_engine = AIDrivenHouseholdDecisionEngine(ai_engine, config_module)
        # Mock _manage_portfolio to do nothing to isolate debt logic
        decision_engine._manage_portfolio = MagicMock(return_value=[])
        decision_engine._check_emergency_liquidity = MagicMock(return_value=[])

        state_dto = MagicMock(spec=HouseholdStateDTO)
        state_dto.id = 1
        state_dto.assets = 1000.0
        state_dto.current_wage = 10.0
        state_dto.preference_asset = 1.0
        state_dto.expected_inflation = {}
        state_dto.wage_modifier = 1.0
        state_dto.inventory = {}
        state_dto.needs = {}
        # Add attributes accessed by engine
        state_dto.portfolio_holdings = {}
        state_dto.agent_data = {}
        state_dto.personality = Personality.CONSERVATIVE
        state_dto.is_employed = False

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
            state=state_dto,
            config=config_module,
            goods_data=[],
            market_data=market_data,
            current_time=100,
            stress_scenario_config=stress_config
        )

        # Act
        output = decision_engine.make_decisions(context)
        orders = output.orders

        # Assert
        repayment_orders = [o for o in orders if o.order_type == "REPAYMENT"]
        assert len(repayment_orders) == 1
        assert repayment_orders[0].quantity == 550.0

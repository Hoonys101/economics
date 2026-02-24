import pytest
from unittest.mock import MagicMock, Mock
from simulation.core_agents import Household
from modules.household.dtos import EconStateDTO
from simulation.systems.handlers.goods_handler import GoodsTransactionHandler
from simulation.systems.handlers.labor_handler import LaborTransactionHandler
from simulation.models import Transaction
from simulation.metrics.economic_tracker import EconomicIndicatorTracker
from modules.simulation.dtos.api import HouseholdConfigDTO
from modules.finance.api import IIncomeTracker, IConsumptionTracker

@pytest.fixture
def mock_config():
    config = MagicMock(spec=HouseholdConfigDTO)
    # Set default values for int fields
    config.household_low_asset_threshold = 10000
    config.panic_selling_asset_threshold = 50000
    config.assets_threshold_for_other_actions = 10000
    # Set other required fields to avoid init errors if any
    config.price_memory_length = 10
    config.wage_memory_length = 10
    config.ticks_per_year = 365
    config.initial_household_age_range = (20, 60)
    config.initial_aptitude_distribution = (0.5, 0.1)
    config.conformity_ranges = {}
    config.value_orientation_mapping = {}
    config.adaptation_rate_normal = 0.1
    config.adaptation_rate_impulsive = 0.2
    config.adaptation_rate_conservative = 0.05
    config.initial_household_assets_mean = 50000
    config.quality_pref_snob_min = 0.8
    config.quality_pref_miser_max = 0.2
    config.elasticity_mapping = {}
    return config

@pytest.fixture
def household(mock_config):
    # Mocking AgentCoreConfigDTO and IDecisionEngine is complex,
    # better to use a minimal subclass or mock the dependencies carefully.
    # But Household.__init__ is heavy.

    # Let's try to instantiate with mocks.
    core_config = MagicMock()
    core_config.id = 1
    core_config.initial_needs = {}
    engine = MagicMock()
    talent = MagicMock()
    goods_data = []
    personality = MagicMock()

    agent = Household(
        core_config=core_config,
        engine=engine,
        talent=talent,
        goods_data=goods_data,
        personality=personality,
        config_dto=mock_config
    )
    return agent

class TestReportingPennies:

    def test_household_expenditure_tracking(self, household):
        # 1. Check Init
        assert household._econ_state.consumption_expenditure_this_tick_pennies == 0
        assert household._econ_state.food_expenditure_this_tick_pennies == 0

        # 2. Add Expenditure
        household.add_consumption_expenditure(100, item_id="basic_food")
        assert household._econ_state.consumption_expenditure_this_tick_pennies == 100
        assert household._econ_state.food_expenditure_this_tick_pennies == 100

        household.add_consumption_expenditure(50, item_id="luxury_goods")
        assert household._econ_state.consumption_expenditure_this_tick_pennies == 150
        assert household._econ_state.food_expenditure_this_tick_pennies == 100 # Unchanged

        # 3. Tick Analytics
        analytics = household.tick_analytics
        assert analytics["consumption_this_tick"] == 150
        assert isinstance(analytics["consumption_this_tick"], int)

        # 4. Reset
        household.reset_tick_state()
        assert household._econ_state.consumption_expenditure_this_tick_pennies == 0
        assert household._econ_state.food_expenditure_this_tick_pennies == 0

    def test_household_income_tracking(self, household):
        # 1. Check Init
        assert household._econ_state.labor_income_this_tick_pennies == 0

        # 2. Add Income
        household.add_labor_income(2000)
        assert household._econ_state.labor_income_this_tick_pennies == 2000

        # 3. Analytics
        analytics = household.tick_analytics
        assert analytics["labor_income_this_tick"] == 2000

        # 4. Reset
        household.reset_tick_state()
        assert household._econ_state.labor_income_this_tick_pennies == 0

    def test_goods_handler_calls_tracker(self, household):
        handler = GoodsTransactionHandler()
        state = MagicMock()
        state.settlement_system.settle_atomic.return_value = True
        state.escrow_agent = MagicMock()
        state.government = MagicMock()
        state.config_module.SALES_TAX_RATE = 0.0
        state.taxation_system.calculate_tax_intents.return_value = [] # No tax for simplicity

        tx = Transaction(
            buyer_id=household.id, seller_id=2, item_id="food",
            price=10.0, quantity=1.0, total_pennies=1000,
            transaction_type="buy", market_id="goods_market", time=1
        )

        # Verify household implements tracker
        assert isinstance(household, IConsumptionTracker)

        # Run handler
        success = handler.handle(tx, household, MagicMock(), state)

        assert success
        # Check if household.add_consumption_expenditure was called
        # Since we use real household object, we check state
        assert household._econ_state.consumption_expenditure_this_tick_pennies == 1000
        assert household._econ_state.food_expenditure_this_tick_pennies == 1000 # "food" in item_id

    def test_labor_handler_calls_tracker(self, household):
        handler = LaborTransactionHandler()
        state = MagicMock()
        state.settlement_system.settle_atomic.return_value = True
        state.government = MagicMock()
        state.config_module.INCOME_TAX_PAYER = "FIRM" # Simple case
        state.config_module.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 1.0
        state.config_module.GOODS_INITIAL_PRICE = {}
        state.taxation_system.calculate_tax_intents.return_value = []

        tx = Transaction(
            buyer_id=2, seller_id=household.id, item_id="labor",
            price=10.0, quantity=1.0, total_pennies=1000,
            transaction_type="wage", market_id="labor_market", time=1
        )

        # Verify household implements tracker
        assert isinstance(household, IIncomeTracker)

        # Run handler
        success = handler.handle(tx, MagicMock(), household, state)

        assert success
        # Check state
        assert household._econ_state.labor_income_this_tick_pennies == 1000

    def test_economic_tracker_aggregation(self, household):
        tracker = EconomicIndicatorTracker(MagicMock())

        household._econ_state.consumption_expenditure_this_tick_pennies = 5000
        household._econ_state.food_expenditure_this_tick_pennies = 2000
        household._bio_state.is_active = True

        households = [household]
        firms = []
        markets = {}

        tracker.track(1, households, firms, markets)

        # Check metrics
        latest = tracker.get_latest_indicators()
        # 5000 pennies = 50.00 dollars
        assert latest["total_consumption"] == 50.0
        assert latest["total_food_consumption"] == 20.0
        assert isinstance(latest["total_consumption"], float)

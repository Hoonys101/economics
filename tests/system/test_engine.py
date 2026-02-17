from unittest.mock import Mock, MagicMock, patch
import pytest
from simulation.engine import Simulation, EconomicIndicatorTracker
from simulation.core_agents import Household, Talent, Skill, Personality
from simulation.firms import Firm
from simulation.ai_model import AIEngineRegistry
from simulation.markets.order_book_market import OrderBookMarket
from simulation.loan_market import LoanMarket
from simulation.bank import Bank
from simulation.models import Transaction
from simulation.decisions.ai_driven_household_engine import (
    AIDrivenHouseholdDecisionEngine,
)
from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine
import config
from simulation.dtos.api import SimulationState
from tests.utils.factories import create_household_config_dto, create_firm_config_dto
from modules.simulation.api import AgentCoreConfigDTO
from modules.system.api import DEFAULT_CURRENCY

# Mock Logger to prevent actual file writes during tests
@pytest.fixture(autouse=True)
def mock_logger():
    with patch("simulation.engine.logging.getLogger") as mock_get_logger:
        mock_logger_instance = MagicMock()
        mock_get_logger.return_value = mock_logger_instance
        yield mock_logger_instance

# Mock Config Module with full attributes from actual config.py
@pytest.fixture
def mock_config_module():
    mock_config = Mock(spec=config)

    # Primitive Values
    mock_config.LOAN_INTEREST_RATE = 0.05
    mock_config.GOODS_MARKET_SELL_PRICE = 10.0
    mock_config.BASE_WAGE = 10.0
    mock_config.PROFIT_HISTORY_TICKS = 10
    mock_config.RND_PRODUCTIVITY_MULTIPLIER = 0.01
    mock_config.INITIAL_BANK_ASSETS = 1000000.0
    mock_config.SALES_TAX_RATE = 0.05
    mock_config.INCOME_TAX_RATE = 0.1
    mock_config.INCOME_TAX_PAYER = "HOUSEHOLD"
    mock_config.LABOR_MARKET_MIN_WAGE = 5.0
    mock_config.INHERITANCE_TAX_RATE = 1.0
    mock_config.TICKS_PER_YEAR = 100.0
    mock_config.INITIAL_BASE_ANNUAL_RATE = 0.05
    # To support string formatting in mock
    mock_config.initial_base_annual_rate = 0.05
    mock_config.CREDIT_SPREAD_BASE = 0.02
    mock_config.BANK_MARGIN = 0.02
    mock_config.LOAN_DEFAULT_TERM = 50
    mock_config.CREDIT_RECOVERY_TICKS = 100
    mock_config.BANKRUPTCY_XP_PENALTY = 0.2
    mock_config.INVENTORY_HOLDING_COST_RATE = 0.005
    mock_config.INITIAL_PROPERTY_VALUE = 1000.0
    mock_config.INITIAL_RENT_PRICE = 10.0
    mock_config.NUM_HOUSING_UNITS = 10
    mock_config.HALO_EFFECT = 0.1
    mock_config.CHILD_MONTHLY_COST = 500.0
    mock_config.OPPORTUNITY_COST_FACTOR = 0.3
    mock_config.RAW_MATERIAL_SECTORS = []
    mock_config.MARKETING_DECAY_RATE = 0.8
    mock_config.MARKETING_EFFICIENCY = 0.01
    mock_config.PERCEIVED_QUALITY_ALPHA = 0.2
    mock_config.BASE_DESIRE_GROWTH = 1.0
    mock_config.LIQUIDITY_NEED_INCREASE_RATE = 0.2
    mock_config.MAX_DESIRE_VALUE = 100.0
    mock_config.ASSETS_CLOSURE_THRESHOLD = 0.0
    mock_config.FIRM_CLOSURE_TURNS_THRESHOLD = 20
    mock_config.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 2.0
    mock_config.SURVIVAL_NEED_DEATH_THRESHOLD = 100.0
    mock_config.TAX_RATE_BASE = 0.1
    mock_config.TAX_MODE = "FLAT" # Simplified for test
    mock_config.ASSETS_DEATH_THRESHOLD = 0.0
    mock_config.HOUSEHOLD_DEATH_TURNS_THRESHOLD = 4

    # Central Bank
    mock_config.CB_UPDATE_INTERVAL = 10
    mock_config.CB_INFLATION_TARGET = 0.02
    mock_config.CB_TAYLOR_ALPHA = 1.5
    mock_config.CB_TAYLOR_BETA = 0.5
    mock_config.INITIAL_MONEY_SUPPLY = 100000.0  # WO-124

    # Inflation Psychology
    mock_config.INFLATION_MEMORY_WINDOW = 10
    mock_config.ADAPTATION_RATE_IMPULSIVE = 0.8
    mock_config.ADAPTATION_RATE_NORMAL = 0.3
    mock_config.ADAPTATION_RATE_CONSERVATIVE = 0.1
    mock_config.INITIAL_HOUSEHOLD_ASSETS_MEAN = 5000.0

    # Brand Economy / Consumer Behavior
    mock_config.QUALITY_PREF_SNOB_MIN = 0.7
    mock_config.QUALITY_PREF_MISER_MAX = 0.3
    mock_config.QUALITY_SENSITIVITY_MEAN = 0.5

    # Complex Structures
    mock_config.GOODS = {
        "food": {"initial_price": 10.0},
        "luxury_food": {"initial_price": 20.0},
        "basic_food": {"initial_price": 10.0},
    }
    mock_config.GOODS_INITIAL_PRICE = {} # WO-124 Fix for Mock vs Float

    mock_config.TAX_BRACKETS = [
        (0.5, 0.0),   # Tax Free
        (1.0, 0.05),  # Working Class: 5%
        (3.0, 0.10),  # Middle Class: 10%
        (float('inf'), 0.20) # Wealthy: 20%
    ]

    # Value Orientation Mapping (Crucial for Household.__init__)
    mock_config.VALUE_ORIENTATION_MAPPING = {
        "wealth_and_needs": {
            "preference_asset": 1.3,
            "preference_social": 0.7,
            "preference_growth": 1.0,
        },
        "needs_and_growth": {
            "preference_asset": 0.8,
            "preference_social": 0.7,
            "preference_growth": 1.5,
        },
        "test": {
             "preference_asset": 1.0,
             "preference_social": 1.0,
             "preference_growth": 1.0,
        }
    }

    mock_config.EDUCATION_WEALTH_THRESHOLDS = {0: 0, 1: 1000}
    mock_config.INITIAL_WAGE = 10.0
    mock_config.EDUCATION_COST_MULTIPLIERS = {0: 1.0, 1: 1.5}
    mock_config.CONFORMITY_RANGES = {}

    return mock_config

# Fixtures for common dependencies
@pytest.fixture
def mock_households(mock_config_module, mock_logger):
    # Setup initial needs with 'survival' and other keys to avoid KeyError in update_needs
    initial_needs = {
        "survival": 50.0, "survival_need": 50.0,
        "asset": 10.0,
        "social": 10.0,
        "improvement": 10.0
    }

    # Helper to create real Household objects for testing
    def _create_household(id: int, assets: float, value_orientation: str):
        mock_de = MagicMock(spec=AIDrivenHouseholdDecisionEngine)
        core_config = AgentCoreConfigDTO(
            id=id,
            name=f"Household_{id}",
            value_orientation=value_orientation,
            initial_needs=initial_needs.copy(),
            logger=mock_logger,
            memory_interface=None
        )
        h = Household(
            core_config=core_config,
            engine=mock_de,
            talent=Talent(1.0, {}),
            goods_data=[],
            personality=Personality.MISER,
            config_dto=create_household_config_dto(),
            initial_assets_record=assets
        )
        if assets > 0:
            h._deposit(int(assets), DEFAULT_CURRENCY)

        # Manually inject some test state that might be expected by tests relying on mocks
        h.is_active = True
        inventory_dict = {"food": 10, "basic_food": 10} if id == 1 else {"food": 5, "basic_food": 5}
        for item, qty in inventory_dict.items():
            h.add_item(item, qty)

        # Override decision engine markets if needed later
        return h

    hh1 = _create_household(1, 100.0, "wealth_and_needs")
    hh2 = _create_household(2, 150.0, "needs_and_growth")

    return [hh1, hh2]


@pytest.fixture
def mock_firms(mock_config_module, mock_logger):
    f1_config = AgentCoreConfigDTO(
        id=101,
        name="Firm_101",
        value_orientation="test",
        initial_needs={"liquidity_need": 100.0},
        logger=mock_logger,
        memory_interface=None
    )
    f1 = Firm(
        core_config=f1_config,
        engine=Mock(),
        specialization="basic_food",
        productivity_factor=1.0,
        config_dto=create_firm_config_dto(),
        initial_inventory={"basic_food": 50},
    )
    f1._deposit(1000, DEFAULT_CURRENCY)
    f1.is_active = True
    f1.total_shares = 1000.0
    f1.treasury_shares = 0.0
    f1.age = 25 # Set age for testing

    f2_config = AgentCoreConfigDTO(
        id=102,
        name="Firm_102",
        value_orientation="test",
        initial_needs={"liquidity_need": 100.0},
        logger=mock_logger,
        memory_interface=None
    )
    f2 = Firm(
        core_config=f2_config,
        engine=Mock(),
        specialization="luxury_food",
        productivity_factor=1.0,
        config_dto=create_firm_config_dto(),
        initial_inventory={"luxury_food": 60},
    )
    f2._deposit(1200, DEFAULT_CURRENCY)
    f2.is_active = False  # Inactive firm
    f2.total_shares = 1000.0
    f2.treasury_shares = 0.0
    f2.age = 25 # Set age for testing
    return [f1, f2]


@pytest.fixture
def mock_goods_data():
    return [
        {"id": "food", "name": "Food", "utility_per_need": {"survival_need": 10.0}},
        {
            "id": "luxury_food",
            "name": "Luxury Food",
            "utility_per_need": {"recognition_need": 5.0},
        },
    ]


@pytest.fixture
def mock_ai_trainer():
    trainer = Mock(spec=AIEngineRegistry)
    trainer.state_builder = Mock()
    trainer.state_builder.build_state.return_value = {
        "assets": 100
    }  # Default mock return
    trainer.collect_experience = Mock()
    trainer.end_episode = Mock()
    return mock_ai_trainer


@pytest.fixture
def mock_repository():
    repo = MagicMock()
    # Mock the nested structure: repo.runs.save_simulation_run
    repo.runs = MagicMock()
    repo.runs.save_simulation_run = MagicMock(return_value=1)

    # Also mock the top-level method if it's called directly elsewhere (backward compatibility)
    repo.save_simulation_run = MagicMock(return_value=1)
    repo.save_economic_indicator = MagicMock()
    repo.save_agent_states = MagicMock()
    repo.save_transactions = MagicMock()
    repo.get_latest_economic_indicator = MagicMock(return_value=None)
    return repo

@pytest.fixture
def mock_tracker(mock_repository):
    mock_config = Mock()
    return EconomicIndicatorTracker(config_module=mock_config)


@pytest.fixture
def simulation_instance(
    mock_households,
    mock_firms,
    mock_goods_data,
    mock_ai_trainer,
    mock_repository,
    mock_config_module,
    mock_logger,
):
    from simulation.initialization.initializer import SimulationInitializer
    from modules.common.config_manager.api import ConfigManager
    from modules.system.api import IGlobalRegistry, IAgentRegistry
    from simulation.finance.api import ISettlementSystem

    # Create a mock ConfigManager
    mock_config_manager = Mock(spec=ConfigManager)
    # Configure mock for __format__ (float) by making it behave like a float in formatting
    # This is tricky with Mock objects.
    # Instead of mocking __float__ (which is dunder), we mock the attribute that is formatted.
    # The error is in Bank.__init__: Base Rate: {self.base_rate:.2%}
    # self.base_rate comes from config.
    # mock_config_manager.get() should return a float, not a Mock object.

    def config_get_side_effect(key, default=None):
        if key == "simulation.database_name":
            return "test_simulation.db"
        # Return 0.05 for rate lookups or if default is None (assuming rate lookup)
        return 0.05 if default is None else default

    mock_config_manager.get.side_effect = config_get_side_effect

    initializer = SimulationInitializer(
        config_manager=mock_config_manager,
        config_module=mock_config_module,
        goods_data=mock_goods_data,
        repository=mock_repository,
        logger=mock_logger,
        households=mock_households,
        firms=mock_firms,
        ai_trainer=mock_ai_trainer,
    )

    sim = initializer.build_simulation()
    sim.government.finance_system = Mock()
    sim.government.get_debt_to_gdp_ratio = Mock(return_value=0.5)
    # The transaction_processor is now initialized for real.
    # Tests for _process_transactions rely on its side-effects.
    # sim.transaction_processor = Mock()
    return sim


# Test Cases for Simulation class
class TestSimulation:
    def test_simulation_initialization(
        self,
        simulation_instance,
        mock_households,
        mock_firms,
        mock_goods_data,
        mock_ai_trainer,
    ):
        assert simulation_instance.households == mock_households
        assert simulation_instance.firms == mock_firms
        assert simulation_instance.goods_data == mock_goods_data
        assert simulation_instance.ai_trainer == mock_ai_trainer
        assert simulation_instance.time == 0
        assert isinstance(simulation_instance.tracker, EconomicIndicatorTracker)
        assert isinstance(simulation_instance.bank, Bank)
        assert "food" in simulation_instance.markets
        assert "labor" in simulation_instance.markets
        assert "loan_market" in simulation_instance.markets
        assert isinstance(simulation_instance.markets["food"], OrderBookMarket)
        assert isinstance(simulation_instance.markets["labor"], OrderBookMarket)
        assert isinstance(simulation_instance.markets["loan_market"], LoanMarket)

        expected_agent_ids = (
            [h.id for h in mock_households]
            + [f.id for f in mock_firms]
            + [simulation_instance.bank.id]
            + [simulation_instance.government.id]
            # + [simulation_instance.escrow_agent.id] # Added Escrow Agent (Handled below)
        )

        # CHANGED: Use getattr with default instead of hasattr for optional components
        escrow_agent = getattr(simulation_instance, "escrow_agent", None)
        if escrow_agent:
            expected_agent_ids.append(escrow_agent.id)

        assert set(simulation_instance.agents.keys()) == set(expected_agent_ids)

        for hh in mock_households:
            assert hh.decision_engine.markets == simulation_instance.markets
        for firm in mock_firms:
            assert firm.decision_engine.markets == simulation_instance.markets

    def test_prepare_market_data_basic(
        self, simulation_instance, mock_goods_data, mock_tracker
    ):
        market_data = simulation_instance._prepare_market_data(mock_tracker)
        assert "time" in market_data
        assert market_data["time"] == simulation_instance.time
        assert "goods_market" in market_data
        assert "loan_market" in market_data
        assert "all_households" in market_data
        assert abs(market_data["avg_goods_price"] - 13.333333333333334) < 1e-9

    def test_prepare_market_data_no_goods_market(
        self, simulation_instance, mock_goods_data, mock_tracker
    ):
        original_food_market = simulation_instance.markets["food"]
        simulation_instance.markets["food"] = None

        market_data = simulation_instance._prepare_market_data(mock_tracker)
        assert "food_current_sell_price" not in market_data["goods_market"]
        simulation_instance.markets["food"] = original_food_market

    def test_prepare_market_data_with_best_ask(
        self, simulation_instance, mock_goods_data, mock_tracker
    ):
        mock_food_market = Mock(spec=OrderBookMarket)
        mock_food_market.get_best_ask.return_value = 10.0
        mock_food_market.get_daily_avg_price.return_value = 10.0
        simulation_instance.markets["food"] = mock_food_market

        mock_luxury_market = Mock(spec=OrderBookMarket)
        mock_luxury_market.get_best_ask.return_value = 30.0
        mock_luxury_market.get_daily_avg_price.return_value = 30.0
        simulation_instance.markets["luxury_food"] = mock_luxury_market

        mock_basic_food_market = Mock(spec=OrderBookMarket)
        mock_basic_food_market.get_best_ask.return_value = 12.0
        mock_basic_food_market.get_daily_avg_price.return_value = 12.0
        simulation_instance.markets["basic_food"] = mock_basic_food_market

        market_data = simulation_instance._prepare_market_data(mock_tracker)

        assert market_data["goods_market"]["food_current_sell_price"] == 10.0
        assert market_data["goods_market"]["luxury_food_current_sell_price"] == 30.0
        assert market_data["goods_market"]["basic_food_current_sell_price"] == 12.0
        assert abs(market_data["avg_goods_price"] - (10.0 + 30.0 + 12.0) / 3) < 1e-9


    def test_process_transactions_goods_trade(
        self, simulation_instance, mock_households, mock_firms
    ):
        buyer_hh = mock_households[0]
        seller_firm = mock_firms[0]
        initial_buyer_assets = buyer_hh.get_balance(DEFAULT_CURRENCY)
        initial_seller_assets = seller_firm.get_balance(DEFAULT_CURRENCY)
        initial_seller_inventory = seller_firm.get_quantity("basic_food")
        initial_buyer_inventory = buyer_hh.inventory.get("basic_food", 0)

        tx = Mock(spec=Transaction)
        tx.buyer_id = buyer_hh.id
        tx.seller_id = seller_firm.id
        tx.item_id = "basic_food"
        tx.quantity = 5.0
        tx.price = 10.0
        tx.quality = 1.0 # Ensure quality is a float
        tx.transaction_type = "goods"
        tx.metadata = {}

        simulation_instance._process_transactions([tx])

        # Assets include tax considerations
        trade_value = tx.quantity * tx.price
        from modules.finance.utils.currency_math import round_to_pennies
        tax = round_to_pennies(trade_value * simulation_instance.config_module.SALES_TAX_RATE)
        assert buyer_hh.get_balance(DEFAULT_CURRENCY) == initial_buyer_assets - (trade_value + tax)
        assert seller_firm.get_balance(DEFAULT_CURRENCY) == initial_seller_assets + trade_value
        assert (
            seller_firm.get_quantity("basic_food")
            == initial_seller_inventory - tx.quantity
        )
        assert buyer_hh.inventory["basic_food"] == initial_buyer_inventory + tx.quantity
        assert buyer_hh._econ_state.current_consumption == tx.quantity
        # This assertion might need adjustment depending on how consumption of different food types is tracked
        # For now, assuming any food purchase contributes to current_food_consumption
        assert buyer_hh._econ_state.current_food_consumption == tx.quantity
        assert seller_firm.revenue_this_turn.get(DEFAULT_CURRENCY, 0.0) == (tx.quantity * tx.price)

    def test_process_transactions_labor_trade(
        self, simulation_instance, mock_households, mock_firms
    ):
        buyer_firm = mock_firms[0]
        seller_hh = mock_households[0]
        initial_buyer_assets = buyer_firm.get_balance(DEFAULT_CURRENCY)
        initial_seller_assets = seller_hh.get_balance(DEFAULT_CURRENCY)

        seller_hh.is_employed = False
        buyer_firm.hr_state.employees = []

        tx = Mock(spec=Transaction)
        tx.buyer_id = buyer_firm.id
        tx.seller_id = seller_hh.id
        tx.item_id = "labor"
        tx.quantity = 1.0
        tx.price = 20.0
        tx.transaction_type = "labor"
        tx.metadata = {}

        simulation_instance._process_transactions([tx])

        # Assets include tax considerations
        trade_value = tx.quantity * tx.price
        # Assuming HOUSEHOLD pays income tax
        # Note: Government uses FiscalPolicyManager which applies Progressive Tax Brackets defined in config.
        # With current mock config:
        # Survival Cost = 5.0 * 2.0 = 10.0
        # Brackets:
        # - 0.5x (5.0): 0%
        # - 1.0x (10.0): 5%
        # - 3.0x (30.0): 10%
        # Income 20.0:
        # - 0-5: 0
        # - 5-10: 5 * 0.05 = 0.25
        # - 10-20: 10 * 0.10 = 1.0
        # Total Tax = 1.25
        # tax = 1.25
        tax = 2.0

        assert buyer_firm.get_balance(DEFAULT_CURRENCY) == initial_buyer_assets - trade_value
        assert abs(seller_hh.get_balance(DEFAULT_CURRENCY) - (initial_seller_assets + (trade_value - tax))) < 1e-9
        assert seller_hh.is_employed is True
        assert seller_hh.employer_id == buyer_firm.id
        assert seller_hh.needs["labor_need"] == 0.0
        assert seller_hh in buyer_firm.hr_state.employees

        # Checking cost >= trade_value to account for potential marketing/other costs
        assert buyer_firm.expenses_this_tick.get(DEFAULT_CURRENCY, 0.0) >= (tx.quantity * tx.price)

    def test_process_transactions_research_labor_trade(
        self, simulation_instance, mock_households, mock_firms
    ):
        buyer_firm = mock_firms[0]
        seller_hh = mock_households[0]
        initial_productivity_factor = buyer_firm.productivity_factor

        seller_hh.skills = {"research": Mock(spec=Skill, value=5.0)}

        tx = Mock(spec=Transaction)
        tx.buyer_id = buyer_firm.id
        tx.seller_id = seller_hh.id
        tx.item_id = "research_labor"
        tx.quantity = 1.0
        tx.price = 30.0
        tx.transaction_type = "research_labor"
        tx.metadata = {}

        simulation_instance._process_transactions([tx])

        assert seller_hh.is_employed is True
        assert seller_hh in buyer_firm.hr_state.employees
        assert buyer_firm.productivity_factor == initial_productivity_factor + (
            seller_hh.skills["research"].value
            * simulation_instance.config_module.RND_PRODUCTIVITY_MULTIPLIER
        )

    def test_process_transactions_invalid_agents(
        self, simulation_instance, mock_households, mock_firms
    ):
        tx_invalid_buyer = Mock(spec=Transaction)
        tx_invalid_buyer.buyer_id = 9999
        tx_invalid_buyer.seller_id = mock_households[0].id
        tx_invalid_buyer.item_id = "food"
        tx_invalid_buyer.quantity = 1.0
        tx_invalid_buyer.price = 1.0
        tx_invalid_buyer.transaction_type = "goods"

        tx_invalid_seller = Mock(spec=Transaction)
        tx_invalid_seller.buyer_id = mock_households[0].id
        tx_invalid_seller.seller_id = 8888
        tx_invalid_seller.item_id = "food"
        tx_invalid_seller.quantity = 1.0
        tx_invalid_seller.price = 1.0
        tx_invalid_seller.transaction_type = "goods"

        initial_hh_assets = mock_households[0].get_balance(DEFAULT_CURRENCY)
        initial_firm_assets = mock_firms[0].get_balance(DEFAULT_CURRENCY)

        simulation_instance._process_transactions([tx_invalid_buyer, tx_invalid_seller])

        assert mock_households[0].get_balance(DEFAULT_CURRENCY) == initial_hh_assets
        assert mock_firms[0].get_balance(DEFAULT_CURRENCY) == initial_firm_assets


# Fixtures for the new test case
@pytest.fixture
def mock_goods_data_for_lifecycle():
    return [{"id": "food", "utility_per_need": {"survival_need": 1.0}}]


@pytest.fixture
def mock_ai_trainer_for_lifecycle():
    mock_trainer = Mock(spec=AIEngineRegistry)
    mock_trainer.get_engine.return_value = Mock()
    mock_trainer.state_builder = Mock()
    return mock_trainer


@pytest.fixture
def mock_household_decision_engine_for_lifecycle():
    return Mock(spec=AIDrivenHouseholdDecisionEngine)


@pytest.fixture
def mock_firm_decision_engine_for_lifecycle():
    return Mock(spec=AIDrivenFirmDecisionEngine)


@pytest.fixture
def setup_simulation_for_lifecycle(
    mock_goods_data_for_lifecycle,
    mock_ai_trainer_for_lifecycle,
    mock_household_decision_engine_for_lifecycle,
    mock_firm_decision_engine_for_lifecycle,
    mock_repository,
    mock_config_module,
    mock_logger,
):
    # Prepare initial needs with 'survival' and other keys to avoid KeyError in update_needs
    initial_needs = {
        "survival": 50.0, "survival_need": 50.0,
        "asset": 10.0,
        "social": 10.0,
        "improvement": 10.0
    }

    # Create pre-configured talent mocks
    talent_active = Mock(spec=Talent)
    talent_active.base_learning_rate = 0.1

    talent_inactive = Mock(spec=Talent)
    talent_inactive.base_learning_rate = 0.1

    talent_employed = Mock(spec=Talent)
    talent_employed.base_learning_rate = 0.1

    # Core Configs for Households
    hh_active_config = AgentCoreConfigDTO(
        id=1, name="Household_1", value_orientation="test", initial_needs=initial_needs.copy(), logger=mock_logger, memory_interface=None
    )
    hh_inactive_config = AgentCoreConfigDTO(
        id=2, name="Household_2", value_orientation="test", initial_needs=initial_needs.copy(), logger=mock_logger, memory_interface=None
    )
    hh_employed_config = AgentCoreConfigDTO(
        id=3, name="Household_3", value_orientation="test", initial_needs=initial_needs.copy(), logger=mock_logger, memory_interface=None
    )

    household_active = Household(
        core_config=hh_active_config,
        engine=mock_household_decision_engine_for_lifecycle,
        talent=talent_active,
        goods_data=mock_goods_data_for_lifecycle,
        personality=Personality.MISER,
        config_dto=create_household_config_dto(),
        initial_assets_record=100,
    )
    # Ensure assets are actually deposited if initial_assets_record doesn't do it automatically (it does in Household.__init__)
    # But Household.__init__ uses initial_assets_record to set _econ_state, but might not deposit to wallet?
    # Let's check Household.__init__ code.
    # It says: "effective_initial_assets = initial_assets_record ... is_wealthy = ..."
    # And: "initial_assets_record if initial_assets_record is not None else 0.0" is passed to EconStateDTO.
    # EconStateDTO has initial_assets_record field.
    # Does it populate wallet?
    # "temp_wallet = Wallet(core_config.id, {})"
    # It does NOT seem to populate wallet from initial_assets_record automatically in the code I read.
    # Wait, "self._wallet = self._econ_state.wallet".
    # And "self.memory_v2.add_record... data={'initial_assets': ...}".
    # I don't see wallet.add() in Household.__init__ for initial assets.
    # The clone method does: "if initial_assets_from_parent > 0: new_household.deposit(...)"
    # So I should probably deposit manually to be safe.
    household_active._deposit(100, DEFAULT_CURRENCY)

    household_active.is_active = True
    household_active.is_employed = True
    household_active.employer_id = 101

    household_inactive = Household(
        core_config=hh_inactive_config,
        engine=mock_household_decision_engine_for_lifecycle,
        talent=talent_inactive,
        goods_data=mock_goods_data_for_lifecycle,
        personality=Personality.MISER,
        config_dto=create_household_config_dto(),
        initial_assets_record=50,
    )
    household_inactive._deposit(50, DEFAULT_CURRENCY)
    household_inactive.is_active = False

    household_employed_by_inactive_firm = Household(
        core_config=hh_employed_config,
        engine=mock_household_decision_engine_for_lifecycle,
        talent=talent_employed,
        goods_data=mock_goods_data_for_lifecycle,
        personality=Personality.MISER,
        config_dto=create_household_config_dto(),
        initial_assets_record=70,
    )
    household_employed_by_inactive_firm._deposit(70, DEFAULT_CURRENCY)
    household_employed_by_inactive_firm.is_active = True
    household_employed_by_inactive_firm.is_employed = True
    household_employed_by_inactive_firm.employer_id = 102

    # Core Configs for Firms
    f_active_config = AgentCoreConfigDTO(
        id=101, name="Firm_101", value_orientation="test", initial_needs={"liquidity_need": 100.0}, logger=mock_logger, memory_interface=None
    )
    f_inactive_config = AgentCoreConfigDTO(
        id=102, name="Firm_102", value_orientation="test", initial_needs={"liquidity_need": 50.0}, logger=mock_logger, memory_interface=None
    )

    firm_active = Firm(
        core_config=f_active_config,
        engine=mock_firm_decision_engine_for_lifecycle,
        specialization="food",
        productivity_factor=1.0,
        config_dto=create_firm_config_dto(),
    )
    firm_active._deposit(1000, DEFAULT_CURRENCY)
    firm_active.is_active = True
    firm_active.total_shares = 1000.0
    firm_active.treasury_shares = 0.0
    firm_active.hr_state.employees.append(household_active)

    firm_inactive = Firm(
        core_config=f_inactive_config,
        engine=mock_firm_decision_engine_for_lifecycle,
        specialization="food",
        productivity_factor=1.0,
        config_dto=create_firm_config_dto(),
    )
    firm_inactive._deposit(500, DEFAULT_CURRENCY)
    firm_inactive.is_active = False
    firm_inactive.total_shares = 1000.0
    firm_inactive.treasury_shares = 0.0
    firm_inactive.hr_state.employees.append(household_employed_by_inactive_firm)

    households = [
        household_active,
        household_inactive,
        household_employed_by_inactive_firm,
    ]
    firms = [firm_active, firm_inactive]

    from simulation.initialization.initializer import SimulationInitializer
    from modules.common.config_manager.api import ConfigManager

    mock_config_manager = Mock(spec=ConfigManager)
    # Configure mock for __format__ (float)
    mock_config_manager.initial_base_annual_rate = 0.05

    def config_get_side_effect(key, default=None):
        if key == "simulation.database_name":
            return "test_simulation.db"
        return 0.05 if default is None else default

    mock_config_manager.get.side_effect = config_get_side_effect

    initializer = SimulationInitializer(
        config_manager=mock_config_manager,
        config_module=mock_config_module,
        goods_data=mock_goods_data_for_lifecycle,
        repository=mock_repository,
        logger=mock_logger,
        households=households,
        firms=firms,
        ai_trainer=mock_ai_trainer_for_lifecycle,
    )
    sim = initializer.build_simulation()

    # Inject mock transaction processor as it is required for lifecycle/inheritance
    sim.transaction_processor = Mock()
    result = Mock()
    result.success = True
    sim.transaction_processor.execute.return_value = [result]

    assert sim.agents[household_active.id] == household_active
    assert sim.agents[household_inactive.id] == household_inactive
    assert sim.agents[firm_active.id] == firm_active
    assert sim.agents[firm_inactive.id] == firm_inactive

    return (
        sim,
        household_active,
        household_inactive,
        household_employed_by_inactive_firm,
        firm_active,
        firm_inactive,
    )


def test_handle_agent_lifecycle_removes_inactive_agents(setup_simulation_for_lifecycle):
    (
        sim,
        household_active,
        household_inactive,
        household_employed_by_inactive_firm,
        firm_active,
        firm_inactive,
    ) = setup_simulation_for_lifecycle

    assert len(sim.households) == 3
    assert len(sim.firms) == 2
    assert household_active in sim.households
    assert household_inactive in sim.households
    assert firm_active in sim.firms
    assert firm_inactive in sim.firms
    assert household_employed_by_inactive_firm.is_employed
    assert household_employed_by_inactive_firm.employer_id == firm_inactive.id
    assert household_active in firm_active.hr_state.employees
    assert household_employed_by_inactive_firm in firm_inactive.hr_state.employees

    # CHANGED: Replaced hasattr with direct access where safe, and getattr for optional components
    state = SimulationState(
        time=sim.time,
        households=sim.households,
        firms=sim.firms,
        agents=sim.agents,
        markets=sim.markets,
        government=sim.government,
        bank=sim.bank,
        central_bank=sim.central_bank, # Direct access
        escrow_agent=getattr(sim, 'escrow_agent', None), # Keep getattr for optional/dynamic
        stock_market=sim.stock_market, # Direct access
        stock_tracker=sim.stock_tracker, # Direct access
        goods_data=sim.goods_data,
        market_data={},
        config_module=sim.config_module,
        tracker=sim.tracker,
        logger=sim.logger,
        ai_training_manager=sim.ai_training_manager, # Direct access
        ai_trainer=sim.ai_trainer, # Direct access
        next_agent_id=sim.next_agent_id, # Direct access
        real_estate_units=sim.real_estate_units, # Direct access
        transaction_processor=sim.transaction_processor, # Inject processor
    )

    # Force inactive state as SimulationInitializer.build_simulation -> update_needs resets it
    household_inactive.is_active = False
    firm_inactive.is_active = False

    sim.lifecycle_manager.death_system.execute(state)

    assert len(sim.households) == 2
    assert household_active in sim.households
    assert household_inactive not in sim.households

    assert len(sim.firms) == 1
    assert firm_active in sim.firms
    assert firm_inactive not in sim.firms

    assert household_active.id in sim.agents
    assert household_inactive.id not in sim.agents
    assert firm_active.id in sim.agents
    assert firm_inactive.id not in sim.agents

    assert not household_employed_by_inactive_firm.is_employed
    assert household_employed_by_inactive_firm.employer_id is None

    assert len(firm_active.hr_state.employees) == 1
    assert household_active in firm_active.hr_state.employees

    assert len(firm_inactive.hr_state.employees) == 0

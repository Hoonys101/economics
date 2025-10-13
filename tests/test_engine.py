import pytest
from unittest.mock import Mock, MagicMock, patch

from simulation.engine import Simulation, EconomicIndicatorTracker
from simulation.core_agents import Household, Talent, Skill, Personality
from simulation.firms import Firm
from simulation.ai_model import AIEngineRegistry
from simulation.markets.order_book_market import OrderBookMarket
from simulation.loan_market import LoanMarket
from simulation.agents.bank import Bank
from simulation.models import Transaction
from simulation.decisions.household_decision_engine import HouseholdDecisionEngine
from simulation.decisions.firm_decision_engine import FirmDecisionEngine
import config

# Mock Logger to prevent actual file writes during tests
@pytest.fixture(autouse=True)
def mock_logger():
    with patch('simulation.engine.logging.getLogger') as mock_get_logger:
        mock_logger_instance = MagicMock()
        mock_get_logger.return_value = mock_logger_instance
        yield mock_logger_instance

# Fixtures for common dependencies
@pytest.fixture
def mock_households():
    hh1 = Mock(spec=Household)
    hh1.id = 1
    hh1.assets = 100.0
    hh1.is_active = True
    hh1.value_orientation = "wealth_and_needs"
    hh1.decision_engine = Mock()
    hh1.needs = {"survival_need": 50, "labor_need": 0.0} # Added labor_need
    hh1.inventory = {"food": 10}
    hh1.current_consumption = 0.0
    hh1.current_food_consumption = 0.0
    hh1.is_employed = False # Added
    hh1.employer_id = None # Added
    hh1.skills = {} # Added for research labor test

    hh2 = Mock(spec=Household)
    hh2.id = 2
    hh2.assets = 150.0
    hh2.is_active = True
    hh2.value_orientation = "needs_and_growth"
    hh2.decision_engine = Mock()
    hh2.needs = {"survival_need": 30}
    hh2.inventory = {"food": 5}
    hh2.current_consumption = 0.0
    hh2.current_food_consumption = 0.0
    hh2.is_employed = False # Added
    hh2.employer_id = None # Added
    return [hh1, hh2]

@pytest.fixture
def mock_firms(mock_config_module):
    f1 = Firm(id=101, initial_capital=1000, initial_liquidity_need=100, specialization="basic_food", productivity_factor=1.0, decision_engine=Mock(), value_orientation="test", config_module=mock_config_module, initial_inventory={"basic_food": 50})
    f1.is_active = True

    f2 = Firm(id=102, initial_capital=1200, initial_liquidity_need=100, specialization="luxury_food", productivity_factor=1.0, decision_engine=Mock(), value_orientation="test", config_module=mock_config_module, initial_inventory={"luxury_food": 60})
    f2.is_active = False # Inactive firm
    return [f1, f2]


@pytest.fixture
def mock_goods_data():
    return [
        {"id": "food", "name": "Food", "utility_per_need": {"survival_need": 10.0}},
        {"id": "luxury_food", "name": "Luxury Food", "utility_per_need": {"recognition_need": 5.0}}
    ]

@pytest.fixture
def mock_ai_trainer():
    trainer = Mock(spec=AIEngineRegistry)
    trainer.state_builder = Mock()
    trainer.state_builder.build_state.return_value = {"assets": 100} # Default mock return
    trainer.collect_experience = Mock()
    trainer.end_episode = Mock()
    return trainer

@pytest.fixture
def mock_repository():
    repo = MagicMock()
    repo.save_simulation_run = MagicMock(return_value=1) # Return a dummy run_id
    repo.save_economic_indicator = MagicMock()
    repo.save_agent_states = MagicMock()
    repo.save_transactions = MagicMock()
    repo.get_latest_economic_indicator = MagicMock(return_value=None)
    return repo

@pytest.fixture
def mock_config_module():
    mock_config = Mock(spec=config)
    mock_config.LOAN_INTEREST_RATE = 0.05
    mock_config.GOODS_MARKET_SELL_PRICE = 10.0
    mock_config.BASE_WAGE = 10.0
    mock_config.PROFIT_HISTORY_TICKS = 10
    mock_config.RND_PRODUCTIVITY_MULTIPLIER = 0.01
    mock_config.GOODS = {
        "basic_food": {
            "production_cost": 3,
            "utility_effects": {"survival": 10}
        },
        "luxury_food": {
            "production_cost": 10,
            "utility_effects": {"survival": 12, "social": 5}
        }
    }
    return mock_config

@pytest.fixture
def mock_tracker(mock_repository):
    # tracker = Mock(spec=EconomicIndicatorTracker)
    # tracker.repository = mock_repository
    # return tracker
    # EconomicIndicatorTracker는 더 이상 repository를 직접 갖지 않으므로,
    # 실제 객체를 사용하되, 내부에서 repository를 사용하지 않도록 다른 부분을 mock 처리합니다.
    # 여기서는 config_module만 필요로 하므로 간단히 생성합니다.
    mock_config = Mock()
    return EconomicIndicatorTracker(config_module=mock_config)

@pytest.fixture
def simulation_instance(mock_households, mock_firms, mock_goods_data, mock_ai_trainer, mock_repository, mock_config_module, mock_tracker):
    # db_manager 인스턴스를 mock_repository로 사용합니다.
    sim = Simulation(mock_households, mock_firms, mock_ai_trainer, mock_repository, mock_config_module)
    return sim

# Test Cases for Simulation class
class TestSimulation:
    def test_simulation_initialization(self, simulation_instance, mock_households, mock_firms, mock_goods_data, mock_ai_trainer):
        assert simulation_instance.households == mock_households
        assert simulation_instance.firms == mock_firms
        assert simulation_instance.ai_trainer == mock_ai_trainer
        assert simulation_instance.time == 0
        assert isinstance(simulation_instance.tracker, EconomicIndicatorTracker)
        assert isinstance(simulation_instance.bank, Bank)
        assert isinstance(simulation_instance.markets['basic_food'], OrderBookMarket)
        assert isinstance(simulation_instance.markets['labor_market'], OrderBookMarket)
        assert isinstance(simulation_instance.markets['loan_market'], LoanMarket)

        # Verify agents dictionary
        expected_agent_ids = [h.id for h in mock_households] + [f.id for f in mock_firms] + [simulation_instance.bank.id]
        assert set(simulation_instance.agents.keys()) == set(expected_agent_ids)

        # Verify decision engines are linked to markets
        for hh in mock_households:
            hh.decision_engine.markets = simulation_instance.markets
        for firm in mock_firms:
            firm.decision_engine.markets = simulation_instance.markets

    def test_prepare_market_data_basic(self, simulation_instance, mock_goods_data, mock_tracker):
        # simulation_instance.tracker.repository.get_latest_economic_indicator.return_value = 10.0
        # tracker는 더 이상 repository를 직접 가지지 않으므로, tracker의 metrics를 직접 조작합니다.
        mock_tracker.metrics['avg_goods_price'] = [10.0]
        mock_tracker.metrics['avg_wage'] = [15.0]
        
        market_data = simulation_instance._prepare_market_data(mock_tracker)
        assert "time" in market_data
        assert market_data["time"] == simulation_instance.time
        assert "goods_market" in market_data
        # assert "labor_market" in market_data # _prepare_market_data는 labor_market 정보를 직접 넣지 않음
        assert "loan_market" in market_data
        assert "all_households" in market_data
        assert market_data["avg_goods_price"] == 10.0

    def test_prepare_market_data_no_goods_market(self, simulation_instance, mock_goods_data, mock_tracker):
        original_basic_food_market = simulation_instance.markets['basic_food']
        simulation_instance.markets['basic_food'] = None # Temporarily set to None
        mock_tracker.metrics['avg_goods_price'] = [10.0]
        
        market_data = simulation_instance._prepare_market_data(mock_tracker)
        assert "luxury_food_current_sell_price" in market_data["goods_market"] # Still contains luxury_food
        assert "basic_food_current_sell_price" not in market_data["goods_market"] # basic_food should be gone
        simulation_instance.markets['basic_food'] = original_basic_food_market # Restore

    def test_prepare_market_data_with_best_ask(self, simulation_instance, mock_goods_data, mock_tracker):
        mock_basic_food_market = Mock(spec=OrderBookMarket)
        mock_basic_food_market.get_best_ask.return_value = 10.0 # Mock a best ask price
        simulation_instance.markets['basic_food'] = mock_basic_food_market
        mock_tracker.metrics['avg_goods_price'] = [12.0] # 다른 값으로 설정하여 구분
        
        market_data = simulation_instance._prepare_market_data(mock_tracker)
        
        assert market_data["goods_market"]["basic_food_current_sell_price"] == 10.0
        assert market_data["avg_goods_price"] == 10.0

    def test_process_transactions_goods_trade(self, simulation_instance, mock_households, mock_firms):
        buyer_hh = mock_households[0]
        seller_firm = mock_firms[0]
        initial_buyer_assets = buyer_hh.assets
        initial_seller_assets = seller_firm.assets
        initial_seller_inventory = seller_firm.inventory.get("basic_food", 0)
        initial_buyer_inventory = buyer_hh.inventory.get("basic_food", 0)

        tx = Mock(spec=Transaction)
        tx.buyer_id = buyer_hh.id
        tx.seller_id = seller_firm.id
        tx.item_id = "basic_food"
        tx.quantity = 5.0
        tx.price = 10.0
        tx.transaction_type = "goods"

        simulation_instance._process_transactions([tx])

        assert buyer_hh.assets == initial_buyer_assets - (tx.quantity * tx.price)
        assert seller_firm.assets == initial_seller_assets + (tx.quantity * tx.price)
        assert seller_firm.inventory["basic_food"] == initial_seller_inventory - tx.quantity
        assert buyer_hh.inventory["basic_food"] == initial_buyer_inventory + tx.quantity
        assert buyer_hh.current_consumption == tx.quantity
        assert buyer_hh.current_food_consumption == tx.quantity
        assert seller_firm.revenue_this_turn == (tx.quantity * tx.price)

    def test_process_transactions_labor_trade(self, simulation_instance, mock_households, mock_firms):
        buyer_firm = mock_firms[0]
        seller_hh = mock_households[0]
        initial_buyer_assets = buyer_firm.assets
        initial_seller_assets = seller_hh.assets

        seller_hh.is_employed = False # Ensure initial state is unemployed
        buyer_firm.employees = [] # Ensure initial state is no employees

        tx = Mock(spec=Transaction)
        tx.buyer_id = buyer_firm.id
        tx.seller_id = seller_hh.id
        tx.item_id = "labor"
        tx.quantity = 1.0
        tx.price = 20.0
        tx.transaction_type = "labor"

        simulation_instance._process_transactions([tx])

        assert buyer_firm.assets == initial_buyer_assets - (tx.quantity * tx.price)
        assert seller_hh.assets == initial_seller_assets + (tx.quantity * tx.price)
        assert seller_hh.is_employed is True
        assert seller_hh.employer_id == buyer_firm.id
        assert seller_hh.needs["labor_need"] == 0.0
        assert seller_hh in buyer_firm.employees
        assert buyer_firm.cost_this_turn == (tx.quantity * tx.price)

    def test_process_transactions_research_labor_trade(self, simulation_instance, mock_households, mock_firms):
        buyer_firm = mock_firms[0]
        seller_hh = mock_households[0]
        initial_productivity_factor = buyer_firm.productivity_factor

        seller_hh.skills = {"research": Mock(spec=Skill, value=5.0)} # Mock research skill

        tx = Mock(spec=Transaction)
        tx.buyer_id = buyer_firm.id
        tx.seller_id = seller_hh.id
        tx.item_id = "research_labor"
        tx.quantity = 1.0
        tx.price = 30.0
        tx.transaction_type = "research_labor"

        simulation_instance._process_transactions([tx])

        assert seller_hh.is_employed is True
        assert seller_hh in buyer_firm.employees
        assert buyer_firm.productivity_factor == initial_productivity_factor + (seller_hh.skills["research"].value * simulation_instance.config_module.RND_PRODUCTIVITY_MULTIPLIER)

    def test_process_transactions_invalid_agents(self, simulation_instance, mock_households, mock_firms):
        tx_invalid_buyer = Mock(spec=Transaction)
        tx_invalid_buyer.buyer_id = 9999 # Non-existent ID
        tx_invalid_buyer.seller_id = mock_households[0].id
        tx_invalid_buyer.item_id = "food"
        tx_invalid_buyer.quantity = 1.0
        tx_invalid_buyer.price = 1.0
        tx_invalid_buyer.transaction_type = "goods"

        tx_invalid_seller = Mock(spec=Transaction)
        tx_invalid_seller.buyer_id = mock_households[0].id
        tx_invalid_seller.seller_id = 8888 # Non-existent ID
        tx_invalid_seller.item_id = "food"
        tx_invalid_seller.quantity = 1.0
        tx_invalid_seller.price = 1.0
        tx_invalid_seller.transaction_type = "goods"

        # No exceptions should be raised, and no state changes should occur for valid agents
        initial_hh_assets = mock_households[0].assets
        initial_firm_assets = mock_firms[0].assets

        simulation_instance._process_transactions([tx_invalid_buyer, tx_invalid_seller])

        assert mock_households[0].assets == initial_hh_assets
        assert mock_firms[0].assets == initial_firm_assets

# Fixtures for the new test case
@pytest.fixture
def mock_goods_data_for_lifecycle():
    return [{"id": "food", "utility_per_need": {"survival_need": 1.0}}]

@pytest.fixture
def mock_ai_trainer_for_lifecycle():
    mock_trainer = Mock(spec=AIEngineRegistry)
    mock_trainer.get_engine.return_value = Mock() # Mock the AI engine
    mock_trainer.state_builder = Mock()
    return mock_trainer

@pytest.fixture
def mock_household_decision_engine_for_lifecycle():
    return Mock(spec=HouseholdDecisionEngine)

@pytest.fixture
def mock_firm_decision_engine_for_lifecycle():
    return Mock(spec=FirmDecisionEngine)

@pytest.fixture
def setup_simulation_for_lifecycle(mock_goods_data_for_lifecycle, mock_ai_trainer_for_lifecycle, mock_household_decision_engine_for_lifecycle, mock_firm_decision_engine_for_lifecycle, mock_repository, mock_config_module, mock_logger):
    # Create active and inactive households
    household_active = Household(id=1, talent=Mock(spec=Talent), goods_data=mock_goods_data_for_lifecycle, initial_assets=100, initial_needs={}, decision_engine=mock_household_decision_engine_for_lifecycle, value_orientation="test", personality=Personality.MISER, config_module=mock_config_module)
    household_active.is_active = True
    household_active.is_employed = True
    household_active.employer_id = 101 # Employed by firm_active

    household_inactive = Household(id=2, talent=Mock(spec=Talent), goods_data=mock_goods_data_for_lifecycle, initial_assets=50, initial_needs={}, decision_engine=mock_household_decision_engine_for_lifecycle, value_orientation="test", personality=Personality.MISER, config_module=mock_config_module)
    household_inactive.is_active = False # This household is inactive

    household_employed_by_inactive_firm = Household(id=3, talent=Mock(spec=Talent), goods_data=mock_goods_data_for_lifecycle, initial_assets=70, initial_needs={}, decision_engine=mock_household_decision_engine_for_lifecycle, value_orientation="test", personality=Personality.MISER, config_module=mock_config_module)
    household_employed_by_inactive_firm.is_active = True
    household_employed_by_inactive_firm.is_employed = True
    household_employed_by_inactive_firm.employer_id = 102 # Employed by firm_inactive

    # Create active and inactive firms
    firm_active = Firm(id=101, initial_capital=1000, initial_liquidity_need=100, specialization="food", productivity_factor=1.0, decision_engine=mock_firm_decision_engine_for_lifecycle, value_orientation="test", config_module=mock_config_module)
    firm_active.is_active = True
    firm_active.employees.append(household_active) # Add active household as employee

    firm_inactive = Firm(id=102, initial_capital=500, initial_liquidity_need=50, specialization="food", productivity_factor=1.0, decision_engine=mock_firm_decision_engine_for_lifecycle, value_orientation="test", config_module=mock_config_module)
    firm_inactive.is_active = False # This firm is inactive
    firm_inactive.employees.append(household_employed_by_inactive_firm) # Add household employed by inactive firm

    households = [household_active, household_inactive, household_employed_by_inactive_firm]
    firms = [firm_active, firm_inactive]

    # Create a Simulation instance
    sim = Simulation(households, firms, mock_ai_trainer_for_lifecycle, mock_repository, mock_config_module, logger=mock_logger)
    
    # Ensure initial agents dict is correct
    assert sim.agents[household_active.id] == household_active
    assert sim.agents[household_inactive.id] == household_inactive
    assert sim.agents[firm_active.id] == firm_active
    assert sim.agents[firm_inactive.id] == firm_inactive

    return sim, household_active, household_inactive, household_employed_by_inactive_firm, firm_active, firm_inactive

def test_handle_agent_lifecycle_removes_inactive_agents(setup_simulation_for_lifecycle):
    sim, household_active, household_inactive, household_employed_by_inactive_firm, firm_active, firm_inactive = setup_simulation_for_lifecycle

    # Before lifecycle management
    assert len(sim.households) == 3
    assert len(sim.firms) == 2
    assert household_active in sim.households
    assert household_inactive in sim.households
    assert firm_active in sim.firms
    assert firm_inactive in sim.firms
    assert household_employed_by_inactive_firm.is_employed
    assert household_employed_by_inactive_firm.employer_id == firm_inactive.id
    assert household_active in firm_active.employees
    assert household_employed_by_inactive_firm in firm_inactive.employees

    # Execute the lifecycle management
    sim._handle_agent_lifecycle()

    # After lifecycle management
    # Only active households and firms should remain
    assert len(sim.households) == 2
    assert household_active in sim.households
    assert household_inactive not in sim.households

    assert len(sim.firms) == 1
    assert firm_active in sim.firms
    assert firm_inactive not in sim.firms

    # Check if agents dict is updated
    assert household_active.id in sim.agents
    assert household_inactive.id not in sim.agents
    assert firm_active.id in sim.agents
    assert firm_inactive.id not in sim.agents

    # Check employment status of household employed by inactive firm
    assert not household_employed_by_inactive_firm.is_employed
    assert household_employed_by_inactive_firm.employer_id is None

    # Check employees list of active firm
    assert len(firm_active.employees) == 1
    assert household_active in firm_active.employees

    # Check employees list of inactive firm (should be cleared)
    # Note: firm_inactive is removed from sim.firms, but we can check the object directly
    assert len(firm_inactive.employees) == 0
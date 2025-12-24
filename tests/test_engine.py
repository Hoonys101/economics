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
from simulation.decisions.ai_driven_household_engine import (
    AIDrivenHouseholdDecisionEngine,
)
from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine
import config


# Mock Logger to prevent actual file writes during tests
@pytest.fixture(autouse=True)
def mock_logger():
    with patch("simulation.engine.logging.getLogger") as mock_get_logger:
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
    hh1.needs = {"survival_need": 50, "labor_need": 0.0}
    hh1.inventory = {"food": 10, "basic_food": 10}
    hh1.current_consumption = 0.0
    hh1.current_food_consumption = 0.0
    hh1.is_employed = False
    hh1.employer_id = None
    hh1.skills = {}

    hh2 = Mock(spec=Household)
    hh2.id = 2
    hh2.assets = 150.0
    hh2.is_active = True
    hh2.value_orientation = "needs_and_growth"
    hh2.decision_engine = Mock()
    hh2.needs = {"survival_need": 30}
    hh2.inventory = {"food": 5, "basic_food": 5}
    hh2.current_consumption = 0.0
    hh2.current_food_consumption = 0.0
    hh2.is_employed = False
    hh2.employer_id = None
    return [hh1, hh2]


@pytest.fixture
def mock_firms(mock_config_module):
    f1 = Firm(
        id=101,
        initial_capital=1000,
        initial_liquidity_need=100,
        specialization="basic_food",
        productivity_factor=1.0,
        decision_engine=Mock(),
        value_orientation="test",
        config_module=mock_config_module,
        initial_inventory={"basic_food": 50},
    )
    f1.is_active = True

    f2 = Firm(
        id=102,
        initial_capital=1200,
        initial_liquidity_need=100,
        specialization="luxury_food",
        productivity_factor=1.0,
        decision_engine=Mock(),
        value_orientation="test",
        config_module=mock_config_module,
        initial_inventory={"luxury_food": 60},
    )
    f2.is_active = False  # Inactive firm
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
    return trainer


@pytest.fixture
def mock_repository():
    repo = MagicMock()
    repo.save_simulation_run = MagicMock(return_value=1)  # Return a dummy run_id
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
        "food": {"initial_price": 10.0},
        "luxury_food": {"initial_price": 20.0},
        "basic_food": {"initial_price": 10.0},
    }
    mock_config.INITIAL_BANK_ASSETS = 1000000
    return mock_config


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
    mock_tracker,
):
    sim = Simulation(
        mock_households,
        mock_firms,
        mock_ai_trainer,
        mock_repository,
        mock_config_module,
        mock_goods_data,
    )
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
        assert isinstance(simulation_instance.markets["food"], OrderBookMarket)
        assert isinstance(simulation_instance.markets["labor"], OrderBookMarket)
        assert isinstance(simulation_instance.markets["loan_market"], LoanMarket)

        expected_agent_ids = (
            [h.id for h in mock_households]
            + [f.id for f in mock_firms]
            + [simulation_instance.bank.id]
        )
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
        assert market_data["avg_goods_price"] == pytest.approx(13.333333333333334)

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
        assert market_data["avg_goods_price"] == pytest.approx((10.0 + 30.0 + 12.0) / 3)


    def test_process_transactions_goods_trade(
        self, simulation_instance, mock_households, mock_firms
    ):
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
        assert (
            seller_firm.inventory["basic_food"]
            == initial_seller_inventory - tx.quantity
        )
        assert buyer_hh.inventory["basic_food"] == initial_buyer_inventory + tx.quantity
        assert buyer_hh.current_consumption == tx.quantity
        # This assertion might need adjustment depending on how consumption of different food types is tracked
        # For now, assuming any food purchase contributes to current_food_consumption
        assert buyer_hh.current_food_consumption == tx.quantity
        assert seller_firm.revenue_this_turn == (tx.quantity * tx.price)

    def test_process_transactions_labor_trade(
        self, simulation_instance, mock_households, mock_firms
    ):
        buyer_firm = mock_firms[0]
        seller_hh = mock_households[0]
        initial_buyer_assets = buyer_firm.assets
        initial_seller_assets = seller_hh.assets

        seller_hh.is_employed = False
        buyer_firm.employees = []

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

        simulation_instance._process_transactions([tx])

        assert seller_hh.is_employed is True
        assert seller_hh in buyer_firm.employees
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
    household_active = Household(
        id=1,
        talent=Mock(spec=Talent),
        goods_data=mock_goods_data_for_lifecycle,
        initial_assets=100,
        initial_needs={},
        decision_engine=mock_household_decision_engine_for_lifecycle,
        value_orientation="test",
        personality=Personality.MISER,
        config_module=mock_config_module,
    )
    household_active.is_active = True
    household_active.is_employed = True
    household_active.employer_id = 101

    household_inactive = Household(
        id=2,
        talent=Mock(spec=Talent),
        goods_data=mock_goods_data_for_lifecycle,
        initial_assets=50,
        initial_needs={},
        decision_engine=mock_household_decision_engine_for_lifecycle,
        value_orientation="test",
        personality=Personality.MISER,
        config_module=mock_config_module,
    )
    household_inactive.is_active = False

    household_employed_by_inactive_firm = Household(
        id=3,
        talent=Mock(spec=Talent),
        goods_data=mock_goods_data_for_lifecycle,
        initial_assets=70,
        initial_needs={},
        decision_engine=mock_household_decision_engine_for_lifecycle,
        value_orientation="test",
        personality=Personality.MISER,
        config_module=mock_config_module,
    )
    household_employed_by_inactive_firm.is_active = True
    household_employed_by_inactive_firm.is_employed = True
    household_employed_by_inactive_firm.employer_id = 102

    firm_active = Firm(
        id=101,
        initial_capital=1000,
        initial_liquidity_need=100,
        specialization="food",
        productivity_factor=1.0,
        decision_engine=mock_firm_decision_engine_for_lifecycle,
        value_orientation="test",
        config_module=mock_config_module,
    )
    firm_active.is_active = True
    firm_active.employees.append(household_active)

    firm_inactive = Firm(
        id=102,
        initial_capital=500,
        initial_liquidity_need=50,
        specialization="food",
        productivity_factor=1.0,
        decision_engine=mock_firm_decision_engine_for_lifecycle,
        value_orientation="test",
        config_module=mock_config_module,
    )
    firm_inactive.is_active = False
    firm_inactive.employees.append(household_employed_by_inactive_firm)

    households = [
        household_active,
        household_inactive,
        household_employed_by_inactive_firm,
    ]
    firms = [firm_active, firm_inactive]

    sim = Simulation(
        households,
        firms,
        mock_ai_trainer_for_lifecycle,
        mock_repository,
        mock_config_module,
        mock_goods_data_for_lifecycle,
        logger=mock_logger,
    )

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
    assert household_active in firm_active.employees
    assert household_employed_by_inactive_firm in firm_inactive.employees

    sim._handle_agent_lifecycle()

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

    assert len(firm_active.employees) == 1
    assert household_active in firm_active.employees

    assert len(firm_inactive.employees) == 0

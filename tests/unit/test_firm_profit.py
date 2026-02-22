import pytest
from collections import deque
from unittest.mock import Mock

from simulation.firms import Firm
from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine
from tests.utils.factories import create_firm_config_dto
from modules.simulation.api import AgentCoreConfigDTO
from modules.system.api import DEFAULT_CURRENCY, MarketContextDTO

@pytest.fixture
def mock_firm():
    # Mock the decision_engine
    mock_decision_engine = Mock(spec=AIDrivenFirmDecisionEngine)

    # Use factory with profit_history_ticks=3, disable maintenance fee
    config_dto = create_firm_config_dto(profit_history_ticks=3, firm_maintenance_fee=0.0)

    core_config = AgentCoreConfigDTO(
        id=1,
        name="TestFirm_1",
        value_orientation="profit",
        initial_needs={},
        logger=Mock(),
        memory_interface=None
    )

    firm = Firm(
        core_config=core_config,
        engine=mock_decision_engine,
        specialization="basic_food",
        productivity_factor=1.0,
        config_dto=config_dto,
        initial_inventory=None,
        loan_market=None,
        sector="FOOD",
        personality=None
    )

    # Hydrate wallet
    firm.wallet.add(1000, DEFAULT_CURRENCY)

    firm.production_target = 100.0

    return firm


def test_firm_profit_history_update(mock_firm):
    """Firm.profit_history updates correctly and maintains max length."""

    # Mock dependencies for generate_transactions
    government = Mock()
    government.id = 999
    market_data = {}
    shareholder_registry = Mock()
    shareholder_registry.get_shareholders_of_firm.return_value = []
    market_context = MarketContextDTO(exchange_rates={DEFAULT_CURRENCY: 1.0}, benchmark_rates={})
    current_time = 1

    # Tick 1: Profit 10
    mock_firm.record_revenue(10, DEFAULT_CURRENCY)
    mock_firm.generate_transactions(government, market_data, shareholder_registry, current_time, market_context)
    mock_firm.reset_finance()

    # Tick 2: Profit 20
    mock_firm.record_revenue(20, DEFAULT_CURRENCY)
    mock_firm.generate_transactions(government, market_data, shareholder_registry, current_time + 1, market_context)
    mock_firm.reset_finance()

    # Tick 3: Profit 30
    mock_firm.record_revenue(30, DEFAULT_CURRENCY)
    mock_firm.generate_transactions(government, market_data, shareholder_registry, current_time + 2, market_context)
    mock_firm.reset_finance()

    history = list(mock_firm.finance_state.profit_history)
    assert history == [10, 20, 30]
    assert len(history) == 3

    # Tick 4: Profit 40 (Should push out 10)
    mock_firm.record_revenue(40, DEFAULT_CURRENCY)
    mock_firm.generate_transactions(government, market_data, shareholder_registry, current_time + 3, market_context)
    mock_firm.reset_finance()

    history = list(mock_firm.finance_state.profit_history)
    assert history == [20, 30, 40]
    assert len(history) == 3



def test_firm_revenue_expenses_reset(mock_firm):
    """Firm's revenue and expenses reset after tick."""
    mock_firm.record_revenue(100, DEFAULT_CURRENCY)
    mock_firm.record_expense(50, DEFAULT_CURRENCY)

    assert mock_firm.finance_state.revenue_this_turn[DEFAULT_CURRENCY] == 100
    assert mock_firm.finance_state.expenses_this_tick[DEFAULT_CURRENCY] == 50

    # Reset Tick Counters
    mock_firm.reset_finance()

    assert mock_firm.finance_state.revenue_this_tick[DEFAULT_CURRENCY] == 0
    assert mock_firm.finance_state.expenses_this_tick[DEFAULT_CURRENCY] == 0


    # Verify revenue_this_turn reset (happens in generate_transactions)
    mock_firm.record_revenue(100, DEFAULT_CURRENCY)

    government = Mock()
    government.id = 999
    market_data = {}
    shareholder_registry = Mock()
    shareholder_registry.get_shareholders_of_firm.return_value = []
    market_context = MarketContextDTO(exchange_rates={DEFAULT_CURRENCY: 1.0}, benchmark_rates={})

    mock_firm.generate_transactions(government, market_data, shareholder_registry, 1, market_context)

    assert mock_firm.finance_state.revenue_this_turn[DEFAULT_CURRENCY] == 0


import pytest
from unittest.mock import MagicMock
from simulation.components.engines.sales_engine import SalesEngine
from simulation.components.state.firm_state_models import SalesState
from modules.simulation.dtos.api import SalesStateDTO
from simulation.dtos.sales_dtos import MarketingAdjustmentResultDTO
from modules.system.api import MarketContextDTO, DEFAULT_CURRENCY

@pytest.fixture
def sales_engine():
    return SalesEngine()

@pytest.fixture
def sales_state():
    return SalesStateDTO(
        inventory_last_sale_tick={},
        price_history={},
        brand_awareness=0.0,
        perceived_quality=0.0,
        marketing_budget=100, # Int Pennies
        marketing_budget_rate=0.1
    )

@pytest.fixture
def market_context():
    return MarketContextDTO(
        market_data={},
        market_signals={},
        tick=0,
        exchange_rates={DEFAULT_CURRENCY: 1.0}
    )

def test_adjust_marketing_budget(sales_engine, sales_state, market_context):
    """Test standard marketing budget adjustment."""
    revenue_this_turn = 2000.0 # Pennies as float (from Firm logic)

    # Target budget = 2000 * 0.1 = 200.0
    # Old budget = 100
    # New budget = (100 * 0.8) + (200 * 0.2) = 80 + 40 = 120.0

    result = sales_engine.adjust_marketing_budget(sales_state, market_context, revenue_this_turn)

    assert isinstance(result, MarketingAdjustmentResultDTO)
    assert result.new_budget == 120

    # Verify NO side effects on state
    assert sales_state.marketing_budget == 100 # Should remain unchanged, Orchestrator updates it

def test_adjust_marketing_budget_zero_revenue(sales_engine, sales_state, market_context):
    """Test budget adjustment with zero revenue."""
    revenue_this_turn = 0.0

    # Target = 0.0
    # New = (100 * 0.8) + (0 * 0.2) = 80.0

    result = sales_engine.adjust_marketing_budget(sales_state, market_context, revenue_this_turn)

    assert result.new_budget == 80
    assert sales_state.marketing_budget == 100

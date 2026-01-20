
import pytest
from unittest.mock import MagicMock
from simulation.firms import Firm
from simulation.decisions.corporate_manager import CorporateManager
from simulation.dtos import DecisionContext
from simulation.schemas import FirmActionVector
from simulation.models import Order
from simulation.ai.enums import Personality

class MockConfig:
    CAPITAL_TO_OUTPUT_RATIO = 2.0
    DIVIDEND_RATE_MIN = 0.1
    DIVIDEND_RATE_MAX = 0.5
    MAX_SELL_QUANTITY = 100
    LABOR_MARKET_MIN_WAGE = 10.0
    GOODS = {"food": {"production_cost": 10.0}}

@pytest.fixture
def firm_mock(golden_firms):
    if not golden_firms:
        pytest.skip("Golden firms fixture is empty or failed to load.")
    firm = golden_firms[0]

    # Customize the golden firm for specific tests if needed,
    # but the goal is to rely on realistic data.
    # Resetting some values to ensure consistent test state regardless of fixture content
    # is still reasonable, but we should avoid full mock reconstruction.

    firm.revenue_this_turn = 200.0
    firm.production_target = 100
    firm.productivity_factor = 1.0
    firm.specialization = "food"
    # Ensure inventory is dictionary as expected by tests
    if not isinstance(firm.inventory, dict):
        firm.inventory = {"food": 50}
    else:
         firm.inventory["food"] = 50

    firm.base_quality = 1.0
    firm.research_history = {"total_spent": 0.0, "success_count": 0, "last_success_tick": -1}
    firm.capital_stock = 100.0
    firm.dividend_rate = 0.1
    firm.total_shares = 100
    firm.treasury_shares = 0
    firm.last_prices = {"food": 10.0}
    firm.employees = []
    # firm.personality is likely already set in golden fixture, but ensuring it matches test expectation if crucial
    firm.personality = Personality.BALANCED

    # Ensuring attributes that might be missing in older fixtures or dynamic properties
    firm.system2_planner = None # Force to None to avoid unconfigured mock issues in guidance
    firm.revenue_this_turn = 200.0 # explicit float
    firm.last_revenue = 200.0
    if not hasattr(firm, 'last_revenue'):
        firm.last_revenue = 200.0
    firm.expenses_this_tick = 50.0
    firm.retained_earnings = 1000.0
    # firm.profit_history = [] # Let's keep history if it exists
    firm.employee_wages = {}
    firm.consecutive_loss_ticks_for_bankruptcy_threshold = 5
    firm.automation_level = 0.0
    firm.last_sales_volume = 1.0 # Fix for the TypeError seen in previous run
    firm.total_debt = 0.0 # Ensure total_debt is float
    firm.bond_obligations = [] # Add bond obligations

    # Ensure decision_engine chain works for _get_total_liabilities
    if not hasattr(firm, 'decision_engine'):
        firm.decision_engine = MagicMock()

    mock_bank = MagicMock()
    mock_bank.get_debt_summary.return_value = {'total_principal': 0.0}

    mock_loan_market = MagicMock()
    mock_loan_market.bank = mock_bank

    firm.decision_engine.loan_market = mock_loan_market

    return firm

@pytest.fixture
def context_mock(firm_mock):
    context = MagicMock(spec=DecisionContext)
    context.firm = firm_mock
    context.current_time = 1
    context.market_data = {}
    context.markets = {
        "food": MagicMock(),
        "labor": MagicMock()
    }
    context.reflux_system = MagicMock()
    context.government = MagicMock()
    return context

def test_rd_logic(firm_mock, context_mock, monkeypatch):
    manager = CorporateManager(MockConfig())
    # Aggressiveness 1.0 -> 20% of Revenue
    vector = FirmActionVector(
        rd_aggressiveness=1.0,
        capital_aggressiveness=0.0,
        dividend_aggressiveness=0.0,
        debt_aggressiveness=0.0,
        hiring_aggressiveness=0.0,
        sales_aggressiveness=0.0
    )

    # Need enough assets to pass safety margin (default 2000)
    firm_mock.assets = 10000.0
    firm_mock.revenue_this_turn = 1000.0
    expected_budget = 1000.0 * 0.2 # 200

    # Force success
    monkeypatch.setattr("random.random", lambda: 0.0)

    initial_quality = firm_mock.base_quality
    initial_prod = firm_mock.productivity_factor

    manager.realize_ceo_actions(firm_mock, context_mock, vector)

    # Verify delegation to finance
    firm_mock.finance.invest_in_rd.assert_called_with(expected_budget)

    assert firm_mock.base_quality == pytest.approx(initial_quality + 0.05)
    assert firm_mock.productivity_factor == pytest.approx(initial_prod * 1.05)

def test_dividend_logic(firm_mock, context_mock):
    manager = CorporateManager(MockConfig())
    vector = FirmActionVector(dividend_aggressiveness=1.0) # Max rate 0.5

    manager.realize_ceo_actions(firm_mock, context_mock, vector)

    assert firm_mock.dividend_rate == 0.5

def test_hiring_logic(firm_mock, context_mock):
    manager = CorporateManager(MockConfig())
    firm_mock.production_target = 100
    # firm.inventory is a dict, so updating it works
    firm_mock.inventory["food"] = 80 # Gap 20
    firm_mock.productivity_factor = 10.0 # Need 2 workers

    vector = FirmActionVector(hiring_aggressiveness=0.5) # Market wage

    orders = manager.realize_ceo_actions(firm_mock, context_mock, vector)

    hiring_orders = [o for o in orders if o.order_type == "BUY" and o.item_id == "labor"]
    assert len(hiring_orders) > 0
    assert hiring_orders[0].price >= 10.0

def test_debt_logic_borrow(firm_mock, context_mock):
    manager = CorporateManager(MockConfig())
    # Assets 1000 (from setup), Debt 0 (assumed default in mock). Leverage 0.
    # Aggressiveness 0.5 -> Target 1.0 Leverage (1000 Debt)
    # Ensure total_assets and total_debt are set if computed properties are used
    # But since it is a mock, we might need to set them if logic depends on them.
    # The original test manually set assets=1000.
    firm_mock.assets = 1000.0
    firm_mock.total_debt = 0.0

    vector = FirmActionVector(debt_aggressiveness=0.5)

    orders = manager.realize_ceo_actions(firm_mock, context_mock, vector)

    loan_reqs = [o for o in orders if o.order_type == "LOAN_REQUEST"]
    assert len(loan_reqs) > 0
    assert loan_reqs[0].quantity > 0

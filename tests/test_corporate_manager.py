
import pytest
from unittest.mock import MagicMock
from simulation.decisions.corporate_manager import CorporateManager
from simulation.dtos import DecisionContext
from simulation.dtos.firm_state_dto import FirmStateDTO
from simulation.schemas import FirmActionVector
from simulation.models import Order
from simulation.ai.enums import Personality

class MockConfig:
    CAPITAL_TO_OUTPUT_RATIO = 2.0
    DIVIDEND_RATE_MIN = 0.1
    DIVIDEND_RATE_MAX = 0.5
    MAX_SELL_QUANTITY = 100
    LABOR_MARKET_MIN_WAGE = 10.0
    GOODS = {"food": {"production_cost": 10.0, "inputs": {}}}
    # Added for automation
    AUTOMATION_COST_PER_PCT = 1000.0
    FIRM_SAFETY_MARGIN = 2000.0
    AUTOMATION_TAX_RATE = 0.05
    SEVERANCE_PAY_WEEKS = 4
    # SEO
    STARTUP_COST = 30000.0
    SEO_TRIGGER_RATIO = 0.5
    SEO_MAX_SELL_RATIO = 0.10
    LABOR_ALPHA = 0.7
    AUTOMATION_LABOR_REDUCTION = 0.5
    DIVIDEND_SUSPENSION_LOSS_TICKS = 3

@pytest.fixture
def firm_state_mock():
    # Construct a DTO directly
    return FirmStateDTO(
        id=100,
        assets=10000.0,
        is_active=True,
        specialization="food",
        inventory={"food": 50},
        needs={},
        current_production=0.0,
        production_target=100.0,
        productivity_factor=1.0,
        employee_count=3,
        employees=[1, 2, 3],
        employee_wages={1: 10.0, 2: 10.0, 3: 10.0},
        profit_history=[10.0, 10.0],
        last_prices={"food": 10.0},
        inventory_quality={"food": 1.0},
        input_inventory={},
        last_revenue=200.0,
        last_sales_volume=1.0,
        revenue_this_turn=200.0,
        expenses_this_tick=100.0,
        consecutive_loss_turns=0,
        total_shares=100.0,
        treasury_shares=0.0,
        dividend_rate=0.1,
        capital_stock=100.0,
        total_debt=0.0,
        personality=Personality.BALANCED,
        base_quality=1.0,
        brand_awareness=0.0,
        perceived_quality=0.0,
        automation_level=0.0
    )

@pytest.fixture
def context_mock(firm_state_mock):
    context = MagicMock(spec=DecisionContext)
    context.firm_state = firm_state_mock
    context.current_time = 1
    context.market_data = {}
    context.markets = {
        "food": MagicMock(),
        "labor": MagicMock(),
        "stock_market": MagicMock() # For SEO
    }
    context.reflux_system = MagicMock()
    context.government = MagicMock()
    return context

def test_rd_logic(firm_state_mock, context_mock):
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

    # Revenue 1000 needed to trigger
    firm_state_mock.revenue_this_turn = 1000.0
    expected_budget = 1000.0 * 0.2 # 200

    guidance = {}
    orders = manager.realize_ceo_actions(firm_state_mock, context_mock, vector, guidance)

    rd_orders = [o for o in orders if o.order_type == "INVEST_RD"]
    assert len(rd_orders) > 0
    assert rd_orders[0].quantity == pytest.approx(expected_budget)

def test_dividend_logic(firm_state_mock, context_mock):
    manager = CorporateManager(MockConfig())
    vector = FirmActionVector(dividend_aggressiveness=1.0) # Max rate 0.5

    guidance = {}
    orders = manager.realize_ceo_actions(firm_state_mock, context_mock, vector, guidance)

    div_orders = [o for o in orders if o.order_type == "SET_DIVIDEND_RATE"]
    assert len(div_orders) > 0
    assert div_orders[0].price == 0.5

def test_hiring_logic(firm_state_mock, context_mock):
    manager = CorporateManager(MockConfig())
    firm_state_mock.production_target = 100
    firm_state_mock.inventory = {"food": 80} # Gap 20
    firm_state_mock.productivity_factor = 10.0 # Need 2 workers
    # Currently 3 employees. 3 > 2. Should Fire 1.

    # Wait, original test expected hiring.
    # Original test setup: firm_mock.productivity_factor = 10.0.
    # Gap 20. Need = 20 / 10 = 2.
    # Employees = 3.
    # So Excess = 1. Firing!

    # Let's adjust mock to force hiring.
    firm_state_mock.employee_count = 1
    firm_state_mock.employees = [1]
    # Reduce capital to avoid Cobb-Douglas suppression of labor demand
    firm_state_mock.capital_stock = 1.0

    vector = FirmActionVector(hiring_aggressiveness=0.5) # Market wage

    guidance = {}
    orders = manager.realize_ceo_actions(firm_state_mock, context_mock, vector, guidance)

    hiring_orders = [o for o in orders if o.order_type == "BUY" and o.item_id == "labor"]
    assert len(hiring_orders) > 0
    assert hiring_orders[0].price >= 10.0

def test_debt_logic_borrow(firm_state_mock, context_mock):
    manager = CorporateManager(MockConfig())
    firm_state_mock.assets = 1000.0
    firm_state_mock.total_debt = 0.0

    vector = FirmActionVector(debt_aggressiveness=0.5)

    guidance = {}
    orders = manager.realize_ceo_actions(firm_state_mock, context_mock, vector, guidance)

    loan_reqs = [o for o in orders if o.order_type == "LOAN_REQUEST"]
    assert len(loan_reqs) > 0
    assert loan_reqs[0].quantity > 0

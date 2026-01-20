
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
    FIRM_MAINTENANCE_FEE = 50.0
    STARTUP_COST = 30000.0
    SEO_TRIGGER_RATIO = 0.5
    SEO_MAX_SELL_RATIO = 0.10
    AUTOMATION_COST_PER_PCT = 1000.0
    FIRM_SAFETY_MARGIN = 2000.0
    AUTOMATION_TAX_RATE = 0.05
    LABOR_ALPHA = 0.7
    AUTOMATION_LABOR_REDUCTION = 0.5
    SEVERANCE_PAY_WEEKS = 4

@pytest.fixture
def firm_mock(golden_firms):
    if not golden_firms:
        pytest.skip("Golden firms fixture is empty or failed to load.")
    firm = golden_firms[0]

    # Setup Finance Mock
    firm.finance = MagicMock()
    firm.finance.revenue_this_turn = 200.0
    firm.finance.last_revenue = 200.0
    firm.finance.last_sales_volume = 1.0
    firm.finance.cash = 10000.0 # Default cash
    firm.finance.invest_in_rd.return_value = True
    firm.finance.invest_in_capex.return_value = True
    firm.finance.invest_in_automation.return_value = True
    firm.finance.get_book_value_per_share.return_value = 10.0
    firm.finance.pay_adhoc_tax.return_value = True

    # Setup HR Mock
    firm.hr = MagicMock()
    firm.hr.employees = []
    firm.hr.employee_wages = {}

    firm.revenue_this_turn = 200.0 # Legacy attribute just in case but tests should use finance
    firm.production_target = 100
    firm.productivity_factor = 1.0
    firm.specialization = "food"
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
    # firm.personality is likely already set in golden fixture
    firm.personality = Personality.BALANCED

    firm.system2_planner = None
    firm.total_debt = 0.0
    firm.bond_obligations = []
    firm.assets = 10000.0 # Default High Assets
    firm.automation_level = 0.0

    if not hasattr(firm, 'decision_engine'):
        firm.decision_engine = MagicMock()

    mock_bank = MagicMock()
    mock_bank.get_debt_summary.return_value = {'total_principal': 0.0}

    mock_loan_market = MagicMock()
    mock_loan_market.bank = mock_bank

    firm.decision_engine.loan_market = mock_loan_market

    # Implement invest side effects if needed, but for unit tests return_value=True is usually enough
    # unless we check side effects on assets.
    def side_effect_invest(amount):
        if firm.assets >= amount:
            firm.assets -= amount
            return True
        return False

    firm.finance.invest_in_rd.side_effect = side_effect_invest
    firm.finance.invest_in_capex.side_effect = side_effect_invest
    firm.finance.invest_in_automation.side_effect = side_effect_invest

    def side_effect_set_dividend(rate):
        firm.dividend_rate = rate
    firm.finance.set_dividend_rate.side_effect = side_effect_set_dividend

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
    vector = FirmActionVector(
        rd_aggressiveness=1.0,
        capital_aggressiveness=0.0,
        dividend_aggressiveness=0.0,
        debt_aggressiveness=0.0,
        hiring_aggressiveness=0.0,
        sales_aggressiveness=0.0
    )

    firm_mock.assets = 10000.0
    firm_mock.finance.cash = 10000.0
    firm_mock.finance.revenue_this_turn = 1000.0 # Set on finance mock
    expected_budget = 1000.0 * 0.2 # 200

    monkeypatch.setattr("random.random", lambda: 0.0)

    initial_quality = firm_mock.base_quality
    initial_prod = firm_mock.productivity_factor

    manager.realize_ceo_actions(firm_mock, context_mock, vector)

    assert firm_mock.assets == 10000.0 - expected_budget
    assert firm_mock.base_quality == pytest.approx(initial_quality + 0.05)
    assert firm_mock.productivity_factor == pytest.approx(initial_prod * 1.05)

    # Verify delegation
    firm_mock.finance.invest_in_rd.assert_called()

def test_dividend_logic(firm_mock, context_mock):
    manager = CorporateManager(MockConfig())
    vector = FirmActionVector(dividend_aggressiveness=1.0)

    manager.realize_ceo_actions(firm_mock, context_mock, vector)

    assert firm_mock.dividend_rate == 0.5
    firm_mock.finance.set_dividend_rate.assert_called_with(0.5)

def test_hiring_logic(firm_mock, context_mock):
    manager = CorporateManager(MockConfig())
    firm_mock.production_target = 100
    firm_mock.inventory["food"] = 80
    firm_mock.productivity_factor = 10.0

    vector = FirmActionVector(hiring_aggressiveness=0.5)

    orders = manager.realize_ceo_actions(firm_mock, context_mock, vector)

    hiring_orders = [o for o in orders if o.order_type == "BUY" and o.item_id == "labor"]
    assert len(hiring_orders) > 0
    assert hiring_orders[0].price >= 10.0

def test_debt_logic_borrow(firm_mock, context_mock):
    manager = CorporateManager(MockConfig())
    firm_mock.assets = 1000.0
    firm_mock.total_debt = 0.0
    firm_mock.finance.revenue_this_turn = 200.0 # needed to avoid error in RD channel which is called first?
    # RD channel checks revenue.

    vector = FirmActionVector(debt_aggressiveness=0.5)

    orders = manager.realize_ceo_actions(firm_mock, context_mock, vector)

    loan_reqs = [o for o in orders if o.order_type == "LOAN_REQUEST"]
    assert len(loan_reqs) > 0
    assert loan_reqs[0].quantity > 0

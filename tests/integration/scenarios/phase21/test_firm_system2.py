import pytest
from unittest.mock import Mock, MagicMock
from simulation.firms import Firm
from simulation.ai.firm_system2_planner import FirmSystem2Planner
from simulation.ai.enums import Personality
import config # Import from root
from tests.utils.factories import create_firm_config_dto, create_firm

@pytest.fixture
def firm_mock():
    # Setup mock decision engine
    decision_engine = Mock()
    decision_engine.loan_market = Mock()

    # Create Firm using Factory
    firm = create_firm(
        id=1,
        assets=10000.0,
        initial_liquidity_need=100.0,
        specialization="basic_food",
        productivity_factor=10.0,
        engine=decision_engine,
        value_orientation="growth",
        config_dto=create_firm_config_dto()
    )
    return firm

def test_system2_planner_guidance_automation_preference(firm_mock):
    """Test that CASH_COW prefers automation when profitable."""
    # Setup cheap automation scenario
    firm_mock.config.automation_cost_per_pct = 100.0
    firm_mock.config.AUTOMATION_COST_PER_PCT = 100.0
    firm_mock.config.AUTOMATION_LABOR_REDUCTION = 0.5
    firm_mock.config.FIRM_MAINTENANCE_FEE = 10.0

    from modules.system.api import DEFAULT_CURRENCY
    firm_mock.hr_state.employee_wages = {1: 1000.0}
    firm_mock.finance_state.revenue_this_turn = {DEFAULT_CURRENCY: 5000.0}
    firm_mock.finance_state.balance = 50000.0

    firm_mock.personality = Personality.CASH_COW
    planner = FirmSystem2Planner(firm_mock, firm_mock.config)

    # Create Mock FirmStateDTO
    firm_state = MagicMock()
    firm_state.finance.revenue_this_turn = 5000.0
    firm_state.finance.balance = 50000.0
    firm_state.finance.total_debt_pennies = 0
    firm_state.finance.average_interest_rate = 0.0
    firm_state.production.automation_level = 0.0
    firm_state.hr.employees_data = {1: {'wage': 1000.0}}
    firm_state.agent_data = {"personality": Personality.CASH_COW}

    guidance = planner.project_future(1, {}, firm_state=firm_state)
    assert guidance["target_automation"] > 0.0

def test_system2_planner_guidance_ma_preference(firm_mock):
    """Test that GROWTH_HACKER prefers M&A when rich."""
    from modules.system.api import DEFAULT_CURRENCY
    firm_mock.finance_state.balance = 1000000.0
    firm_mock.finance_state.revenue_this_turn = {DEFAULT_CURRENCY: 10000.0}
    firm_mock.personality = Personality.GROWTH_HACKER
    planner = FirmSystem2Planner(firm_mock, firm_mock.config)

    # Create Mock FirmStateDTO
    firm_state = MagicMock()
    firm_state.finance.revenue_this_turn = 10000.0
    firm_state.finance.balance = 1000000.0
    firm_state.finance.total_debt_pennies = 0
    firm_state.finance.average_interest_rate = 0.0
    firm_state.production.automation_level = 0.0
    firm_state.hr.employees_data = {}
    firm_state.agent_data = {"personality": Personality.GROWTH_HACKER}

    guidance = planner.project_future(1, {}, firm_state=firm_state)
    assert guidance["expansion_mode"] == "MA"
    assert guidance["rd_intensity"] == 0.2

def test_system2_planner_with_debt(firm_mock):
    """Test that high debt reduces NPV and potentially changes guidance."""
    from modules.system.api import DEFAULT_CURRENCY
    firm_mock.finance_state.balance = 100000.0
    firm_mock.finance_state.revenue_this_turn = {DEFAULT_CURRENCY: 10000.0}
    firm_mock.personality = Personality.BALANCED

    planner = FirmSystem2Planner(firm_mock, firm_mock.config)

    # 1. Zero Debt Scenario
    firm_state_clean = MagicMock()
    firm_state_clean.finance.revenue_this_turn = 10000.0
    firm_state_clean.finance.balance = 100000.0
    firm_state_clean.finance.total_debt_pennies = 0
    firm_state_clean.finance.average_interest_rate = 0.05
    firm_state_clean.production.automation_level = 0.0
    firm_state_clean.hr.employees_data = {}
    firm_state_clean.agent_data = {"personality": Personality.BALANCED}

    guidance_clean = planner.project_future(1, {}, firm_state=firm_state_clean)

    # 2. High Debt Scenario
    firm_state_debt = MagicMock()
    firm_state_debt.finance.revenue_this_turn = 10000.0
    firm_state_debt.finance.balance = 100000.0
    firm_state_debt.finance.total_debt_pennies = 5000000 # 50k debt
    firm_state_debt.finance.average_interest_rate = 0.20 # 20% interest
    firm_state_debt.production.automation_level = 0.0
    firm_state_debt.hr.employees_data = {}
    firm_state_debt.agent_data = {"personality": Personality.BALANCED}

    # Use distinct tick to avoid cache
    guidance_debt = planner.project_future(20, {}, firm_state=firm_state_debt)

    # NPV should be significantly lower
    assert guidance_debt["npv_status_quo"] < guidance_clean["npv_status_quo"]

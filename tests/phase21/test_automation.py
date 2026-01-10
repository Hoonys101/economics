import pytest
from unittest.mock import Mock, MagicMock
from simulation.firms import Firm
from simulation.ai.firm_system2_planner import FirmSystem2Planner
from simulation.ai.enums import Personality
import config # Import from root

@pytest.fixture
def firm_mock():
    # Setup mock decision engine
    decision_engine = Mock()
    decision_engine.loan_market = Mock()

    # Create Firm
    firm = Firm(
        id=1,
        initial_capital=10000.0,
        initial_liquidity_need=100.0,
        specialization="basic_food",
        productivity_factor=10.0,
        decision_engine=decision_engine,
        value_orientation="growth",
        config_module=config
    )
    return firm

def test_firm_automation_init(firm_mock):
    """Test if automation_level initializes correctly."""
    assert firm_mock.automation_level == 0.0
    assert firm_mock.system2_planner is None

def test_production_function_with_automation(firm_mock):
    """Test modified Cobb-Douglas production function."""
    # Setup
    firm_mock.employees = [Mock(labor_skill=1.0)] # 1 Employee
    firm_mock.capital_stock = 100.0
    firm_mock.productivity_factor = 10.0
    firm_mock.config_module.LABOR_ALPHA = 0.5
    firm_mock.config_module.AUTOMATION_LABOR_REDUCTION = 0.5

    # Disable depreciation for precise calc
    firm_mock.config_module.CAPITAL_DEPRECIATION_RATE = 0.0

    # Case 1: Automation 0.0
    # Alpha = 0.5 * (1 - 0) = 0.5
    # Y = 10 * (1^0.5) * (100^0.5) = 10 * 1 * 10 = 100
    firm_mock.automation_level = 0.0
    firm_mock.produce(current_time=1)
    prod_zero = firm_mock.current_production
    assert 99.0 < prod_zero < 101.0

    # Case 2: Automation 1.0
    # Alpha = 0.5 * (1 - 0.5) = 0.25
    # Beta = 0.75
    # Y = 10 * (1^0.25) * (100^0.75) = 10 * 1 * 31.62 = 316.2
    # Output should INCREASE because Capital is High (100) and we shifted weight to Capital.
    firm_mock.automation_level = 1.0
    firm_mock.produce(current_time=2)
    prod_full = firm_mock.current_production

    assert prod_full > prod_zero # Automation helps when Capital is abundant
    assert prod_full > 310.0

def test_system2_planner_guidance(firm_mock):
    """Test System 2 Planner logic."""
    # Override config for this test to make automation cheaper
    firm_mock.config_module.AUTOMATION_COST_PER_PCT = 100.0 # Was 1000.0

    firm_mock.system2_planner = FirmSystem2Planner(firm_mock, firm_mock.config_module)

    # Mock Data
    market_data = {}
    firm_mock.revenue_this_turn = 5000.0
    firm_mock.assets = 300000.0 # Rich firm (Needs to be > 50 * Revenue = 250k)

    # High wages to justify automation
    firm_mock.employee_wages = {1: 1000.0, 2: 1000.0}

    # Test CASH_COW personality
    firm_mock.personality = Personality.CASH_COW
    guidance = firm_mock.system2_planner.project_future(1, market_data)

    # Should favor automation if profitable
    # With lower cost (100.0 * 80 gap = 8000 cost) vs 80k benefit, highly profitable.
    assert guidance["target_automation"] > 0.0

    # Test GROWTH_HACKER
    firm_mock.personality = Personality.GROWTH_HACKER
    guidance = firm_mock.system2_planner.project_future(11, market_data)

    # Expansion mode should be MA if rich
    assert guidance["expansion_mode"] == "MA"
    assert guidance["rd_intensity"] >= 0.2

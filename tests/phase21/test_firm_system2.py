import pytest
from unittest.mock import Mock, MagicMock
from simulation.firms import Firm
from simulation.ai.firm_system2_planner import FirmSystem2Planner
from simulation.ai.enums import Personality
import config  # Import from root


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
        config_module=config,
    )
    return firm


def test_system2_planner_guidance_automation_preference(firm_mock):
    """Test that CASH_COW prefers automation when profitable."""
    # Setup cheap automation scenario
    firm_mock.config_module.AUTOMATION_COST_PER_PCT = 100.0
    firm_mock.employee_wages = {1: 1000.0}
    firm_mock.revenue_this_turn = 5000.0
    firm_mock._assets = 50000.0

    firm_mock.personality = Personality.CASH_COW
    firm_mock.system2_planner = FirmSystem2Planner(firm_mock, config)

    guidance = firm_mock.system2_planner.project_future(1, {})
    assert guidance["target_automation"] > 0.0


def test_system2_planner_guidance_ma_preference(firm_mock):
    """Test that GROWTH_HACKER prefers M&A when rich."""
    firm_mock._assets = 1000000.0
    firm_mock.revenue_this_turn = 10000.0
    firm_mock.personality = Personality.GROWTH_HACKER
    firm_mock.system2_planner = FirmSystem2Planner(firm_mock, config)

    guidance = firm_mock.system2_planner.project_future(1, {})
    assert guidance["expansion_mode"] == "MA"
    assert guidance["rd_intensity"] == 0.2

import pytest
from unittest.mock import MagicMock, patch
from simulation.components.engines.rd_engine import RDEngine
from modules.firm.api import RDInputDTO, FirmSnapshotDTO
from modules.simulation.dtos.api import ProductionStateDTO, HRStateDTO, FinanceStateDTO

@pytest.fixture
def rd_engine():
    return RDEngine()

@pytest.fixture
def firm_snapshot():
    snapshot = MagicMock(spec=FirmSnapshotDTO)

    # Mock Finance
    finance = MagicMock(spec=FinanceStateDTO)
    finance.revenue_this_turn = {"USD": 1000.0}
    snapshot.finance = finance

    # Mock HR (for skill)
    hr = MagicMock(spec=HRStateDTO)
    hr.employees = [1, 2] # Dummy IDs
    hr.employees_data = {
        1: {"skill": 1.0},
        2: {"skill": 1.0}
    } # Avg skill = 1.0
    snapshot.hr = hr

    # Mock Production
    production = MagicMock(spec=ProductionStateDTO)
    snapshot.production = production

    # Mock Config
    config = MagicMock() # spec=FirmConfigDTO not strictly needed unless we access fields
    snapshot.config = config

    return snapshot

@patch('simulation.components.engines.rd_engine.random.random')
def test_research_success(mock_random, rd_engine, firm_snapshot):
    # Set mock_random to return 0.0 (always success if chance > 0)
    mock_random.return_value = 0.0

    input_dto = RDInputDTO(
        firm_snapshot=firm_snapshot,
        investment_amount=100.0,
        current_time=10
    )

    # Calculation:
    # Revenue = 1000.0
    # Denominator = max(200.0, 100.0) = 200.0
    # Base chance = 100.0 / 200.0 = 0.5
    # Avg skill = 1.0
    # Success chance = 0.5 * 1.0 = 0.5
    # Random = 0.0 < 0.5 -> Success

    result = rd_engine.research(input_dto)

    assert result.success
    assert result.actual_cost == 100.0
    assert result.quality_improvement == 0.05
    assert result.productivity_multiplier_change == 1.05

@patch('simulation.components.engines.rd_engine.random.random')
def test_research_failure(mock_random, rd_engine, firm_snapshot):
    # Set mock_random to return 0.9 (failure if chance < 0.9)
    mock_random.return_value = 0.9

    input_dto = RDInputDTO(
        firm_snapshot=firm_snapshot,
        investment_amount=100.0, # Chance 0.5
        current_time=10
    )

    result = rd_engine.research(input_dto)

    assert not result.success
    assert result.actual_cost == 100.0
    assert result.message == "R&D attempt failed."

def test_research_negative_amount(rd_engine, firm_snapshot):
    input_dto = RDInputDTO(firm_snapshot=firm_snapshot, investment_amount=-1.0, current_time=10)
    result = rd_engine.research(input_dto)
    assert not result.success
    assert "positive" in result.message

import pytest
from unittest.mock import MagicMock
from modules.government.tax.service import TaxService
from modules.government.dtos import TaxAssessmentResultDTO, PaymentRequestDTO
from modules.system.api import DEFAULT_CURRENCY
from simulation.factories.golden_agents import create_golden_agent

@pytest.fixture
def mock_config():
    config = MagicMock()
    config.ANNUAL_WEALTH_TAX_RATE = 0.02 # 2%
    config.TICKS_PER_YEAR = 100
    # Threshold in pennies: $1000 -> 100,000 pennies
    config.WEALTH_TAX_THRESHOLD = 100000
    return config

@pytest.fixture
def tax_service(mock_config):
    return TaxService(mock_config)

@pytest.fixture
def golden_agent():
    # Assets will be set in tests
    return create_golden_agent(agent_id=201, assets_pennies=0, is_employed=True)

def test_collect_wealth_tax(tax_service, golden_agent):
    # Setup
    # Net worth 2000. Threshold 1000 (dollars) -> 100000 pennies.
    # Assets 200,000 pennies. Taxable 100,000.
    # Rate per tick = 0.02 / 100 = 0.0002
    # Tax = 100,000 * 0.0002 = 20 pennies.

    golden_agent.assets = {DEFAULT_CURRENCY: 200000}
    agents = [golden_agent]

    # Execution
    result = tax_service.collect_wealth_tax(agents)

    # Verification
    assert isinstance(result, TaxAssessmentResultDTO)
    assert len(result.payment_requests) == 1
    req = result.payment_requests[0]
    assert req.payer == golden_agent
    assert req.amount == 20
    assert req.memo == "wealth_tax"

def test_collect_wealth_tax_below_threshold(tax_service, golden_agent):
    golden_agent.assets = {DEFAULT_CURRENCY: 50000}
    agents = [golden_agent]

    result = tax_service.collect_wealth_tax(agents)

    assert len(result.payment_requests) == 0
    assert result.total_collected == 0 # Penny standard (int)

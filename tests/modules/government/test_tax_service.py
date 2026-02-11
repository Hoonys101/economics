import pytest
from unittest.mock import MagicMock
from modules.government.tax.service import TaxService
from modules.government.dtos import TaxCollectionResultDTO, PaymentRequestDTO
from modules.system.api import DEFAULT_CURRENCY

@pytest.fixture
def mock_config():
    config = MagicMock()
    config.ANNUAL_WEALTH_TAX_RATE = 0.02 # 2%
    config.TICKS_PER_YEAR = 100
    config.WEALTH_TAX_THRESHOLD = 1000.0
    return config

@pytest.fixture
def tax_service(mock_config):
    return TaxService(mock_config)

@pytest.fixture
def mock_agent():
    agent = MagicMock()
    agent.id = 201
    agent.is_active = True
    agent.needs = {}
    agent.is_employed = True
    return agent

def test_collect_wealth_tax(tax_service, mock_agent):
    # Setup
    # Net worth 2000. Threshold 1000 (dollars) -> 100000 pennies.
    # Assets 200,000 pennies. Taxable 100,000.
    # Rate per tick = 0.02 / 100 = 0.0002
    # Tax = 100,000 * 0.0002 = 20 pennies.

    mock_agent.assets = {DEFAULT_CURRENCY: 200000}
    agents = [mock_agent]

    # Execution
    result = tax_service.collect_wealth_tax(agents)

    # Verification
    assert isinstance(result, TaxCollectionResultDTO)
    assert len(result.payment_requests) == 1
    req = result.payment_requests[0]
    assert req.payer == mock_agent
    assert req.amount == 20
    assert req.memo == "wealth_tax"

def test_collect_wealth_tax_below_threshold(tax_service, mock_agent):
    mock_agent.assets = {DEFAULT_CURRENCY: 50000}
    agents = [mock_agent]

    result = tax_service.collect_wealth_tax(agents)

    assert len(result.payment_requests) == 0
    assert result.total_collected == 0.0

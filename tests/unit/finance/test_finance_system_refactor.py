import pytest
from unittest.mock import MagicMock
from modules.finance.system import FinanceSystem
from modules.finance.api import GrantBailoutCommand, BailoutCovenant
from modules.system.api import DEFAULT_CURRENCY

class MockGovernment:
    def __init__(self, assets):
        self.assets = assets
        self.id = "GOVERNMENT"

class MockCentralBank:
    def get_base_rate(self):
        return 0.05

class MockFirm:
    def __init__(self, id):
        self.id = id
        self.total_debt = 0.0
        self.has_bailout_loan = False

@pytest.fixture
def mock_dependencies():
    government = MockGovernment(assets={DEFAULT_CURRENCY: 10000.0})
    central_bank = MockCentralBank()
    bank = MagicMock()
    config_module = MagicMock()
    settlement_system = MagicMock()

    # Config defaults
    def get_config(key, default=None):
        return default
    config_module.get.side_effect = get_config

    return {
        "government": government,
        "central_bank": central_bank,
        "bank": bank,
        "config_module": config_module,
        "settlement_system": settlement_system
    }

def test_request_bailout_loan_success(mock_dependencies):
    deps = mock_dependencies
    system = FinanceSystem(
        government=deps["government"],
        central_bank=deps["central_bank"],
        bank=deps["bank"],
        config_module=deps["config_module"],
        settlement_system=deps["settlement_system"]
    )

    firm = MockFirm(id=1)
    amount = 5000.0

    command = system.request_bailout_loan(firm, amount)

    assert isinstance(command, GrantBailoutCommand)
    assert command.firm_id == 1
    assert command.amount == 5000.0
    assert command.interest_rate > 0.05 # Base rate + penalty
    assert isinstance(command.covenants, BailoutCovenant)
    assert command.covenants.dividends_allowed is False

    # Verify State Purity: Firm state MUST NOT change
    assert firm.total_debt == 0.0
    assert firm.has_bailout_loan is False

def test_request_bailout_loan_insufficient_funds(mock_dependencies):
    deps = mock_dependencies
    # Set low government funds
    deps["government"].assets = {DEFAULT_CURRENCY: 100.0}

    system = FinanceSystem(
        government=deps["government"],
        central_bank=deps["central_bank"],
        bank=deps["bank"],
        config_module=deps["config_module"],
        settlement_system=deps["settlement_system"]
    )

    firm = MockFirm(id=1)
    amount = 5000.0

    command = system.request_bailout_loan(firm, amount)

    assert command is None

def test_grant_bailout_loan_deprecated(mock_dependencies):
    deps = mock_dependencies
    system = FinanceSystem(
        government=deps["government"],
        central_bank=deps["central_bank"],
        bank=deps["bank"],
        config_module=deps["config_module"],
        settlement_system=deps["settlement_system"]
    )

    firm = MockFirm(id=1)
    amount = 5000.0

    # Should return None and log warning (logging not asserted here, but result checked)
    result = system.grant_bailout_loan(firm, amount)
    assert result is None

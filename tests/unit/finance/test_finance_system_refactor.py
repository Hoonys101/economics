import pytest
from unittest.mock import MagicMock
from modules.finance.system import FinanceSystem
from modules.finance.api import GrantBailoutCommand, BailoutCovenant
from modules.system.api import DEFAULT_CURRENCY
from modules.system.constants import ID_GOVERNMENT

class MockGovernment:
    def __init__(self, assets):
        self.assets = assets
        self.id = ID_GOVERNMENT
        self.wallet = MagicMock()
        self.wallet.get_balance.return_value = assets.get(DEFAULT_CURRENCY, 0)

class MockCentralBank:
    def get_base_rate(self):
        return 0.05

class MockFirm:
    def __init__(self, id):
        self.id = id
        self.total_debt = 0.0
        self.has_bailout_loan = False
        self.capital_stock_units = 1000

@pytest.fixture
def mock_dependencies():
    government = MockGovernment(assets={DEFAULT_CURRENCY: 1000000}) # 1M pennies
    central_bank = MockCentralBank()
    bank = MagicMock()
    # Mock bank base rate for ledger initialization
    bank.base_rate = 0.03

    config_module = MagicMock()
    settlement_system = MagicMock()

    # Config defaults
    def get_config(key, default=None):
        return default
    config_module.get.side_effect = get_config

    # Setup Settlement System get_balance side effect
    def get_balance_side_effect(agent_id, currency):
        if agent_id == government.id:
            return government.wallet.get_balance()
        return 0
    settlement_system.get_balance.side_effect = get_balance_side_effect

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
    amount = 500000 # 5000.00 pennies

    command = system.request_bailout_loan(firm, amount)

    assert isinstance(command, GrantBailoutCommand)
    assert command.firm_id == 1
    assert command.amount == 500000.0 # Float check
    assert command.interest_rate > 0.05 # Base rate + penalty
    assert isinstance(command.covenants, BailoutCovenant)
    assert command.covenants.dividends_allowed is False
    assert command.covenants.executive_bonus_allowed is False

    # Verify State Purity: Firm state MUST NOT change
    assert firm.total_debt == 0.0
    assert firm.has_bailout_loan is False

def test_request_bailout_loan_insufficient_funds(mock_dependencies):
    deps = mock_dependencies
    # Set low government funds
    deps["government"].wallet.get_balance.return_value = 10000 # 100.00

    system = FinanceSystem(
        government=deps["government"],
        central_bank=deps["central_bank"],
        bank=deps["bank"],
        config_module=deps["config_module"],
        settlement_system=deps["settlement_system"]
    )

    firm = MockFirm(id=1)
    amount = 500000

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
    amount = 500000

    # Should return tuple (Loan, Txs) - Mocked loan processing returns None in test?
    # grant_bailout_loan calls request_bailout_loan then process_loan_application.
    # process_loan_application logic needs Bank ID in ledger.
    # FinanceSystem uses default mock bank ID.

    # We expect return values, not None, if successful.
    # But since process_loan_application relies on loan_risk_engine etc., and we didn't mock those engines inside FinanceSystem (they are created in init),
    # default engines might fail or return nothing if ledger is empty/default.

    # Actually, process_loan_application creates a loan if approved.
    # Risk engine defaults to approved if no specific risk logic blocks it.
    # But we haven't set up the ledger fully.

    # Let's just check it runs without error and returns something.

    result = system.grant_bailout_loan(firm, amount, current_tick=1)
    # result is (LoanInfoDTO, List[Transaction])
    loan, txs = result

    # So it should return a loan.
    assert loan is not None
    # Use dot notation as strictly typed
    assert loan.principal_pennies == 500000
    assert len(txs) > 0

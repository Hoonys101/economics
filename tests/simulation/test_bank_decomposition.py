import pytest
from unittest.mock import MagicMock
from simulation.bank import Bank
from modules.finance.managers.loan_manager import LoanManager
from modules.finance.managers.deposit_manager import DepositManager
from modules.common.config_manager.api import ConfigManager
from modules.finance.api import IShareholderRegistry, ICreditFrozen, IPortfolioHandler, IFinancialEntity, PortfolioDTO
from modules.simulation.api import IEducated
from modules.system.api import DEFAULT_CURRENCY

class MockShareholderRegistry:
    def register_shares(self, firm_id, agent_id, quantity):
        pass

class MockAgent(ICreditFrozen, IEducated, IPortfolioHandler, IFinancialEntity):
    def __init__(self, id):
        self.id = id
        self._assets = {DEFAULT_CURRENCY: 1000.0}
        self._credit_frozen_until_tick = 0
        self._education_xp = 100.0
        self.portfolio_cleared = False

    @property
    def assets(self) -> float:
        return self._assets[DEFAULT_CURRENCY]

    def deposit(self, amount: float) -> None:
        self._assets[DEFAULT_CURRENCY] += amount

    def withdraw(self, amount: float) -> None:
        self._assets[DEFAULT_CURRENCY] -= amount

    @property
    def credit_frozen_until_tick(self) -> int:
        return self._credit_frozen_until_tick

    @credit_frozen_until_tick.setter
    def credit_frozen_until_tick(self, value: int) -> None:
        self._credit_frozen_until_tick = value

    @property
    def education_xp(self) -> float:
        return self._education_xp

    @education_xp.setter
    def education_xp(self, value: float) -> None:
        self._education_xp = value

    def get_portfolio(self) -> PortfolioDTO:
        return PortfolioDTO(assets=[])

    def receive_portfolio(self, portfolio: PortfolioDTO) -> None:
        pass

    def clear_portfolio(self) -> None:
        self.portfolio_cleared = True

@pytest.fixture
def mock_config():
    cm = MagicMock(spec=ConfigManager)
    cm.get.return_value = 0.1 # Default
    return cm

@pytest.fixture
def bank(mock_config):
    registry = MockShareholderRegistry()
    bank = Bank(id=1, initial_assets=10000.0, config_manager=mock_config, shareholder_registry=registry)
    return bank

def test_bank_initialization(bank):
    assert isinstance(bank.loan_manager, LoanManager)
    assert isinstance(bank.deposit_manager, DepositManager)
    assert bank.assets == 10000.0

def test_grant_loan_delegation(bank):
    # Setup
    bank.loan_manager.assess_and_create_loan = MagicMock(return_value=({'loan_id': 'loan_1'}, 'dep_1'))

    # Execute
    result = bank.grant_loan("101", 1000.0, 0.05, 10)

    # Verify
    assert result is not None
    dto, tx = result
    assert dto['loan_id'] == 'loan_1'
    assert tx.transaction_type == 'credit_creation'
    bank.loan_manager.assess_and_create_loan.assert_called_once()

def test_run_tick_defaults(bank):
    # Setup
    agent = MockAgent(101)
    agents = {101: agent}

    # Mock loan manager to return a default event
    bank.loan_manager.service_loans = MagicMock(return_value=[
        {'type': 'default', 'loan_id': 'loan_1', 'borrower_id': 101, 'amount_defaulted': 500.0}
    ])

    # Execute
    txs = bank.run_tick(agents, current_tick=10)

    # Verify
    assert len(txs) > 0
    # Check for credit destruction
    assert any(tx.transaction_type == 'credit_destruction' for tx in txs)

    # Check Protocol interactions
    # 1. ICreditFrozen: Should be set to > 10
    assert agent.credit_frozen_until_tick > 10

    # 2. IEducated: XP should be reduced
    assert agent.education_xp < 100.0

    # 3. IPortfolioHandler: Cleared
    assert agent.portfolio_cleared

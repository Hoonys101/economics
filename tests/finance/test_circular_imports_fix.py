import pytest
from unittest.mock import MagicMock, Mock, create_autospec
from typing import Optional, List, Dict, Any
from modules.finance.system import FinanceSystem
from modules.finance.api import (
    IConfig, IBank, IGovernmentFinance, IFinancialFirm, IFinancialAgent,
    BondDTO, LoanInfoDTO, GrantBailoutCommand, BailoutCovenant
)
from modules.simulation.api import AgentID
from simulation.dtos.api import GovernmentSensoryDTO
from modules.system.api import DEFAULT_CURRENCY

# --- Protocol Implementations for Mocks ---

class MockConfig:
    def get(self, key: str, default: Any = None) -> Any:
        if key == "economy_params.QE_DEBT_TO_GDP_THRESHOLD":
            return 1.5
        if key == "economy_params.STARTUP_GRACE_PERIOD_TICKS":
            return 24
        if key == "economy_params.ALTMAN_Z_SCORE_THRESHOLD":
            return 1.81
        if key == "economy_params.BAILOUT_PENALTY_PREMIUM":
            return 0.05
        if key == "economy_params.BAILOUT_COVENANT_RATIO":
            return 0.5
        return default

class MockBank(IBank):
    id: AgentID = AgentID(100)
    base_rate: float = 0.03

    def get_balance(self, currency: str = DEFAULT_CURRENCY) -> int:
        return 1000000000

    def get_all_balances(self) -> Dict[str, int]:
        return {DEFAULT_CURRENCY: 1000000000}

    def get_total_deposits(self) -> int:
        return 0

    def _deposit(self, amount: int, currency: str = DEFAULT_CURRENCY) -> None: pass
    def _withdraw(self, amount: int, currency: str = DEFAULT_CURRENCY) -> None: pass

    @property
    def total_wealth(self) -> int: return 1000000000

    def grant_loan(self, *args, **kwargs) -> Optional[LoanInfoDTO]: return None
    def stage_loan(self, *args, **kwargs) -> Optional[LoanInfoDTO]: return None
    def repay_loan(self, *args, **kwargs) -> bool: return True
    def get_customer_balance(self, *args, **kwargs) -> int: return 0
    def get_debt_status(self, *args, **kwargs) -> Any: return None
    def terminate_loan(self, *args, **kwargs) -> Any: return None
    def withdraw_for_customer(self, *args, **kwargs) -> bool: return True

class MockGovernment(IGovernmentFinance):
    id: AgentID = AgentID(1)
    total_debt: int = 500000
    sensory_data: Optional[GovernmentSensoryDTO] = None

    def get_balance(self, currency: str = DEFAULT_CURRENCY) -> int:
        return 1000000

    def get_all_balances(self) -> Dict[str, int]:
        return {DEFAULT_CURRENCY: 1000000}

    def _deposit(self, amount: int, currency: str = DEFAULT_CURRENCY) -> None: pass
    def _withdraw(self, amount: int, currency: str = DEFAULT_CURRENCY) -> None: pass

    @property
    def total_wealth(self) -> int: return 1000000

class MockFirm(IFinancialFirm):
    id: AgentID = AgentID(200)
    age: int = 10
    capital_stock_pennies: int = 100000
    inventory_value_pennies: int = 50000
    monthly_wage_bill_pennies: int = 20000
    total_debt_pennies: int = 10000
    retained_earnings_pennies: int = 30000
    average_profit_pennies: int = 5000

    @property
    def balance_pennies(self) -> int: return 20000

    def deposit(self, amount: int, currency: str = DEFAULT_CURRENCY) -> None: pass
    def withdraw(self, amount: int, currency: str = DEFAULT_CURRENCY) -> None: pass

def test_finance_system_instantiation_and_protocols():
    """
    Test that FinanceSystem can be instantiated with protocol-compliant mocks
    and that strict typing checks (if any) pass.
    """
    config = MockConfig()
    bank = MockBank()
    gov = MockGovernment()
    central_bank = Mock() # CentralBank protocol not strictly enforced yet in system.py
    settlement = Mock()

    # Verify protocols
    assert isinstance(config, IConfig)
    assert isinstance(bank, IBank)
    assert isinstance(gov, IGovernmentFinance)

    fs = FinanceSystem(gov, central_bank, bank, config, settlement)

    assert fs.government == gov
    assert fs.bank == bank
    assert fs.config_module == config

    # Test ledger initialization used bank.base_rate
    assert fs.ledger.banks[bank.id].base_rate == 0.03

def test_issue_treasury_bonds_protocol_usage():
    """
    Test issue_treasury_bonds uses protocols for config and government sensory data.
    """
    config = MockConfig()
    bank = MockBank()
    gov = MockGovernment()

    # Setup sensory data
    sensory = GovernmentSensoryDTO(
        tick=10, inflation_sma=0.02, unemployment_sma=0.05, gdp_growth_sma=0.03,
        wage_sma=100.0, approval_sma=0.6, current_gdp=2.0
    )
    gov.sensory_data = sensory

    central_bank = Mock()
    central_bank.id = AgentID(999)
    settlement = Mock()
    settlement.transfer.return_value = True
    settlement.get_balance.return_value = 1000000

    fs = FinanceSystem(gov, central_bank, bank, config, settlement)

    # Execute
    bonds, txs = fs.issue_treasury_bonds(10000, 100)

    assert len(bonds) == 1
    assert bonds[0].face_value == 10000
    # Yield rate = base_rate (0.03) + 0.01 = 0.04
    assert bonds[0].yield_rate == 0.04

    # With low GDP, ratio is high -> QE
    # current_gdp = 2.0. total_debt = 500000. ratio >> 1.5.

    settlement.transfer.assert_called()
    call_args = settlement.transfer.call_args
    assert call_args[0][0] == central_bank # buyer

    # Case 2: High GDP, Bank buys
    gov.sensory_data.current_gdp = 1000000.0

    bonds, txs = fs.issue_treasury_bonds(10000, 101)

    # Now ratio = 0.5 < 1.5. Buyer should be Bank.
    call_args = settlement.transfer.call_args
    assert call_args[0][0] == bank # buyer

def test_evaluate_solvency_protocol_usage():
    config = MockConfig()
    bank = MockBank()
    gov = MockGovernment()
    central_bank = Mock()
    settlement = Mock()

    fs = FinanceSystem(gov, central_bank, bank, config, settlement)

    firm = MockFirm()
    assert isinstance(firm, IFinancialFirm)

    # Test solvency
    # Age = 10 < 24 (Startup grace period)
    # required runway = wage * 3 = 20000 * 3 = 60000
    # balance = 20000
    # 20000 < 60000 -> False

    solvent = fs.evaluate_solvency(firm, 10)
    assert solvent is False

    # Test established firm
    firm.age = 30
    # Z-Score calc...
    # Just verify it runs without AttributeError
    solvent = fs.evaluate_solvency(firm, 30)
    assert isinstance(solvent, bool)

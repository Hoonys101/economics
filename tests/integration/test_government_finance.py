import pytest
from unittest.mock import MagicMock
from simulation.agents.government import Government
from simulation.finance.api import ISettlementSystem
from modules.finance.api import IFinancialAgent
from typing import Optional, Dict, Any, List
from modules.system.api import DEFAULT_CURRENCY, CurrencyCode
from simulation.models import Transaction

class MockRefluxSystem:
    def __init__(self, id: int, initial_assets: float = 0.0):
        self.id = id
        self._assets = initial_assets

    @property
    def total_wealth(self) -> int:
        return int(self._assets)

    def _add_assets(self, amount: float) -> None:
        self._assets += amount

    def _sub_assets(self, amount: float) -> None:
        self._assets -= amount

    def _deposit(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self._add_assets(amount)

    def _withdraw(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self._sub_assets(amount)

    def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        return int(self._assets)

    def get_all_balances(self) -> Dict[CurrencyCode, int]:
        return {DEFAULT_CURRENCY: int(self._assets)}

class MockSettlementSystem(ISettlementSystem):
    def transfer(
        self,
        debit_agent: IFinancialAgent,
        credit_agent: IFinancialAgent,
        amount: int,
        memo: str,
        debit_context: Optional[Dict[str, Any]] = None,
        credit_context: Optional[Dict[str, Any]] = None,
        tick: int = 0,
        currency: CurrencyCode = DEFAULT_CURRENCY
    ) -> bool:
        credit_agent._deposit(amount)
        # We don't debit to simulate "bug" in original test context,
        # but here we just need a dummy implementation.
        return True

    def audit_total_m2(self, expected_total: Optional[int] = None) -> bool:
        return True

class MockConfig:
    INFRASTRUCTURE_INVESTMENT_COST = 1000.0
    TICKS_PER_YEAR = 100
    GOVERNMENT_POLICY_MODE = "TAYLOR_RULE"
    INCOME_TAX_RATE = 0.1
    CORPORATE_TAX_RATE = 0.2
    TAX_MODE = "PROGRESSIVE" # Needed for TaxAgency
    INFRASTRUCTURE_TFP_BOOST = 0.1
    HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 1.0

def test_invest_infrastructure_generates_transaction():
    # 1. Setup
    config = MockConfig()
    government = Government(id=1, initial_assets=10000.0, config_module=config)
    # Mock FinanceSystem to avoid AttributeError when accessing issue_treasury_bonds_synchronous
    government.finance_system = MagicMock()
    # It needs to return false for issue_treasury_bonds_synchronous check unless we mock it
    # logic: if hasattr(self.government.finance_system, 'issue_treasury_bonds_synchronous'):
    # So we don't need to do anything if it's a MagicMock, it will return a Mock object for that attr.
    # But then success check: if success: ...
    # So we need it to return True.
    # TD-177: Updated to return tuple (success, transactions)
    government.finance_system.issue_treasury_bonds_synchronous.return_value = (True, [])

    # Households
    mock_household = MagicMock()
    mock_household.id = 101
    mock_household.is_active = True

    # 2. Record State Before
    assets_gov_before = government.total_wealth

    # 3. Execute
    txs = government.invest_infrastructure(current_tick=1, households=[mock_household])

    # 4. Assert
    # Should return a list of transactions
    assert isinstance(txs, list)
    assert len(txs) == 1

    tx = txs[0]
    assert isinstance(tx, Transaction)
    assert tx.transaction_type == "infrastructure_spending"
    assert tx.buyer_id == government.id
    assert tx.seller_id == mock_household.id
    assert tx.price == config.INFRASTRUCTURE_INVESTMENT_COST
    assert tx.metadata.get("triggers_effect") == "GOVERNMENT_INFRA_UPGRADE"
    assert tx.metadata.get("is_public_works") == True

    # 5. Assert No Immediate State Change (Sacred Sequence)
    # The transaction object is created, but not executed yet.
    # HOWEVER, finance system logic in InfrastructureManager might have run.
    # If using synchronous financing, it might have updated state?
    # No, invest_infrastructure just returns transactions for SPENDING.
    # Financing part:
    # `success = self.government.finance_system.issue_treasury_bonds_synchronous(...)`
    # We mocked it.

    # Assert assets didn't change (assuming transaction not processed)
    assert government.total_wealth == assets_gov_before

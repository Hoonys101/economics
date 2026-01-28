import pytest
from unittest.mock import MagicMock
from simulation.agents.government import Government
from simulation.finance.api import IFinancialEntity, ISettlementSystem
from typing import Optional, Dict, Any, List
from simulation.models import Transaction

class MockRefluxSystem:
    def __init__(self, id: int, initial_assets: float = 0.0):
        self.id = id
        self._assets = initial_assets

    @property
    def assets(self) -> float:
        return self._assets

    def _add_assets(self, amount: float) -> None:
        self._assets += amount

    def _sub_assets(self, amount: float) -> None:
        self._assets -= amount

    def deposit(self, amount: float) -> None:
        self._add_assets(amount)

class MockSettlementSystem(ISettlementSystem):
    def transfer(
        self,
        debit_agent: IFinancialEntity,
        credit_agent: IFinancialEntity,
        amount: float,
        memo: str,
        debit_context: Optional[Dict[str, Any]] = None,
        credit_context: Optional[Dict[str, Any]] = None
    ) -> bool:
        credit_agent._add_assets(amount)
        # We don't debit to simulate "bug" in original test context,
        # but here we just need a dummy implementation.
        return True

class MockConfig:
    INFRASTRUCTURE_INVESTMENT_COST = 1000.0
    TICKS_PER_YEAR = 100
    GOVERNMENT_POLICY_MODE = "TAYLOR_RULE"
    INCOME_TAX_RATE = 0.1
    CORPORATE_TAX_RATE = 0.2
    TAX_MODE = "PROGRESSIVE" # Needed for TaxAgency
    INFRASTRUCTURE_TFP_BOOST = 0.1

def test_invest_infrastructure_generates_transaction():
    # 1. Setup
    config = MockConfig()
    government = Government(id=1, initial_assets=10000.0, config_module=config)
    reflux = MockRefluxSystem(id=999, initial_assets=0.0)

    # 2. Record State Before
    assets_gov_before = government.assets
    assets_reflux_before = reflux.assets

    # 3. Execute
    txs = government.invest_infrastructure(current_tick=1, reflux_system=reflux)

    # 4. Assert
    # Should return a list of transactions
    assert isinstance(txs, list)
    assert len(txs) == 1

    tx = txs[0]
    assert isinstance(tx, Transaction)
    assert tx.transaction_type == "infrastructure_spending"
    assert tx.buyer_id == government.id
    assert tx.seller_id == reflux.id
    assert tx.price == config.INFRASTRUCTURE_INVESTMENT_COST
    assert tx.metadata.get("triggers_effect") == "GLOBAL_TFP_BOOST"

    # 5. Assert No Immediate State Change (Sacred Sequence)
    assert government.assets == assets_gov_before
    assert reflux.assets == assets_reflux_before

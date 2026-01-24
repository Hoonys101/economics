import pytest
from unittest.mock import MagicMock
from simulation.agents.government import Government
from simulation.finance.api import IFinancialEntity, ISettlementSystem
from typing import Optional, Dict, Any, List

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
        # Simulate the bug: Only credit the receiver, do NOT debit the sender.
        # This forces the caller to handle the debit if they want to ensure zero-sum
        # in the presence of this "untrusted" system.
        credit_agent._add_assets(amount)
        return True

class MockConfig:
    INFRASTRUCTURE_INVESTMENT_COST = 1000.0
    TICKS_PER_YEAR = 100
    GOVERNMENT_POLICY_MODE = "TAYLOR_RULE"
    INCOME_TAX_RATE = 0.1
    CORPORATE_TAX_RATE = 0.2
    TAX_MODE = "PROGRESSIVE" # Needed for TaxAgency

def test_invest_infrastructure_is_zero_sum():
    # 1. Setup
    config = MockConfig()
    government = Government(id=1, initial_assets=10000.0, config_module=config)
    reflux = MockRefluxSystem(id=999, initial_assets=0.0)

    settlement_system = MockSettlementSystem()
    government.settlement_system = settlement_system

    # 2. Record State Before
    assets_gov_before = government.assets
    assets_reflux_before = reflux.assets
    total_before = assets_gov_before + assets_reflux_before

    print(f"Before: Gov={assets_gov_before}, Reflux={assets_reflux_before}, Total={total_before}")

    # 3. Execute
    success, txs = government.invest_infrastructure(current_tick=1, reflux_system=reflux)

    assert success is True

    # 4. Record State After
    assets_gov_after = government.assets
    assets_reflux_after = reflux.assets
    total_after = assets_gov_after + assets_reflux_after

    print(f"After: Gov={assets_gov_after}, Reflux={assets_reflux_after}, Total={total_after}")

    # 5. Assert Zero-Sum
    # With the "buggy" MockSettlementSystem, Reflux gains 1000, Gov loses nothing.
    # Total increases by 1000.
    # This assertion is expected to FAIL until the fix is implemented.
    assert total_after == total_before, \
        f"Zero-Sum Violation! Delta: {total_after - total_before}. Gov Delta: {assets_gov_after - assets_gov_before}, Reflux Delta: {assets_reflux_after - assets_reflux_before}"

    # Also check specific expectations
    assert assets_reflux_after == assets_reflux_before + config.INFRASTRUCTURE_INVESTMENT_COST
    assert assets_gov_after == assets_gov_before - config.INFRASTRUCTURE_INVESTMENT_COST

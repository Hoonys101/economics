import pytest
from unittest.mock import MagicMock
from modules.finance.system import FinanceSystem
from modules.system.api import DEFAULT_CURRENCY

def test_bond_issuance_checks_liquidity():
    """
    Regression Test for TD-FORENSIC-004.
    Verifies that bond issuance logic skips if bank lacks reserves.
    """
    # 1. Setup Mock Environment
    gov = MagicMock()
    gov.id = 1
    cb = MagicMock()
    cb.id = 3
    bank = MagicMock()
    bank.id = 2
    bank.base_rate = 0.05
    
    config = MagicMock()
    config.get.side_effect = lambda key, default: default
    
    # Mock sensory_data for gov to avoid AttributeError
    gov.sensory_data = MagicMock()
    gov.sensory_data.current_gdp = 100.0
    
    settlement = MagicMock()
    
    # FinanceSystem uses bank_registry internally
    finance_system = FinanceSystem(
        government=gov,
        central_bank=cb,
        bank=bank,
        config_module=config,
        settlement_system=settlement
    )
    
    # 2. Setup Poor Bank in Registry
    bank_state = finance_system.bank_registry.get_bank(bank.id)
    # Ensure reserves is a Mock that behaves like a dict for .get()
    bank_state.reserves = MagicMock()
    bank_state.reserves.get.side_effect = lambda k, d=0: 1000 if k == DEFAULT_CURRENCY else d
    # Also support direct access for other potential checks
    bank_state.reserves.__getitem__.side_effect = lambda k: 1000 if k == DEFAULT_CURRENCY else 0
    
    # 3. Attempt Large Issuance (50M) via Commercial Bank (Buyer)
    # The default behavior in system.py:350 sets buyer_agent = self.bank if QE not triggered
    
    # Force self.government.total_debt and gdp to keep QE off
    gov.total_debt = 1.0
    gov.sensory_data.current_gdp = 100.0 # Debt/GDP = 0.01 < 1.5
    
    bonds, txs = finance_system.issue_treasury_bonds(amount=50000000, current_tick=1)
    
    # 4. Assert
    # Should be empty because reserves (1000) < amount (50M)
    assert len(bonds) == 0, "Bond issuance should be skipped if bank reserves are insufficient"
    assert len(txs) == 0

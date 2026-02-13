import pytest
from unittest.mock import MagicMock
from simulation.systems.settlement_system import SettlementSystem
from modules.finance.api import IFinancialAgent, IBank
from modules.system.constants import ID_CENTRAL_BANK

class MockAgent:
    def __init__(self, id, balance):
        self.id = id
        self._balance = balance
    def get_balance(self, currency):
        return self._balance
    def get_assets_by_currency(self):
        return {"USD": self._balance}

class MockBank:
    def __init__(self, id, balance, deposits):
        self.id = id
        self._balance = balance
        self._total_deposits = deposits
        self.__class__.__name__ = "Bank" # Simulate legacy check
    def get_balance(self, currency):
        return self._balance
    def get_assets_by_currency(self):
        return {"USD": self._balance}
    def get_total_deposits(self):
        return self._total_deposits

def test_audit_total_m2_logic():
    ss = SettlementSystem()
    ss.agent_registry = MagicMock()
    ss.settlement_accounts = {}

    # 1. Standard Agent (Household)
    hh = MockAgent(1, 100)

    # 2. Central Bank (Should be Excluded)
    cb = MockAgent(ID_CENTRAL_BANK, 999999)

    # 3. Bank (Reserves = 50, Deposits = 200)
    # Total Cash = HH(100) + Bank(50) = 150.
    # Bank Reserves = 50.
    # Total Deposits = 200.
    # M2 = (150 - 50) + 200 = 300.
    bank = MockBank(2, 50, 200)

    ss.agent_registry.get_all_financial_agents.return_value = [hh, cb, bank]

    # Run audit (mock logger to capture output if needed)
    ss.logger = MagicMock()

    # Verify M2 calculation
    # Since audit_total_m2 returns bool based on expectation, we pass expectation.
    result = ss.audit_total_m2(expected_total=300)

    if not result:
        # Debug why it failed
        args = ss.logger.critical.call_args
        if args:
            print(f"Audit Failed Log: {args}")

    assert result
    ss.logger.info.assert_called_with("AUDIT_PASS | M2 Verified: 300")

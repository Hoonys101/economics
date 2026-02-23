import pytest
from unittest.mock import MagicMock, PropertyMock
from simulation.systems.settlement_system import SettlementSystem
from modules.finance.api import IFinancialAgent, IBank, IFinancialEntity
from modules.system.constants import ID_CENTRAL_BANK
from modules.system.api import DEFAULT_CURRENCY

def test_audit_total_m2_logic():
    ss = SettlementSystem()
    ss.agent_registry = MagicMock()
    ss.settlement_accounts = {}

    # 1. Standard Agent (Household) -> IFinancialAgent (to pass isinstance check)
    hh = MagicMock(spec=IFinancialAgent)
    hh.id = 1
    hh.get_balance.return_value = 100
    type(hh).balance_pennies = PropertyMock(return_value=100)

    # 2. Central Bank (Should be Excluded) -> IFinancialEntity
    cb = MagicMock(spec=IFinancialEntity)
    cb.id = ID_CENTRAL_BANK
    type(cb).balance_pennies = PropertyMock(return_value=999999)

    # 3. Bank (Reserves = 50, Deposits = 200) -> IBank (inherits IFinancialAgent)
    # Total Cash = HH(100) + Bank(50) = 150.
    # Bank Reserves = 50.
    # Total Deposits = 200.
    # M2 = (150 - 50) + 200 = 300.
    bank = MagicMock(spec=IBank)
    bank.id = 2
    # IBank uses get_balance method
    bank.get_balance.return_value = 50
    type(bank).balance_pennies = PropertyMock(return_value=50)
    bank.get_total_deposits.return_value = 200

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
        else:
            print(f"All logs: {ss.logger.mock_calls}")

    assert result
    # Expected: Cash 150, Liab: 0
    ss.logger.info.assert_called_with("AUDIT_PASS | M2 Verified: 300 (Cash: 150, Liab: 0)")

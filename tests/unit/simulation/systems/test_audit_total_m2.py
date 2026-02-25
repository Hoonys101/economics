import pytest
from unittest.mock import MagicMock, PropertyMock
from simulation.systems.settlement_system import SettlementSystem
from modules.system.constants import ID_CENTRAL_BANK
from modules.system.api import DEFAULT_CURRENCY
from simulation.core_agents import Household
from simulation.agents.central_bank import CentralBank
from simulation.bank import Bank

def test_audit_total_m2_logic():
    ss = SettlementSystem()
    ss.agent_registry = MagicMock()
    ss.settlement_accounts = {}

    # 1. Standard Agent (Household)
    hh = MagicMock(spec=Household)
    hh.id = 101  # Use ID > 100 to avoid collision with System Agents (ID_GOVERNMENT=1)
    # Household implements IFinancialEntity via protocol/duck typing, ensure property exists
    type(hh).balance_pennies = PropertyMock(return_value=100)
    # Fallback for instance check failure
    hh.get_assets_by_currency.return_value = {DEFAULT_CURRENCY: 100}

    # Ensure get_balance returns integer if called (mock doesn't default to int)
    hh.get_balance.return_value = 100

    # 2. Central Bank (Should be Excluded)
    cb = MagicMock(spec=CentralBank)
    cb.id = ID_CENTRAL_BANK
    type(cb).balance_pennies = PropertyMock(return_value=999999)
    cb.get_assets_by_currency.return_value = {DEFAULT_CURRENCY: 999999}
    cb.get_balance.return_value = 999999

    # 3. Bank (Reserves = 50, Deposits = 200)
    # Total Cash = HH(100) + Bank(50) = 150.
    # Bank Reserves = 50.
    # Total Deposits = 200.
    # New M2 Definition: Sum of Public Balances (Household + Firm).
    # Bank Reserves (M0) and Deposits (Liabilities) are NOT summed.
    # M2 = HH(100).
    bank = MagicMock(spec=Bank)
    bank.id = 2 # Bank ID
    # Bank uses get_balance method (or balance_pennies depending on implementation)
    # SettlementSystem prefers balance_pennies for IFinancialEntity
    type(bank).balance_pennies = PropertyMock(return_value=50)
    bank.get_balance.return_value = 50
    bank.get_assets_by_currency.return_value = {DEFAULT_CURRENCY: 50}
    bank.get_total_deposits.return_value = 200

    ss.agent_registry.get_all_financial_agents.return_value = [hh, cb, bank]

    # Run audit (mock logger to capture output if needed)
    ss.logger = MagicMock()

    # Verify M2 calculation
    # Since audit_total_m2 returns bool based on expectation, we pass expectation.
    result = ss.audit_total_m2(expected_total=100)

    if not result:
        # Debug why it failed
        args = ss.logger.critical.call_args
        if args:
            print(f"Audit Failed Log: {args}")
        else:
            print(f"All logs: {ss.logger.mock_calls}")

    assert result
    # Expected: M2 = 100.
    ss.logger.info.assert_called_with("AUDIT_PASS | M2 Verified: 100 (Delta: 0)", extra={'tag': 'MONEY_SUPPLY_CHECK'})

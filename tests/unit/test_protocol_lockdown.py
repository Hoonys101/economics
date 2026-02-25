import pytest
from typing import Protocol, runtime_checkable
from modules.finance.api import IFinancialEntity, ISettlementSystem, IBankService
from modules.finance.transaction.api import ITransactionExecutor, ITransactionValidator
from modules.system.api import DEFAULT_CURRENCY

class MockFinancialEntity:
    """Correct implementation of IFinancialEntity"""
    id = 1 # Added id
    @property
    def balance_pennies(self) -> int:
        return 100

    def deposit(self, amount_pennies: int, currency: str = "USD") -> None:
        pass

    def withdraw(self, amount_pennies: int, currency: str = "USD") -> None:
        pass

class IncompleteFinancialEntity:
    """Missing methods"""
    @property
    def balance_pennies(self) -> int:
        return 100

def test_financial_entity_protocol_compliance():
    mock = MockFinancialEntity()
    assert isinstance(mock, IFinancialEntity), "MockFinancialEntity should satisfy IFinancialEntity protocol"

    incomplete = IncompleteFinancialEntity()
    assert not isinstance(incomplete, IFinancialEntity), "IncompleteFinancialEntity should NOT satisfy IFinancialEntity protocol"

class MockSettlementSystem:
    def transfer(self, debit_agent, credit_agent, amount, memo, debit_context=None, credit_context=None, tick=0, currency="USD"):
        return None

    def execute_swap(self, match):
        return None

    def get_balance(self, agent_id, currency="USD"):
        return 100

    def audit_total_m2(self, expected_total=None): # Added missing method
        return True

    def get_total_m2_pennies(self, currency=DEFAULT_CURRENCY) -> int: return 0
    def get_total_circulating_cash(self, currency=DEFAULT_CURRENCY) -> int: return 0
    def set_monetary_ledger(self, ledger): pass

    def get_account_holders(self, bank_id):
        return []
    def get_agent_banks(self, agent_id):
        return []
    def register_account(self, bank_id, agent_id):
        pass
    def deregister_account(self, bank_id, agent_id):
        pass
    def remove_agent_from_all_accounts(self, agent_id):
        pass

def test_settlement_system_protocol_compliance():
    mock = MockSettlementSystem()
    assert isinstance(mock, ISettlementSystem), "MockSettlementSystem should satisfy ISettlementSystem protocol"

class MockTransactionExecutor:
    def execute(self, transaction):
        pass

def test_transaction_executor_protocol_compliance():
    mock = MockTransactionExecutor()
    assert isinstance(mock, ITransactionExecutor), "MockTransactionExecutor should satisfy ITransactionExecutor protocol"

class MockBankService:
    def get_interest_rate(self) -> float: return 0.05
    def grant_loan(self, borrower_id, amount, interest_rate, due_tick): return None
    def stage_loan(self, borrower_id, amount, interest_rate, due_tick, borrower_profile): return None
    def repay_loan(self, loan_id, amount): return True

def test_bank_service_protocol_compliance():
    mock = MockBankService()
    assert isinstance(mock, IBankService), "MockBankService should satisfy IBankService protocol"

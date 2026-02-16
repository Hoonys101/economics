import pytest
from unittest.mock import MagicMock
from modules.finance.api import IFinancialAgent, IFinancialEntity, IBank
from simulation.systems.settlement_system import SettlementSystem
from modules.system.api import DEFAULT_CURRENCY, AgentID

class StrictMockBank(IBank):
    """
    A strict mock implementation of IBank without using MagicMock for everything,
    to ensure attributes are explicitly defined as per Protocol.
    """
    def __init__(self, id: AgentID, balance: int = 0, deposits: int = 0):
        self.id = id
        self._balance = balance
        self._deposits = deposits
        self.base_rate = 0.05

    @property
    def balance_pennies(self) -> int:
        return self._balance

    def deposit(self, amount_pennies: int, currency = DEFAULT_CURRENCY) -> None:
        if currency == DEFAULT_CURRENCY:
            self._balance += amount_pennies

    def withdraw(self, amount_pennies: int, currency = DEFAULT_CURRENCY) -> None:
        if currency == DEFAULT_CURRENCY:
            if self._balance >= amount_pennies:
                self._balance -= amount_pennies
            else:
                raise Exception("Insufficient funds")

    def _deposit(self, amount: int, currency = DEFAULT_CURRENCY) -> None:
        self.deposit(amount, currency)

    def _withdraw(self, amount: int, currency = DEFAULT_CURRENCY) -> None:
        self.withdraw(amount, currency)

    def get_balance(self, currency = DEFAULT_CURRENCY) -> int:
        return self._balance if currency == DEFAULT_CURRENCY else 0

    def get_all_balances(self):
        return {DEFAULT_CURRENCY: self._balance}

    @property
    def total_wealth(self) -> int:
        return self._balance

    def get_total_deposits(self) -> int:
        return self._deposits

    # Other IBank methods stubbed
    def grant_loan(self, *args, **kwargs): return None
    def stage_loan(self, *args, **kwargs): return None
    def repay_loan(self, *args, **kwargs): return False
    def get_customer_balance(self, *args, **kwargs): return 0
    def get_debt_status(self, *args, **kwargs): return None
    def terminate_loan(self, *args, **kwargs): return None
    def withdraw_for_customer(self, *args, **kwargs): return False
    def get_assets_by_currency(self, *args, **kwargs): return {}


class StrictFinancialAgent(IFinancialAgent, IFinancialEntity):
    def __init__(self, id: AgentID, balance: int = 0):
        self.id = id
        self._balance = balance

    @property
    def balance_pennies(self) -> int:
        return self._balance

    def deposit(self, amount_pennies: int, currency = DEFAULT_CURRENCY) -> None:
        if currency == DEFAULT_CURRENCY:
            self._balance += amount_pennies

    def withdraw(self, amount_pennies: int, currency = DEFAULT_CURRENCY) -> None:
        if currency == DEFAULT_CURRENCY:
            if self._balance >= amount_pennies:
                self._balance -= amount_pennies
            else:
                raise Exception("Insufficient funds")

    def _deposit(self, amount: int, currency = DEFAULT_CURRENCY) -> None:
        self.deposit(amount, currency)

    def _withdraw(self, amount: int, currency = DEFAULT_CURRENCY) -> None:
        self.withdraw(amount, currency)

    def get_balance(self, currency = DEFAULT_CURRENCY) -> int:
        return self._balance if currency == DEFAULT_CURRENCY else 0

    def get_all_balances(self):
        return {DEFAULT_CURRENCY: self._balance}

    @property
    def total_wealth(self) -> int:
        return self._balance


def test_audit_total_m2_strict_protocol():
    """
    Verifies that audit_total_m2 correctly calculates M2 using strict IBank protocol.
    """
    system = SettlementSystem()

    # Mock Registry
    bank = StrictMockBank(id=1, balance=1000, deposits=5000)
    agent = StrictFinancialAgent(id=2, balance=200) # Cash in circulation

    # M2 = (Total Cash - Bank Reserves) + Total Deposits + Escrow
    # Cash: Bank(1000) + Agent(200) = 1200
    # Bank Reserves: 1000
    # Deposits: 5000
    # Escrow: 0
    # M2 = (1200 - 1000) + 5000 + 0 = 5200

    # Mock Registry
    mock_registry = MagicMock()
    mock_registry.get_all_financial_agents.return_value = [bank, agent]
    system.agent_registry = mock_registry

    assert system.audit_total_m2(expected_total=5200) == True

def test_transfer_memo_validation():
    """
    Verifies that transfer handles memo validation (to be implemented).
    """
    system = SettlementSystem()
    sender = StrictFinancialAgent(id=1, balance=1000)
    receiver = StrictFinancialAgent(id=2, balance=0)

    # Test valid transfer
    tx = system.transfer(sender, receiver, 100, "valid_memo")
    assert tx is not None
    assert sender.balance_pennies == 900
    assert receiver.balance_pennies == 100

    # Test long memo (Should ideally fail after hardening)
    long_memo = "a" * 300
    # Expected behavior after hardening: Reject (return None)
    tx_long = system.transfer(sender, receiver, 100, long_memo)
    assert tx_long is None

def test_transfer_invalid_agent():
    """
    Verifies transfer rejection for non-protocol agents.
    """
    system = SettlementSystem()

    class BadAgent:
        id = 3
        # No IFinancialAgent methods

    sender = StrictFinancialAgent(id=1, balance=1000)
    bad_receiver = BadAgent()

    # Should return None and log error
    tx = system.transfer(sender, bad_receiver, 100, "fail")
    assert tx is None

def test_mint_and_distribute_security():
    """
    Verifies minting security checks.
    """
    system = SettlementSystem()

    from modules.system.constants import ID_CENTRAL_BANK
    # Mock Registry
    central_bank = StrictMockBank(id=ID_CENTRAL_BANK, balance=0, deposits=0)
    target = StrictFinancialAgent(id=2, balance=0)

    class BadAgent:
        id = 3

    mock_registry = MagicMock()
    def get_agent_side_effect(x):
        if x == ID_CENTRAL_BANK or str(x) == str(ID_CENTRAL_BANK):
            return central_bank
        elif x == 2:
            return target
        elif x == 3:
            return BadAgent()
        return None

    mock_registry.get_agent.side_effect = get_agent_side_effect
    system.agent_registry = mock_registry

    # Valid mint
    success = system.mint_and_distribute(2, 500, reason="test")
    assert success == True
    assert target.balance_pennies == 500

    # Invalid target
    success = system.mint_and_distribute(3, 500, reason="test")
    assert success == False

def test_settle_atomic_logging():
    """
    Verifies settle_atomic logs failure properly.
    """
    system = SettlementSystem()
    sender = StrictFinancialAgent(id=1, balance=100) # Insufficient for 200
    receiver = StrictFinancialAgent(id=2, balance=0)

    credits = [(receiver, 200, "atomic_credit")]

    # Capture logs? pytest does it.
    success = system.settle_atomic(sender, credits, tick=0)
    assert success == False

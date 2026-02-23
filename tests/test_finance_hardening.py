import pytest
from unittest.mock import Mock, MagicMock
from modules.finance.api import IFinancialEntity, FloatIncursionError, ZeroSumViolationError, IFinancialAgent
from simulation.models import Transaction
from simulation.systems.settlement_system import SettlementSystem
from simulation.bank import Bank
from modules.simulation.api import AgentID

# --- Mocks ---

class MockFinancialAgent:
    def __init__(self, id: int, balance: int = 0):
        self.id = AgentID(id)
        self._balance = balance

    @property
    def balance_pennies(self) -> int:
        return self._balance

    @balance_pennies.setter
    def balance_pennies(self, value: int):
        self._balance = value

    def deposit(self, amount: int, currency: str = "USD"):
        self._balance += amount

    def withdraw(self, amount: int, currency: str = "USD"):
        if self._balance < amount:
            # raise ValueError("Insufficient funds")
            # Note: SettlementSystem checks funds via _prepare_seamless_funds before calling withdraw.
            # But TransactionEngine might check it again?
            # The engine uses adapter.withdraw which calls entity.withdraw.
            pass
        self._balance -= amount

    def get_balance(self, currency: str = "USD"):
        return self._balance

    # For IFinancialAgent compatibility
    def _deposit(self, amount: int, currency: str = "USD"):
        self.deposit(amount, currency)

    def _withdraw(self, amount: int, currency: str = "USD"):
        self.withdraw(amount, currency)

    @property
    def total_wealth(self) -> int:
        return self._balance

    def get_all_balances(self):
        return {"USD": self._balance}

    def get_liquid_assets(self, currency="USD"):
        return self._balance

    def get_total_debt(self):
        return 0

# --- Tests ---

def test_transaction_legacy_init():
    """Verify legacy initialization with price works and sets total_pennies."""
    # Legacy: price=10.0, quantity=1.0 -> total_pennies=1000
    tx = Transaction(
        buyer_id=1, seller_id=2, item_id="test", quantity=1.0,
        price=10.0, market_id="test_market", transaction_type="goods", time=0
        # total_pennies defaults to 0
    )
    assert tx.total_pennies == 1000
    assert tx.price == 10.0

def test_transaction_ssot_enforcement():
    """Verify total_pennies updates price."""
    # New: total_pennies=2000, quantity=2.0 -> price should be 10.0
    tx = Transaction(
        buyer_id=1, seller_id=2, item_id="test", quantity=2.0,
        price=0.0, market_id="test_market", transaction_type="goods", time=0,
        total_pennies=2000
    )
    assert tx.price == 10.0

def test_transaction_float_rejection():
    """Verify float passed to total_pennies raises FloatIncursionError."""
    with pytest.raises(FloatIncursionError):
        Transaction(
            buyer_id=1, seller_id=2, item_id="test", quantity=1.0,
            price=0.0, market_id="test_market", transaction_type="goods", time=0,
            total_pennies=100.5 # Float!
        )

def test_settlement_transfer_success():
    """Verify successful integer transfer."""
    settlement = SettlementSystem()

    sender = MockFinancialAgent(1, 1000)
    receiver = MockFinancialAgent(2, 0)

    # We pass explicit context_agents to create the engine
    # SettlementSystem._get_engine will use these agents to build the map.

    # Also we need to make sure _prepare_seamless_funds passes.
    # It checks IFinancialEntity.balance_pennies or IFinancialAgent.get_balance.

    tx = settlement.transfer(sender, receiver, 100, "test", currency="USD")

    assert tx is not None
    assert sender.balance_pennies == 900
    assert receiver.balance_pennies == 100
    assert tx.amount_pennies == 100

def test_settlement_transfer_float_rejection():
    """Verify float amount raises FloatIncursionError."""
    settlement = SettlementSystem()
    sender = MockFinancialAgent(1, 1000)
    receiver = MockFinancialAgent(2, 0)

    with pytest.raises(FloatIncursionError):
        settlement.transfer(sender, receiver, 10.5, "test")

def test_settlement_transfer_negative_rejection():
    """Verify negative amount raises ValueError."""
    settlement = SettlementSystem()
    sender = MockFinancialAgent(1, 1000)
    receiver = MockFinancialAgent(2, 0)

    with pytest.raises(ValueError):
        settlement.transfer(sender, receiver, -100, "test")

def test_bank_grant_loan_float_rejection():
    """Verify Bank.grant_loan rejects float amount."""
    mock_config = MagicMock()
    bank = Bank(AgentID(1), 1000, mock_config)

    with pytest.raises(FloatIncursionError):
        bank.grant_loan(AgentID(2), 1000.5, 0.05)

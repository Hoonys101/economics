import pytest
from unittest.mock import MagicMock, PropertyMock, patch
from simulation.systems.settlement_system import SettlementSystem
from modules.finance.api import IFinancialAgent, IBank, InsufficientFundsError, ICentralBank
from modules.system.constants import ID_CENTRAL_BANK
from modules.system.api import DEFAULT_CURRENCY, IAgentRegistry

from modules.finance.api import IPortfolioHandler, IHeirProvider, PortfolioDTO, PortfolioAsset

class MockRegistry(IAgentRegistry):
    def __init__(self):
        self.agents = {}

    def register(self, agent):
        self.agents[agent.id] = agent
        self.agents[str(agent.id)] = agent

    def get_agent(self, agent_id):
        return self.agents.get(agent_id) or self.agents.get(str(agent_id))

    def get_all_financial_agents(self):
        return list(self.agents.values())

    def set_state(self, state):
        pass

class MockAgent(IFinancialAgent, IPortfolioHandler, IHeirProvider):
    def __init__(self, agent_id, assets=0, heir_id=None):
        self._id = agent_id
        self._assets = int(assets)
        self.portfolio = PortfolioDTO(assets=[])
        self._heir_id = heir_id

        # Mock wallet to satisfy SettlementSystem checks
        self._wallet = MagicMock()
        self._wallet.get_balance.side_effect = lambda c=DEFAULT_CURRENCY: self._assets if c == DEFAULT_CURRENCY else 0
        self._wallet.owner_id = self._id

    @property
    def wallet(self):
        return self._wallet

    @property
    def id(self):
        return self._id

    @property
    def assets(self):
        return self._assets

    def _withdraw(self, amount, currency=DEFAULT_CURRENCY):
        if currency != DEFAULT_CURRENCY:
             raise ValueError(f"MockAgent only supports {DEFAULT_CURRENCY}")
        if self._assets < amount:
            raise InsufficientFundsError("Insufficient funds")
        self._assets -= int(amount)

    def _deposit(self, amount, currency=DEFAULT_CURRENCY):
        if currency != DEFAULT_CURRENCY:
             # Just ignore other currencies for simple tests or store them if needed
             pass
        else:
             self._assets += int(amount)

    def get_balance(self, currency=DEFAULT_CURRENCY) -> int:
        if currency == DEFAULT_CURRENCY:
            return self._assets
        return 0

    def get_all_balances(self):
        return {DEFAULT_CURRENCY: self._assets}

    @property
    def total_wealth(self) -> int:
        return self._assets

    def _add_assets(self, amount):
        self._deposit(amount)

    def _sub_assets(self, amount):
        self._withdraw(amount)

    def get_portfolio(self) -> PortfolioDTO:
        return self.portfolio

    def clear_portfolio(self) -> None:
        self.portfolio = PortfolioDTO(assets=[])

    def receive_portfolio(self, portfolio: PortfolioDTO) -> None:
        self.portfolio.assets.extend(portfolio.assets)

    def get_heir(self):
        return self._heir_id

class MockCentralBank(MockAgent, ICentralBank):
    # Central Bank can withdraw infinitely (negative assets allowed for tracking)
    def _withdraw(self, amount, currency=DEFAULT_CURRENCY):
        self._assets -= int(amount)

    def process_omo_settlement(self, transaction) -> None:
        pass

    def execute_open_market_operation(self, instruction):
        return []

class MockBank(IBank):
    def __init__(self):
        self.id = 999
        self.accounts = {}
        self.own_assets = 10000

    # IFinancialAgent impl
    def _deposit(self, amount: int, currency: str = DEFAULT_CURRENCY) -> None:
        if currency == DEFAULT_CURRENCY:
            self.own_assets += int(amount)

    def _withdraw(self, amount: int, currency: str = DEFAULT_CURRENCY) -> None:
        if currency == DEFAULT_CURRENCY:
            self.own_assets -= int(amount)

    def get_balance(self, currency: str = DEFAULT_CURRENCY) -> int:
        if currency == DEFAULT_CURRENCY:
            return self.own_assets
        return 0

    # IBank impl
    def get_total_deposits(self) -> int:
        return sum(self.accounts.values())

    def get_customer_balance(self, agent_id: str) -> int:
        return self.accounts.get(str(agent_id), 0)

    def withdraw_for_customer(self, agent_id: int, amount: int) -> bool:
        str_id = str(agent_id)
        balance = self.accounts.get(str_id, 0)
        if balance >= amount:
            self.accounts[str_id] = balance - int(amount)
            return True
        return False

    def deposit_for_customer(self, agent_id: int, amount: int):
        str_id = str(agent_id)
        self.accounts[str_id] = self.accounts.get(str_id, 0) + int(amount)

    # Stub other IBank methods
    def grant_loan(self, *args, **kwargs): return None
    def stage_loan(self, *args, **kwargs): return None
    def repay_loan(self, loan_id: str, amount: int) -> int: return amount
    def get_debt_status(self, *args, **kwargs): return None
    def terminate_loan(self, *args, **kwargs): return None
    def get_total_deposits_pennies(self) -> int: return self.get_total_deposits()
    def close_account(self, agent_id) -> int: return self.accounts.pop(str(agent_id), 0)
    def receive_repayment(self, borrower_id, amount: int) -> int: return amount

@pytest.fixture
def mock_bank():
    return MockBank()

@pytest.fixture
def settlement_system(mock_bank):
    registry = MockRegistry()
    registry.register(mock_bank)
    system = SettlementSystem(bank=mock_bank)
    system.agent_registry = registry
    return system

def test_transfer_success(settlement_system):
    sender = MockAgent(1, 100)
    receiver = MockAgent(2, 50)
    settlement_system.agent_registry.register(sender)
    settlement_system.agent_registry.register(receiver)

    tx = settlement_system.transfer(sender, receiver, 20, "Test Transfer", tick=10)

    assert tx is not None
    assert tx.quantity == 20
    assert settlement_system.get_balance(sender.id) == 80
    assert settlement_system.get_balance(receiver.id) == 70
    assert tx.time == 10

def test_transfer_insufficient_funds(settlement_system):
    sender = MockAgent(1, 10)
    receiver = MockAgent(2, 50)
    settlement_system.agent_registry.register(sender)
    settlement_system.agent_registry.register(receiver)

    tx = settlement_system.transfer(sender, receiver, 20, "Test Fail", tick=10)

    assert tx is None
    assert settlement_system.get_balance(sender.id) == 10
    assert settlement_system.get_balance(receiver.id) == 50

def test_create_and_transfer_minting(settlement_system):
    cb = MockCentralBank(ID_CENTRAL_BANK, 0)
    receiver = MockAgent(1, 0)
    settlement_system.agent_registry.register(cb)
    settlement_system.agent_registry.register(receiver)

    tx = settlement_system.create_and_transfer(cb, receiver, 100, "Minting", tick=5)

    assert tx is not None
    assert settlement_system.get_balance(receiver.id) == 100
    assert settlement_system.get_balance(cb.id) == 0

def test_create_and_transfer_government_grant(settlement_system):
    gov = MockAgent(3, 1000)
    receiver = MockAgent(1, 0)
    settlement_system.agent_registry.register(gov)
    settlement_system.agent_registry.register(receiver)

    tx = settlement_system.create_and_transfer(gov, receiver, 100, "Grant", tick=5)

    assert tx is not None
    assert settlement_system.get_balance(receiver.id) == 100
    assert settlement_system.get_balance(gov.id) == 900

def test_transfer_and_destroy_burning(settlement_system):
    cb = MockCentralBank(ID_CENTRAL_BANK, 0)
    sender = MockAgent(1, 100)
    settlement_system.agent_registry.register(cb)
    settlement_system.agent_registry.register(sender)

    tx = settlement_system.transfer_and_destroy(sender, cb, 50, "Burning", tick=5)

    assert tx is not None
    assert settlement_system.get_balance(sender.id) == 50
    assert settlement_system.get_balance(cb.id) == 0

def test_transfer_and_destroy_tax(settlement_system):
    gov = MockAgent(3, 0)
    sender = MockAgent(1, 100)
    settlement_system.agent_registry.register(gov)
    settlement_system.agent_registry.register(sender)

    tx = settlement_system.transfer_and_destroy(sender, gov, 20, "Tax", tick=5)

    assert tx is not None
    assert settlement_system.get_balance(sender.id) == 80
    assert settlement_system.get_balance(gov.id) == 20

def test_record_liquidation(settlement_system):
    agent = MockAgent(1, 0)
    settlement_system.agent_registry.register(agent)

    settlement_system.record_liquidation(agent, 100, 50, 20, "Bankruptcy", tick=1)
    assert settlement_system.total_liquidation_losses == 130

    settlement_system.record_liquidation(agent, 10, 0, 0, "More Loss", tick=2)
    assert settlement_system.total_liquidation_losses == 140

def test_record_liquidation_escheatment(settlement_system):
    agent = MockAgent(1, 50)
    gov = MockAgent(99, 0)
    settlement_system.agent_registry.register(agent)
    settlement_system.agent_registry.register(gov)

    settlement_system.record_liquidation(
        agent,
        inventory_value=10,
        capital_value=10,
        recovered_cash=0,
        reason="Escheatment Test",
        tick=1,
        government_agent=gov
    )

    assert settlement_system.total_liquidation_losses == 20
    assert settlement_system.get_balance(agent.id) == 0
    assert settlement_system.get_balance(gov.id) == 50

def test_transfer_rollback(settlement_system):
    class FaultyAgent(MockAgent):
        def _deposit(self, amount, currency=DEFAULT_CURRENCY):
            raise Exception("Deposit Failed")

    sender = MockAgent(1, 100)
    receiver = FaultyAgent(2, 50)
    settlement_system.agent_registry.register(sender)
    settlement_system.agent_registry.register(receiver)

    tx = settlement_system.transfer(sender, receiver, 20, "Faulty Transfer", tick=10)

    assert tx is None
    assert settlement_system.get_balance(sender.id) == 100
    assert settlement_system.get_balance(receiver.id) == 50

# --- NEW TESTS BELOW ---

def test_transfer_insufficient_cash_despite_bank_balance(settlement_system, mock_bank):
    """
    Verifies that 'Seamless' automatic withdrawals are REMOVED.
    Agent has 10 cash, 100 in bank, needs 50.
    Should FAIL because SettlementSystem checks cash only.
    """
    sender = MockAgent(1, 10)
    receiver = MockAgent(2, 0)
    settlement_system.agent_registry.register(sender)
    settlement_system.agent_registry.register(receiver)

    mock_bank.deposit_for_customer(1, 100)

    # Attempt transfer of 50. Has 10 cash, 100 bank.
    # Expectation: FAIL (None) because auto-withdrawal is disabled.
    tx = settlement_system.transfer(sender, receiver, 50, "Seamless Disabled", tick=10)

    assert tx is None
    assert settlement_system.get_balance(sender.id) == 10 # Untouched
    assert mock_bank.get_customer_balance("1") == 100 # Bank untouched
    assert settlement_system.get_balance(receiver.id) == 0

def test_transfer_insufficient_total_funds(settlement_system, mock_bank):
    # Agent has 10 cash, but only 10 in bank. Needs 50. Total 20. Fail.
    sender = MockAgent(1, 10)
    receiver = MockAgent(2, 0)
    settlement_system.agent_registry.register(sender)
    settlement_system.agent_registry.register(receiver)

    mock_bank.deposit_for_customer(1, 10)

    tx = settlement_system.transfer(sender, receiver, 50, "Total Fail", tick=10)

    assert tx is None
    assert settlement_system.get_balance(sender.id) == 10 # Untouched
    assert mock_bank.get_customer_balance("1") == 10
    assert settlement_system.get_balance(receiver.id) == 0

def test_execute_multiparty_settlement_success(settlement_system):
    # A->B 50, B->C 30
    agent_a = MockAgent("A", 100)
    agent_b = MockAgent("B", 100)
    agent_c = MockAgent("C", 100)
    settlement_system.agent_registry.register(agent_a)
    settlement_system.agent_registry.register(agent_b)
    settlement_system.agent_registry.register(agent_c)

    transfers = [
        (agent_a, agent_b, 50),
        (agent_b, agent_c, 30)
    ]

    success = settlement_system.execute_multiparty_settlement(transfers, tick=1)

    assert success is True
    assert settlement_system.get_balance(agent_a.id) == 50
    assert settlement_system.get_balance(agent_b.id) == 120 # 100 + 50 - 30
    assert settlement_system.get_balance(agent_c.id) == 130

def test_execute_multiparty_settlement_rollback(settlement_system):
    # A->B 50 (Success), B->C 200 (Fail, B only has 100)
    agent_a = MockAgent("A", 100)
    agent_b = MockAgent("B", 100) # has 100
    agent_c = MockAgent("C", 0)
    settlement_system.agent_registry.register(agent_a)
    settlement_system.agent_registry.register(agent_b)
    settlement_system.agent_registry.register(agent_c)

    transfers = [
        (agent_a, agent_b, 50), # This succeeds initially
        (agent_b, agent_c, 200) # This fails (150 vs 200? No, check is done per transfer.)
    ]

    success = settlement_system.execute_multiparty_settlement(transfers, tick=1)

    assert success is False
    assert settlement_system.get_balance(agent_a.id) == 100
    assert settlement_system.get_balance(agent_b.id) == 100
    assert settlement_system.get_balance(agent_c.id) == 0

def test_settle_atomic_success(settlement_system):
    # A pays B 50 and C 50. A has 100.
    agent_a = MockAgent("A", 100)
    agent_b = MockAgent("B", 0)
    agent_c = MockAgent("C", 0)
    settlement_system.agent_registry.register(agent_a)
    settlement_system.agent_registry.register(agent_b)
    settlement_system.agent_registry.register(agent_c)

    credits = [
        (agent_b, 50, "pay b"),
        (agent_c, 50, "pay c")
    ]

    success = settlement_system.settle_atomic(agent_a, credits, tick=1)

    assert success is True
    assert settlement_system.get_balance(agent_a.id) == 0
    assert settlement_system.get_balance(agent_b.id) == 50
    assert settlement_system.get_balance(agent_c.id) == 50

def test_settle_atomic_rollback(settlement_system):
    # A pays B 50 and C 50. A has 90. Total debit 100 > 90. Fail before any execution.
    agent_a = MockAgent("A", 90)
    agent_b = MockAgent("B", 0)
    agent_c = MockAgent("C", 0)
    settlement_system.agent_registry.register(agent_a)
    settlement_system.agent_registry.register(agent_b)
    settlement_system.agent_registry.register(agent_c)

    credits = [
        (agent_b, 50, "pay b"),
        (agent_c, 50, "pay c")
    ]

    success = settlement_system.settle_atomic(agent_a, credits, tick=1)

    assert success is False
    assert settlement_system.get_balance(agent_a.id) == 90
    assert settlement_system.get_balance(agent_b.id) == 0

def test_settle_atomic_credit_fail_rollback(settlement_system):
    # A pays Faulty 50. A has 100.
    class FaultyAgent(MockAgent):
        def _deposit(self, amount, currency=DEFAULT_CURRENCY):
            raise Exception("Deposit Fail")

    agent_a = MockAgent("A", 100)
    agent_b = FaultyAgent("B", 0)
    settlement_system.agent_registry.register(agent_a)
    settlement_system.agent_registry.register(agent_b)

    credits = [(agent_b, 50, "pay b")]

    success = settlement_system.settle_atomic(agent_a, credits, tick=1)

    assert success is False
    assert settlement_system.get_balance(agent_a.id) == 100 # Refunded
    assert settlement_system.get_balance(agent_b.id) == 0

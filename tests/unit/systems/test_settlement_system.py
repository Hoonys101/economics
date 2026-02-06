import pytest
from unittest.mock import MagicMock, PropertyMock, patch
from simulation.systems.settlement_system import SettlementSystem
from modules.finance.api import IFinancialEntity, InsufficientFundsError
from modules.system.constants import ID_CENTRAL_BANK

from modules.finance.api import IPortfolioHandler, IHeirProvider, PortfolioDTO, PortfolioAsset

class MockAgent(IFinancialEntity, IPortfolioHandler, IHeirProvider):
    def __init__(self, agent_id, assets=0.0, heir_id=None):
        self._id = agent_id
        self._assets = float(assets)
        self.portfolio = PortfolioDTO(assets=[])
        self._heir_id = heir_id

        # Mock wallet to satisfy SettlementSystem checks
        self._wallet = MagicMock()
        self._wallet.get_balance.side_effect = lambda c=None: self._assets
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

    def withdraw(self, amount, currency="USD"):
        if self._assets < amount:
            raise InsufficientFundsError("Insufficient funds")
        self._assets -= amount

    def deposit(self, amount, currency="USD"):
        self._assets += amount

    def _add_assets(self, amount):
        self.deposit(amount)

    def _sub_assets(self, amount):
        self.withdraw(amount)

    def get_portfolio(self) -> PortfolioDTO:
        return self.portfolio

    def clear_portfolio(self) -> None:
        self.portfolio = PortfolioDTO(assets=[])

    def receive_portfolio(self, portfolio: PortfolioDTO) -> None:
        self.portfolio.assets.extend(portfolio.assets)

    def get_heir(self):
        return self._heir_id

class MockCentralBank(MockAgent):
    # Central Bank can withdraw infinitely (negative assets allowed for tracking)
    def withdraw(self, amount, currency="USD"):
        self._assets -= amount

class MockBank:
    def __init__(self):
        self.accounts = {}

    def get_balance(self, agent_id: str) -> float:
        return self.accounts.get(str(agent_id), 0.0)

    def withdraw_for_customer(self, agent_id: int, amount: float) -> bool:
        str_id = str(agent_id)
        balance = self.accounts.get(str_id, 0.0)
        if balance >= amount:
            self.accounts[str_id] = balance - amount
            return True
        return False

    def deposit_for_customer(self, agent_id: int, amount: float):
        str_id = str(agent_id)
        self.accounts[str_id] = self.accounts.get(str_id, 0.0) + amount

@pytest.fixture
def mock_bank():
    return MockBank()

@pytest.fixture
def settlement_system(mock_bank):
    return SettlementSystem(bank=mock_bank)

def test_transfer_success(settlement_system):
    sender = MockAgent(1, 100.0)
    receiver = MockAgent(2, 50.0)

    tx = settlement_system.transfer(sender, receiver, 20.0, "Test Transfer", tick=10)

    assert tx is not None
    assert tx.quantity == 20.0
    assert sender.assets == 80.0
    assert receiver.assets == 70.0
    assert tx.time == 10

def test_transfer_insufficient_funds(settlement_system):
    sender = MockAgent(1, 10.0)
    receiver = MockAgent(2, 50.0)

    tx = settlement_system.transfer(sender, receiver, 20.0, "Test Fail", tick=10)

    assert tx is None
    assert sender.assets == 10.0
    assert receiver.assets == 50.0

def test_create_and_transfer_minting(settlement_system):
    cb = MockCentralBank(ID_CENTRAL_BANK, 0.0)
    receiver = MockAgent(1, 0.0)

    tx = settlement_system.create_and_transfer(cb, receiver, 100.0, "Minting", tick=5)

    assert tx is not None
    assert receiver.assets == 100.0
    assert cb.assets == 0.0

def test_create_and_transfer_government_grant(settlement_system):
    gov = MockAgent(3, 1000.0)
    receiver = MockAgent(1, 0.0)

    tx = settlement_system.create_and_transfer(gov, receiver, 100.0, "Grant", tick=5)

    assert tx is not None
    assert receiver.assets == 100.0
    assert gov.assets == 900.0

def test_transfer_and_destroy_burning(settlement_system):
    cb = MockCentralBank(ID_CENTRAL_BANK, 0.0)
    sender = MockAgent(1, 100.0)

    tx = settlement_system.transfer_and_destroy(sender, cb, 50.0, "Burning", tick=5)

    assert tx is not None
    assert sender.assets == 50.0
    assert cb.assets == 0.0

def test_transfer_and_destroy_tax(settlement_system):
    gov = MockAgent(3, 0.0)
    sender = MockAgent(1, 100.0)

    tx = settlement_system.transfer_and_destroy(sender, gov, 20.0, "Tax", tick=5)

    assert tx is not None
    assert sender.assets == 80.0
    assert gov.assets == 20.0

def test_record_liquidation(settlement_system):
    agent = MockAgent(1, 0.0)
    settlement_system.record_liquidation(agent, 100.0, 50.0, 20.0, "Bankruptcy", tick=1)
    assert settlement_system.total_liquidation_losses == 130.0

    settlement_system.record_liquidation(agent, 10.0, 0.0, 0.0, "More Loss", tick=2)
    assert settlement_system.total_liquidation_losses == 140.0

def test_record_liquidation_escheatment(settlement_system):
    agent = MockAgent(1, 50.0)
    gov = MockAgent(99, 0.0)

    settlement_system.record_liquidation(
        agent,
        inventory_value=10.0,
        capital_value=10.0,
        recovered_cash=0.0,
        reason="Escheatment Test",
        tick=1,
        government_agent=gov
    )

    assert settlement_system.total_liquidation_losses == 20.0
    assert agent.assets == 0.0
    assert gov.assets == 50.0

def test_transfer_rollback(settlement_system):
    class FaultyAgent(MockAgent):
        def deposit(self, amount):
            raise Exception("Deposit Failed")

    sender = MockAgent(1, 100.0)
    receiver = FaultyAgent(2, 50.0)

    tx = settlement_system.transfer(sender, receiver, 20.0, "Faulty Transfer", tick=10)

    assert tx is None
    assert sender.assets == 100.0
    assert receiver.assets == 50.0

def test_atomic_settlement_success(settlement_system):
    deceased_id = 101
    deceased_agent = MockAgent(deceased_id, 500.0)
    heir1 = MockAgent(201, 100.0)
    heir2 = MockAgent(202, 50.0)

    account = settlement_system.create_settlement(deceased_agent, tick=1)

    assert account.status == "OPEN"
    assert account.escrow_cash == 500.0

    plan = [
        (heir1, 250.0, "Split 1", "inheritance"),
        (heir2, 250.0, "Split 2", "inheritance")
    ]

    receipts = settlement_system.execute_settlement(deceased_id, plan, tick=2)

    assert len(receipts) == 2
    assert receipts[0].quantity == 250.0
    assert heir1.assets == 350.0
    assert heir2.assets == 300.0
    assert account.escrow_cash == 0.0

    success = settlement_system.verify_and_close(deceased_id, tick=3)
    assert success is True
    assert account.status == "CLOSED"

def test_atomic_settlement_leak_prevention(settlement_system):
    deceased_id = 102
    deceased_agent = MockAgent(deceased_id, 100.0)
    heir = MockAgent(203, 0.0)

    account = settlement_system.create_settlement(deceased_agent, 1)

    plan = [(heir, 90.0, "Partial", "inheritance")]
    settlement_system.execute_settlement(deceased_id, plan, 1)

    assert heir.assets == 90.0
    assert account.escrow_cash == 10.0

    success = settlement_system.verify_and_close(deceased_id, 1)

    assert success is False
    assert account.status == "CLOSED_WITH_LEAK"
    assert account.escrow_cash == 0.0

def test_atomic_settlement_overdraft_protection(settlement_system):
    deceased_id = 103
    deceased_agent = MockAgent(deceased_id, 100.0)
    heir = MockAgent(204, 0.0)

    account = settlement_system.create_settlement(deceased_agent, 1)

    plan = [(heir, 150.0, "Overdraft", "inheritance")]
    receipts = settlement_system.execute_settlement(deceased_id, plan, 1)

    assert len(receipts) == 0
    assert heir.assets == 0.0
    assert account.escrow_cash == 100.0


# --- NEW TESTS BELOW ---

def test_transfer_seamless_success(settlement_system, mock_bank):
    # Agent has 10 cash, but 100 in bank. Needs to transfer 50.
    sender = MockAgent(1, 10.0)
    receiver = MockAgent(2, 0.0)
    mock_bank.deposit_for_customer(1, 100.0)

    tx = settlement_system.transfer(sender, receiver, 50.0, "Seamless", tick=10)

    assert tx is not None
    assert sender.assets == 0.0 # Cash drained
    assert mock_bank.get_balance("1") == 60.0 # 100 - (50 - 10) = 60
    assert receiver.assets == 50.0

def test_transfer_seamless_fail_bank(settlement_system, mock_bank):
    # Agent has 10 cash, but only 10 in bank. Needs 50. Total 20. Fail.
    sender = MockAgent(1, 10.0)
    receiver = MockAgent(2, 0.0)
    mock_bank.deposit_for_customer(1, 10.0)

    tx = settlement_system.transfer(sender, receiver, 50.0, "Seamless Fail", tick=10)

    assert tx is None
    assert sender.assets == 10.0 # Untouched (due to check)
    assert mock_bank.get_balance("1") == 10.0
    assert receiver.assets == 0.0

def test_execute_multiparty_settlement_success(settlement_system):
    # A->B 50, B->C 30
    agent_a = MockAgent("A", 100.0)
    agent_b = MockAgent("B", 100.0)
    agent_c = MockAgent("C", 100.0)

    transfers = [
        (agent_a, agent_b, 50.0),
        (agent_b, agent_c, 30.0)
    ]

    success = settlement_system.execute_multiparty_settlement(transfers, tick=1)

    assert success is True
    assert agent_a.assets == 50.0
    assert agent_b.assets == 120.0 # 100 + 50 - 30
    assert agent_c.assets == 130.0

def test_execute_multiparty_settlement_rollback(settlement_system):
    # A->B 50 (Success), B->C 200 (Fail, B only has 100)
    agent_a = MockAgent("A", 100.0)
    agent_b = MockAgent("B", 100.0) # has 100
    agent_c = MockAgent("C", 0.0)

    transfers = [
        (agent_a, agent_b, 50.0), # This succeeds initially
        (agent_b, agent_c, 200.0) # This fails (150 vs 200? No, check is done per transfer.)
        # Wait, if done sequentially:
        # 1. A->B: A=50, B=150.
        # 2. B->C: B=150. If transfer 200 -> Fail.
        # So rollback A->B.
    ]

    # Note: MockAgent withdraw checks balance.
    # But wait, settlement_system.transfer calls withdraw.
    # In seq: A withdraws 50 (OK). B deposits 50 (OK).
    # Then B withdraws 200 (Fail, has 150).
    # Rollback: B withdraws 50 (OK). A deposits 50 (OK).

    success = settlement_system.execute_multiparty_settlement(transfers, tick=1)

    assert success is False
    assert agent_a.assets == 100.0
    assert agent_b.assets == 100.0
    assert agent_c.assets == 0.0

def test_settle_atomic_success(settlement_system):
    # A pays B 50 and C 50. A has 100.
    agent_a = MockAgent("A", 100.0)
    agent_b = MockAgent("B", 0.0)
    agent_c = MockAgent("C", 0.0)

    credits = [
        (agent_b, 50.0, "pay b"),
        (agent_c, 50.0, "pay c")
    ]

    success = settlement_system.settle_atomic(agent_a, credits, tick=1)

    assert success is True
    assert agent_a.assets == 0.0
    assert agent_b.assets == 50.0
    assert agent_c.assets == 50.0

def test_settle_atomic_rollback(settlement_system):
    # A pays B 50 and C 50. A has 90. Total debit 100 > 90. Fail before any execution.
    agent_a = MockAgent("A", 90.0)
    agent_b = MockAgent("B", 0.0)
    agent_c = MockAgent("C", 0.0)

    credits = [
        (agent_b, 50.0, "pay b"),
        (agent_c, 50.0, "pay c")
    ]

    success = settlement_system.settle_atomic(agent_a, credits, tick=1)

    assert success is False
    assert agent_a.assets == 90.0
    assert agent_b.assets == 0.0

def test_settle_atomic_credit_fail_rollback(settlement_system):
    # A pays Faulty 50. A has 100.
    class FaultyAgent(MockAgent):
        def deposit(self, amount):
            raise Exception("Deposit Fail")

    agent_a = MockAgent("A", 100.0)
    agent_b = FaultyAgent("B", 0.0)

    credits = [(agent_b, 50.0, "pay b")]

    success = settlement_system.settle_atomic(agent_a, credits, tick=1)

    assert success is False
    assert agent_a.assets == 100.0 # Refunded
    assert agent_b.assets == 0.0

def test_inheritance_portfolio_transfer(settlement_system):
    heir_id = 900
    deceased = MockAgent(100, 0.0, heir_id=heir_id)
    deceased.portfolio.assets.append(PortfolioAsset(asset_type="stock", asset_id="TEST", quantity=10))

    heir = MockAgent(heir_id, 0.0)

    # 1. Create
    account = settlement_system.create_settlement(deceased, 1)
    assert len(account.escrow_portfolio.assets) == 1
    assert len(deceased.portfolio.assets) == 0 # Moved to escrow

    # 2. Execute (Heir is recipient)
    plan = [(heir, 0.0, "Portfolio Transfer", "inheritance")]
    settlement_system.execute_settlement(100, plan, 2)

    assert len(heir.portfolio.assets) == 1
    assert heir.portfolio.assets[0].asset_id == "TEST"
    assert len(account.escrow_portfolio.assets) == 0

def test_escheatment_portfolio_transfer(settlement_system):
    deceased = MockAgent(100, 0.0, heir_id=None) # No heir
    deceased.portfolio.assets.append(PortfolioAsset(asset_type="bond", asset_id="GOV_TEST", quantity=5))

    gov = MockAgent("GOVERNMENT", 0.0)
    # MockAgent doesn't have agent_type="government", but id="GOVERNMENT" matches heuristic in settlement_system.py

    # 1. Create
    account = settlement_system.create_settlement(deceased, 1)
    assert account.is_escheatment is True

    # 2. Execute (Gov is recipient)
    plan = [(gov, 0.0, "Escheatment", "inheritance")]
    settlement_system.execute_settlement(100, plan, 2)

    assert len(gov.portfolio.assets) == 1
    assert gov.portfolio.assets[0].asset_id == "GOV_TEST"
    assert len(account.escrow_portfolio.assets) == 0


import pytest
from unittest.mock import MagicMock, PropertyMock
from simulation.systems.settlement_system import SettlementSystem
from modules.finance.api import IFinancialEntity, InsufficientFundsError

class MockAgent(IFinancialEntity):
    def __init__(self, agent_id, assets=0.0):
        self._id = agent_id
        self._assets = float(assets)

    @property
    def id(self):
        return self._id

    @property
    def assets(self):
        return self._assets

    def withdraw(self, amount):
        if self._assets < amount:
            raise InsufficientFundsError("Insufficient funds")
        self._assets -= amount

    def deposit(self, amount):
        self._assets += amount

    def _add_assets(self, amount):
        self.deposit(amount)

    def _sub_assets(self, amount):
        self.withdraw(amount)

class MockCentralBank(MockAgent):
    # Central Bank can withdraw infinitely (negative assets allowed for tracking)
    def withdraw(self, amount):
        self._assets -= amount

@pytest.fixture
def settlement_system():
    return SettlementSystem()

def test_transfer_success(settlement_system):
    sender = MockAgent(1, 100.0)
    receiver = MockAgent(2, 50.0)

    tx = settlement_system.transfer(sender, receiver, 20.0, "Test Transfer", tick=10)

    assert tx is not None
    assert tx["quantity"] == 20.0
    assert sender.assets == 80.0
    assert receiver.assets == 70.0
    assert tx["time"] == 10

def test_transfer_insufficient_funds(settlement_system):
    sender = MockAgent(1, 10.0)
    receiver = MockAgent(2, 50.0)

    tx = settlement_system.transfer(sender, receiver, 20.0, "Test Fail", tick=10)

    assert tx is None
    assert sender.assets == 10.0
    assert receiver.assets == 50.0

def test_create_and_transfer_minting(settlement_system):
    cb = MockCentralBank("CENTRAL_BANK", 0.0)
    receiver = MockAgent(1, 0.0)

    tx = settlement_system.create_and_transfer(cb, receiver, 100.0, "Minting", tick=5)

    assert tx is not None
    assert receiver.assets == 100.0
    # CB might not change assets if logic is just deposit on dest, OR withdraw on CB.
    # Implementation checks if CB: calls destination.deposit(amount).
    # Does NOT call source.withdraw? Let's check implementation.
    # Implementation: "destination.deposit(amount)". Does NOT call withdraw on source_authority.
    # So CB assets remain 0.0 (if we consider Minting separate from CB balance sheet here).
    # If CB has `mint` method, it would be called. But here we just inject.
    assert cb.assets == 0.0

def test_create_and_transfer_government_grant(settlement_system):
    gov = MockAgent(3, 1000.0)
    receiver = MockAgent(1, 0.0)

    # Gov is NOT Central Bank, so it should act as transfer
    tx = settlement_system.create_and_transfer(gov, receiver, 100.0, "Grant", tick=5)

    assert tx is not None
    assert receiver.assets == 100.0
    assert gov.assets == 900.0 # Standard transfer

def test_transfer_and_destroy_burning(settlement_system):
    cb = MockCentralBank("CENTRAL_BANK", 0.0)
    sender = MockAgent(1, 100.0)

    tx = settlement_system.transfer_and_destroy(sender, cb, 50.0, "Burning", tick=5)

    assert tx is not None
    assert sender.assets == 50.0
    # Implementation for CB sink: "source.withdraw(amount)". Does NOT call deposit on sink.
    assert cb.assets == 0.0

def test_transfer_and_destroy_tax(settlement_system):
    gov = MockAgent(3, 0.0)
    sender = MockAgent(1, 100.0)

    # Gov is NOT Central Bank, so it should act as transfer
    tx = settlement_system.transfer_and_destroy(sender, gov, 20.0, "Tax", tick=5)

    assert tx is not None
    assert sender.assets == 80.0
    assert gov.assets == 20.0

def test_record_liquidation(settlement_system):
    agent = MockAgent(1, 0.0)

    # Initial loss
    settlement_system.record_liquidation(agent, 100.0, 50.0, 20.0, "Bankruptcy", tick=1)
    # Loss = 100 + 50 - 20 = 130
    assert settlement_system.total_liquidation_losses == 130.0

    # Another loss
    settlement_system.record_liquidation(agent, 10.0, 0.0, 0.0, "More Loss", tick=2)
    assert settlement_system.total_liquidation_losses == 140.0

def test_transfer_rollback(settlement_system):
    class FaultyAgent(MockAgent):
        def deposit(self, amount):
            raise Exception("Deposit Failed")

    sender = MockAgent(1, 100.0)
    receiver = FaultyAgent(2, 50.0)

    # Transfer should fail at deposit, trigger rollback
    tx = settlement_system.transfer(sender, receiver, 20.0, "Faulty Transfer", tick=10)

    assert tx is None
    # Sender should have 100.0 (rolled back)
    assert sender.assets == 100.0
    # Receiver should have 50.0 (unchanged)
    assert receiver.assets == 50.0

import unittest
from unittest.mock import MagicMock
from simulation.systems.transaction_processor import TransactionProcessor
from simulation.models import Transaction

class MockSettlementSystem:
    def __init__(self):
        self.settle_atomic_called = False
        self.last_credits = []
        self.last_debit_agent = None

    def settle_atomic(self, debit_agent, credits, tick):
        self.settle_atomic_called = True
        self.last_debit_agent = debit_agent
        self.last_credits = credits
        return True

    def transfer(self, *args, **kwargs):
        return True

class MockState:
    def __init__(self, settlement_system, agents, transactions, government):
        self.settlement_system = settlement_system
        self.agents = agents
        self.transactions = transactions
        self.government = government
        self.time = 0
        self.market_data = {}
        self.inactive_agents = {}
        self.stock_market = None
        self.real_estate_units = []
        self.logger = MagicMock()
        self.central_bank = None
        self.effects_queue = []

class TestTransactionProcessorV2(unittest.TestCase):
    def test_inheritance_distribution_atomic(self):
        """Verify inheritance distribution uses settle_atomic and splits correctly."""
        settlement = MockSettlementSystem()

        buyer = MagicMock()
        buyer.id = 1
        buyer.assets = 100.0

        heir1 = MagicMock()
        heir1.id = 2
        heir2 = MagicMock()
        heir2.id = 3

        agents = {1: buyer, 2: heir1, 3: heir2}
        government = MagicMock()
        government.id = 99

        tx = Transaction(
            buyer_id=1,
            seller_id=1,
            item_id="inheritance_distribution",
            quantity=1.0,
            price=0.0,
            market_id="system",
            transaction_type="inheritance_distribution",
            time=0,
            metadata={"heir_ids": [2, 3]}
        )

        state = MockState(settlement, agents, [tx], government)
        processor = TransactionProcessor(MagicMock())
        processor.execute(state)

        self.assertTrue(settlement.settle_atomic_called)
        self.assertEqual(len(settlement.last_credits), 2)
        # 100 / 2 = 50.0 each
        self.assertEqual(settlement.last_credits[0][0].id, 2)
        self.assertEqual(settlement.last_credits[0][1], 50.0)
        self.assertEqual(settlement.last_credits[1][0].id, 3)
        self.assertEqual(settlement.last_credits[1][1], 50.0)

    def test_escheatment_dynamic_leak_prevention(self):
        """Verify escheatment uses dynamic buyer.assets instead of static tx.price."""
        settlement = MockSettlementSystem()
        buyer = MagicMock()
        buyer.id = 1
        buyer.assets = 150.0 # Dynamic assets higher than tx price

        government = MagicMock()
        government.id = 99

        tx = Transaction(
            buyer_id=1,
            seller_id=99,
            item_id="escheatment_cash",
            quantity=1.0,
            price=100.0, # Old calculated price
            market_id="system",
            transaction_type="escheatment",
            time=0
        )

        state = MockState(settlement, {1: buyer, 99: government}, [tx], government)
        processor = TransactionProcessor(MagicMock())
        processor.execute(state)

        self.assertTrue(settlement.settle_atomic_called)
        # Should use buyer.assets (150.0) not tx.price (100.0)
        self.assertEqual(settlement.last_credits[0][1], 150.0)

if __name__ == '__main__':
    unittest.main()

import pytest
from unittest.mock import MagicMock
from simulation.models import Transaction, Order
from modules.system.execution.public_manager import PublicManager
from simulation.systems.transaction_manager import TransactionManager
from simulation.systems.registry import Registry
from simulation.systems.accounting import AccountingSystem

class MockAgent:
    def __init__(self, agent_id, assets=0.0):
        self.id = agent_id
        self.assets = assets
        self.inventory = {}
        self.inventory_quality = {}
        self.total_money_issued = 0.0 # for central bank checks if any

    def withdraw(self, amount):
        if self.assets < amount:
            raise Exception("Insufficient funds")
        self.assets -= amount

    def deposit(self, amount):
        self.assets += amount

class TestPublicManagerIntegration:
    def test_full_liquidation_cycle(self):
        # 1. Setup PublicManager
        config = MagicMock()
        config.LIQUIDATION_SELL_RATE = 1.0 # Sell all for test
        config.LIQUIDATION_ASK_UNDERCUT = 0.0
        # Setup GOODS config for Registry
        config.GOODS = {
            "gold": {"is_service": False, "is_essential": False}
        }
        config.RAW_MATERIAL_SECTORS = []

        pm = PublicManager(config)

        # 2. Simulate Bankruptcy Event
        event = {
            "agent_id": 99,
            "tick": 1,
            "inventory": {"gold": 10.0}
        }
        pm.process_bankruptcy_event(event)
        assert pm.managed_inventory["gold"] == 10.0

        # 3. Generate Liquidation Orders (Phase 4.5)
        # Mock Market Signals
        signals = {
            "gold": {
                "market_id": "gold",
                "item_id": "gold",
                "best_ask": 100.0,
                # ... other fields ignored by simple logic
            }
        }
        orders = pm.generate_liquidation_orders(signals)
        assert len(orders) == 1
        order = orders[0]
        assert order.quantity == 10.0
        assert order.price == 100.0
        assert pm.managed_inventory["gold"] == 0.0 # Tentatively decremented

        # 4. Simulate Market Matching (Phase 2/5)
        # Assume market matched it perfectly
        buyer = MockAgent(2, assets=5000.0)

        tx = Transaction(
            item_id="gold",
            quantity=10.0,
            price=100.0,
            buyer_id=buyer.id,
            seller_id="PUBLIC_MANAGER",
            market_id="gold",
            transaction_type="goods",
            time=1
        )

        # 5. Execute Transaction (Phase 3)
        # Setup TransactionManager dependencies
        registry = Registry()
        accounting = MagicMock() # Mock accounting
        settlement = MagicMock() # Mock settlement (won't be used for PublicManager)

        tm = TransactionManager(registry, accounting, settlement, MagicMock(), config)

        # Setup State
        state = MagicMock()
        state.transactions = [tx]
        state.agents = {buyer.id: buyer}
        state.public_manager = pm
        state.market_data = {}
        state.config_module = config
        state.time = 1

        tm.execute(state)

        # 6. Verify Outcome
        # Buyer assets should decrease: 10 * 100 = 1000
        assert buyer.assets == 4000.0

        # PublicManager treasury should increase
        assert pm.system_treasury == 1000.0

        # Buyer inventory should increase (via Registry)
        assert buyer.inventory.get("gold", 0) == 10.0

        # Accounting recorded?
        assert accounting.record_transaction.called

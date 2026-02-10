import unittest
from unittest.mock import MagicMock
from simulation.models import Transaction
from modules.system.execution.public_manager import PublicManager
from simulation.systems.transaction_manager import TransactionManager
from modules.system.api import MarketSignalDTO, DEFAULT_CURRENCY

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

class TestPublicManagerIntegrationRepro(unittest.TestCase):
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
        config.SALES_TAX_RATE = 0.0
        config.INCOME_TAX_PAYER = "HOUSEHOLD"
        config.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 1.0
        config.GOODS_INITIAL_PRICE = {}

        pm = PublicManager(config)

        # 4. Simulate Market Matching (Phase 2/5)
        # Assume market matched it perfectly
        buyer = MockAgent(2, assets=5000.0)

        tx = Transaction(
            item_id="gold",
            quantity=10.0,
            price=100.0,
            buyer_id=buyer.id,
            seller_id=-1,
            market_id="gold",
            transaction_type="goods",
            time=1
        )

        # 5. Execute Transaction (Phase 3)
        # Setup TransactionManager dependencies
        # Mock Registry to avoid side effects (Inventory update) failing on MockAgent
        registry = MagicMock()
        accounting = MagicMock() # Mock accounting
        settlement = MagicMock() # Mock settlement (won't be used for PublicManager)

        tm = TransactionManager(registry, accounting, settlement, MagicMock(), config, MagicMock())

        # Setup State
        state = MagicMock()
        state.transactions = [tx]
        state.agents = {buyer.id: buyer}
        state.public_manager = pm
        state.market_data = {}
        state.config_module = config
        state.time = 1

        tm.execute(state)

        print(f"Buyer assets: {buyer.assets}")
        print(f"PM Treasury: {pm.system_treasury}")

        # 6. Verify Outcome
        # Buyer assets should decrease: 10 * 100 = 1000
        self.assertEqual(buyer.assets, 4000.0)

        # PublicManager treasury should increase
        self.assertEqual(pm.system_treasury[DEFAULT_CURRENCY], 1000.0)

if __name__ == "__main__":
    unittest.main()

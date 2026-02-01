import unittest
from unittest.mock import MagicMock
import sys
import os

# Add repo root to path
sys.path.append(os.getcwd())

from simulation.systems.handlers.goods_handler import GoodsTransactionHandler
from simulation.systems.handlers.labor_handler import LaborTransactionHandler
from simulation.core_agents import Household
from simulation.models import Transaction

class TestHandlerFix(unittest.TestCase):
    def setUp(self):
        # Create a mock that mimics Household instance
        self.mock_household = MagicMock(spec=Household)
        # Mock inventory as a dict so get/set works
        self.mock_household.inventory = {}
        # Mock inventory_quality as a dict
        self.mock_household.inventory_quality = {}

        # Setup context
        self.mock_context = MagicMock()
        self.mock_context.config_module = MagicMock()
        self.mock_context.config_module.GOODS = {}
        self.mock_context.config_module.RAW_MATERIAL_SECTORS = []
        self.mock_context.time = 1
        self.mock_context.agents = {}
        self.mock_context.inactive_agents = {}

    def test_goods_handler_uses_record_consumption(self):
        handler = GoodsTransactionHandler()

        tx = MagicMock(spec=Transaction)
        tx.item_id = "basic_food"
        tx.quantity = 10.0

        # Setup Seller (Firm)
        seller = MagicMock()
        seller.inventory = {"basic_food": 100.0}

        # _apply_goods_effects signature: (tx, buyer, seller, trade_value, buyer_total_cost, context)
        handler._apply_goods_effects(
            tx=tx,
            buyer=self.mock_household,
            seller=seller,
            trade_value=100.0,
            buyer_total_cost=100.0,
            context=self.mock_context
        )

        self.mock_household.record_consumption.assert_called_once_with(10.0, is_food=True)
        # Also verify inventory was updated since Households do have inventory
        self.assertEqual(self.mock_household.inventory["basic_food"], 10.0)

    def test_labor_handler_uses_add_labor_income(self):
        handler = LaborTransactionHandler()

        tx = MagicMock(spec=Transaction)
        tx.price = 50.0
        tx.quantity = 1.0
        tx.transaction_type = "labor"

        seller = self.mock_household
        buyer = MagicMock() # Firm mock

        # _apply_labor_effects signature: (tx, buyer, seller, seller_net_income, buyer_total_cost, context)
        handler._apply_labor_effects(
            tx=tx,
            buyer=buyer,
            seller=seller,
            seller_net_income=45.0,
            buyer_total_cost=55.0,
            context=self.mock_context
        )

        self.mock_household.add_labor_income.assert_called_once_with(45.0)

if __name__ == '__main__':
    unittest.main()

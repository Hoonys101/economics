import unittest
from unittest.mock import MagicMock
from simulation.systems.liquidation_handlers import InventoryLiquidationHandler
from modules.system.api import DEFAULT_CURRENCY
from simulation.dtos.api import SimulationState

class TestInventoryLiquidationHandler(unittest.TestCase):
    def setUp(self):
        self.mock_settlement = MagicMock()
        self.mock_public = MagicMock()
        self.handler = InventoryLiquidationHandler(self.mock_settlement, self.mock_public)
        self.firm = MagicMock()
        self.firm.id = 1
        self.firm.config = MagicMock()
        self.firm.config.liquidation_haircut = 0.2
        self.firm.config.goods_initial_price = {"default": 10.0}
        self.firm.config.goods = {}
        self.firm.last_prices = {}
        self.firm.inventory = {}
        self.state = MagicMock(spec=SimulationState)

    def test_liquidate_no_inventory(self):
        self.firm.inventory = {}
        self.handler.liquidate(self.firm, self.state)
        self.mock_settlement.transfer.assert_not_called()

    def test_liquidate_with_inventory(self):
        self.firm.inventory = {"apple": 10}
        self.firm.last_prices = {"apple": 5.0}

        # 10 * 5.0 * (1 - 0.2) = 50 * 0.8 = 40.0

        self.mock_settlement.transfer.return_value = True

        self.handler.liquidate(self.firm, self.state)

        self.mock_settlement.transfer.assert_called_once_with(
            self.mock_public,
            self.firm,
            40.0,
            "Asset Liquidation (Inventory) - Firm 1",
            currency=DEFAULT_CURRENCY
        )
        self.mock_public.receive_liquidated_assets.assert_called_once_with({"apple": 10})
        # Check inventory is cleared
        self.assertEqual(self.firm.inventory, {})

    def test_liquidate_fallback_price(self):
        self.firm.inventory = {"unknown": 10}
        self.firm.last_prices = {}
        # default price 10.0
        # 10 * 10.0 * 0.8 = 80.0

        self.mock_settlement.transfer.return_value = True
        self.handler.liquidate(self.firm, self.state)

        self.mock_settlement.transfer.assert_called_once_with(
            self.mock_public,
            self.firm,
            80.0,
            "Asset Liquidation (Inventory) - Firm 1",
            currency=DEFAULT_CURRENCY
        )
        self.assertEqual(self.firm.inventory, {})

    def test_liquidate_payment_fail(self):
        self.firm.inventory = {"apple": 10}
        self.firm.last_prices = {"apple": 5.0}

        self.mock_settlement.transfer.return_value = False

        self.handler.liquidate(self.firm, self.state)

        self.mock_settlement.transfer.assert_called_once()
        self.mock_public.receive_liquidated_assets.assert_not_called()
        # Inventory should NOT be cleared
        self.assertEqual(self.firm.inventory, {"apple": 10})

    def test_liquidate_no_public_manager(self):
        handler = InventoryLiquidationHandler(self.mock_settlement, None)
        self.firm.inventory = {"apple": 10}
        handler.liquidate(self.firm, self.state)
        self.mock_settlement.transfer.assert_not_called()

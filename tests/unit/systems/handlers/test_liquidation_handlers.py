import unittest
from unittest.mock import MagicMock, ANY
from simulation.systems.liquidation_handlers import InventoryLiquidationHandler
from modules.system.api import DEFAULT_CURRENCY, AssetBuyoutRequestDTO, AssetBuyoutResultDTO
from modules.system.constants import ID_PUBLIC_MANAGER
from simulation.dtos.api import SimulationState
from modules.simulation.api import IInventoryHandler, IConfigurable, LiquidationConfigDTO
from typing import Dict, Optional

class MockLiquidatableFirm(IInventoryHandler, IConfigurable):
    """
    Mock class that satisfies protocols for isinstance checks.
    We don't implement logic here, just structure for spec.
    """
    def get_liquidation_config(self) -> LiquidationConfigDTO: ...
    def add_item(self, item_id: str, quantity: float, transaction_id: Optional[str] = None, quality: float = 1.0) -> bool: ...
    def remove_item(self, item_id: str, quantity: float, transaction_id: Optional[str] = None) -> bool: ...
    def get_quantity(self, item_id: str) -> float: ...
    def get_quality(self, item_id: str) -> float: ...
    def get_all_items(self) -> Dict[str, float]: ...
    def clear_inventory(self) -> None: ...
    @property
    def id(self) -> int: return 1

class TestInventoryLiquidationHandler(unittest.TestCase):
    def setUp(self):
        self.mock_settlement = MagicMock()
        self.mock_public = MagicMock()
        self.handler = InventoryLiquidationHandler(self.mock_settlement, self.mock_public)

        # Use spec ensuring isinstance checks pass
        self.firm = MagicMock(spec=MockLiquidatableFirm)
        self.firm.id = 1

        self.state = MagicMock(spec=SimulationState)

    def test_liquidate_no_inventory(self):
        # Configure firm behavior
        self.firm.get_all_items.return_value = {}
        self.firm.get_liquidation_config.return_value = LiquidationConfigDTO(0.2, {}, 10.0, {})

        # Should not call execute_asset_buyout if no inventory?
        # The handler iterates items. If empty, loop doesn't run.
        # But wait, logic is:
        # prices_pennies = {}
        # for item in items: ...
        # request = AssetBuyoutRequestDTO(inventory=items, ...)
        # public.execute_asset_buyout(request)
        # So it IS called even with empty inventory?
        # Let's check logic:
        # request = AssetBuyoutRequestDTO(...)
        # result = public.execute_asset_buyout(request)

        # Configure mock return for safety
        self.mock_public.execute_asset_buyout.return_value = AssetBuyoutResultDTO(True, 0, {}, ID_PUBLIC_MANAGER)

        self.handler.liquidate(self.firm, self.state)

        # It might be called with empty inventory
        # But transfer should NOT happen because total_paid_pennies > 0 check.
        self.mock_settlement.transfer.assert_not_called()

    def test_liquidate_with_inventory(self):
        self.firm.get_all_items.return_value = {"apple": 10}
        self.firm.get_liquidation_config.return_value = LiquidationConfigDTO(
            haircut=0.2,
            initial_prices={},
            default_price=1000,
            market_prices={"apple": 500}
        )

        # Expected:
        # Request with inventory={"apple": 10}, market_prices={"apple": 500}, distress_discount=0.8
        # Result mock: total_paid=4000

        buyout_result = AssetBuyoutResultDTO(
            success=True,
            total_paid_pennies=4000,
            items_acquired={"apple": 10},
            buyer_id=ID_PUBLIC_MANAGER
        )
        self.mock_public.execute_asset_buyout.return_value = buyout_result
        self.mock_settlement.transfer.return_value = True

        self.handler.liquidate(self.firm, self.state)

        # Verify execute_asset_buyout called
        self.mock_public.execute_asset_buyout.assert_called_once()
        args, _ = self.mock_public.execute_asset_buyout.call_args
        request = args[0]
        self.assertEqual(request.inventory, {"apple": 10})
        self.assertEqual(request.market_prices, {"apple": 500})
        self.assertAlmostEqual(request.distress_discount, 0.8)

        # Verify Transfer
        self.mock_settlement.transfer.assert_called_once_with(
            self.mock_public,
            self.firm,
            4000,
            "Asset Liquidation (Inventory) - Agent 1",
            currency=DEFAULT_CURRENCY
        )

        # Check inventory is cleared
        self.firm.clear_inventory.assert_called_once()

    def test_liquidate_fallback_price(self):
        self.firm.get_all_items.return_value = {"unknown": 10}
        self.firm.get_liquidation_config.return_value = LiquidationConfigDTO(
            haircut=0.2,
            initial_prices={"unknown": 1000},
            default_price=1000,
            market_prices={}
        )

        buyout_result = AssetBuyoutResultDTO(
            success=True,
            total_paid_pennies=8000, # 10 * 1000 * 0.8
            items_acquired={"unknown": 10},
            buyer_id=ID_PUBLIC_MANAGER
        )
        self.mock_public.execute_asset_buyout.return_value = buyout_result
        self.mock_settlement.transfer.return_value = True

        self.handler.liquidate(self.firm, self.state)

        # Verify Request uses fallback price
        args, _ = self.mock_public.execute_asset_buyout.call_args
        request = args[0]
        self.assertEqual(request.market_prices, {"unknown": 1000})

        self.mock_settlement.transfer.assert_called_once_with(
            self.mock_public,
            self.firm,
            8000,
            "Asset Liquidation (Inventory) - Agent 1",
            currency=DEFAULT_CURRENCY
        )
        self.firm.clear_inventory.assert_called_once()

    def test_liquidate_payment_fail(self):
        self.firm.get_all_items.return_value = {"apple": 10}
        self.firm.get_liquidation_config.return_value = LiquidationConfigDTO(
            haircut=0.2,
            initial_prices={},
            default_price=1000,
            market_prices={"apple": 500}
        )

        buyout_result = AssetBuyoutResultDTO(
            success=True,
            total_paid_pennies=4000,
            items_acquired={"apple": 10},
            buyer_id=ID_PUBLIC_MANAGER
        )
        self.mock_public.execute_asset_buyout.return_value = buyout_result

        self.mock_settlement.transfer.return_value = False

        self.handler.liquidate(self.firm, self.state)

        self.mock_settlement.transfer.assert_called_once()
        # Inventory should NOT be cleared if payment fails
        self.firm.clear_inventory.assert_not_called()

    def test_liquidate_no_public_manager(self):
        handler = InventoryLiquidationHandler(self.mock_settlement, None)
        self.firm.get_all_items.return_value = {"apple": 10}
        handler.liquidate(self.firm, self.state)
        self.mock_settlement.transfer.assert_not_called()

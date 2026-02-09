import unittest
from unittest.mock import MagicMock
from simulation.systems.liquidation_handlers import InventoryLiquidationHandler
from modules.system.api import DEFAULT_CURRENCY
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

        self.handler.liquidate(self.firm, self.state)
        self.mock_settlement.transfer.assert_not_called()

    def test_liquidate_with_inventory(self):
        self.firm.get_all_items.return_value = {"apple": 10}
        self.firm.get_liquidation_config.return_value = LiquidationConfigDTO(
            haircut=0.2,
            initial_prices={},
            default_price=10.0,
            market_prices={"apple": 5.0}
        )

        # 10 * 5.0 * (1 - 0.2) = 50 * 0.8 = 40.0

        self.mock_settlement.transfer.return_value = True

        self.handler.liquidate(self.firm, self.state)

        self.mock_settlement.transfer.assert_called_once_with(
            self.mock_public,
            self.firm,
            40.0,
            "Asset Liquidation (Inventory) - Agent 1",
            currency=DEFAULT_CURRENCY
        )
        self.mock_public.receive_liquidated_assets.assert_called_once_with({"apple": 10})
        # Check inventory is cleared
        self.firm.clear_inventory.assert_called_once()

    def test_liquidate_fallback_price(self):
        self.firm.get_all_items.return_value = {"unknown": 10}
        self.firm.get_liquidation_config.return_value = LiquidationConfigDTO(
            haircut=0.2,
            initial_prices={"unknown": 10.0},
            default_price=10.0,
            market_prices={}
        )
        # default price 10.0
        # 10 * 10.0 * 0.8 = 80.0

        self.mock_settlement.transfer.return_value = True
        self.handler.liquidate(self.firm, self.state)

        self.mock_settlement.transfer.assert_called_once_with(
            self.mock_public,
            self.firm,
            80.0,
            "Asset Liquidation (Inventory) - Agent 1",
            currency=DEFAULT_CURRENCY
        )
        self.firm.clear_inventory.assert_called_once()

    def test_liquidate_payment_fail(self):
        self.firm.get_all_items.return_value = {"apple": 10}
        self.firm.get_liquidation_config.return_value = LiquidationConfigDTO(
            haircut=0.2,
            initial_prices={},
            default_price=10.0,
            market_prices={"apple": 5.0}
        )

        self.mock_settlement.transfer.return_value = False

        self.handler.liquidate(self.firm, self.state)

        self.mock_settlement.transfer.assert_called_once()
        self.mock_public.receive_liquidated_assets.assert_not_called()
        # Inventory should NOT be cleared
        self.firm.clear_inventory.assert_not_called()

    def test_liquidate_no_public_manager(self):
        handler = InventoryLiquidationHandler(self.mock_settlement, None)
        self.firm.get_all_items.return_value = {"apple": 10}
        handler.liquidate(self.firm, self.state)
        self.mock_settlement.transfer.assert_not_called()

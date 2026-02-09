from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, Any, Optional
import logging
from modules.system.api import DEFAULT_CURRENCY
from modules.finance.api import ILiquidatable
from modules.simulation.api import IInventoryHandler

if TYPE_CHECKING:
    from simulation.firms import Firm
    from simulation.dtos.api import SimulationState
    from simulation.finance.api import ISettlementSystem
    from modules.system.api import IAssetRecoverySystem

logger = logging.getLogger(__name__)

class ILiquidationHandler(ABC):
    """
    Interface for asset-specific liquidation logic.
    """
    @abstractmethod
    def liquidate(self, agent: ILiquidatable, state: SimulationState) -> None:
        """
        Liquidates specific assets of the firm to generate cash.
        """
        pass

class InventoryLiquidationHandler(ILiquidationHandler):
    """
    Liquidates firm inventory by selling to PublicManager.
    """
    def __init__(self, settlement_system: ISettlementSystem, public_manager: IAssetRecoverySystem):
        self.settlement_system = settlement_system
        self.public_manager = public_manager

    def liquidate(self, agent: ILiquidatable, state: SimulationState) -> None:
        """
        Liquidates non-cash assets (Inventory) by selling them to the PublicManager.
        This prevents the 'Asset-Rich Cash-Poor' leak.
        """
        if not self.public_manager:
            return

        # Check capability
        if not isinstance(agent, IInventoryHandler):
            return

        # We treat 'agent' as the entity with inventory (Firm)
        # We also need access to 'config' and 'last_prices' which are currently Firm-specific.
        # Ideally, we would have IPricingProvider or similar, but for now getattr is safe.
        firm = agent

        # Calculate Total Value
        total_value = 0.0

        # Use last prices or default config price from firm's config
        # Default price fallback: 10.0 if not found in config
        default_price = 10.0
        config = getattr(firm, "config", None)

        if config and hasattr(config, "goods_initial_price") and isinstance(config.goods_initial_price, dict):
             default_price = config.goods_initial_price.get("default", 10.0)

        # Configurable Haircut (Default 20%)
        haircut = getattr(config, "liquidation_haircut", 0.2) if config else 0.2

        inventory_transfer = {}
        # Iterate over a copy to allow modification if needed (though we only read keys/values here)
        # firm.inventory is a dict
        for item_id, qty in firm.get_all_items().items():
            if qty <= 0:
                continue

            # Determine fair value
            price = 0.0
            if hasattr(firm, "last_prices") and isinstance(firm.last_prices, dict):
                price = firm.last_prices.get(item_id, 0.0)

            if price <= 0:
                # Fallback to configured initial price if available
                if config and hasattr(config, "goods") and isinstance(config.goods, dict):
                     price = config.goods.get(item_id, {}).get("initial_price", default_price)
                else:
                     price = default_price

            # Apply Liquidation Discount (Haircut)
            liquidation_value = price * qty * (1.0 - haircut)
            total_value += liquidation_value
            inventory_transfer[item_id] = qty

        if total_value > 0:
            # Transfer Funds: PublicManager -> Firm
            # Note: PublicManager must implement IFinancialEntity to be a sender in SettlementSystem
            # and it must have funds (System Treasury).
            success = self.settlement_system.transfer(
                self.public_manager,
                firm,
                total_value,
                f"Asset Liquidation (Inventory) - Agent {firm.id}",
                currency=DEFAULT_CURRENCY
            )

            if success:
                logger.info(f"LIQUIDATION_ASSET_SALE | Agent {firm.id} sold inventory to PublicManager for {total_value:.2f}.")

                # Transfer Inventory via Interface (Encapsulation)
                self.public_manager.receive_liquidated_assets(inventory_transfer)

                # Clear Firm Inventory
                firm.clear_inventory()
            else:
                logger.error(f"LIQUIDATION_ASSET_SALE_FAIL | PublicManager failed to pay {total_value:.2f} to Agent {firm.id}.")

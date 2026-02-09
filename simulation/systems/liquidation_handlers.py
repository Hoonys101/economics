from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, Any, Optional
import logging
from modules.system.api import DEFAULT_CURRENCY
from modules.finance.api import ILiquidatable
from modules.simulation.api import IInventoryHandler, IConfigurable

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
        if not (isinstance(agent, IInventoryHandler) and isinstance(agent, IConfigurable)):
            return

        # Use Protocol Access
        liq_config = agent.get_liquidation_config()
        haircut = liq_config.haircut
        initial_prices = liq_config.initial_prices
        default_price = liq_config.default_price
        market_prices = liq_config.market_prices

        # Calculate Total Value
        total_value = 0.0

        inventory_transfer = {}
        # Iterate via Interface
        for item_id, qty in agent.get_all_items().items():
            if qty <= 0:
                continue

            # Determine fair value
            price = market_prices.get(item_id, 0.0)

            if price <= 0:
                # Fallback to configured initial price
                price = initial_prices.get(item_id, default_price)

            # Apply Liquidation Discount (Haircut)
            liquidation_value = price * qty * (1.0 - haircut)
            total_value += liquidation_value
            inventory_transfer[item_id] = qty

        if total_value > 0:
            # Transfer Funds: PublicManager -> Agent
            success = self.settlement_system.transfer(
                self.public_manager,
                agent,
                total_value,
                f"Asset Liquidation (Inventory) - Agent {agent.id}",
                currency=DEFAULT_CURRENCY
            )

            if success:
                logger.info(f"LIQUIDATION_ASSET_SALE | Agent {agent.id} sold inventory to PublicManager for {total_value:.2f}.")

                # Transfer Inventory via Interface (Encapsulation)
                self.public_manager.receive_liquidated_assets(inventory_transfer)

                # Clear Agent Inventory
                agent.clear_inventory()
            else:
                logger.error(f"LIQUIDATION_ASSET_SALE_FAIL | PublicManager failed to pay {total_value:.2f} to Agent {agent.id}.")

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, Any, Optional
import logging
from modules.system.api import DEFAULT_CURRENCY, AssetBuyoutRequestDTO
from modules.finance.api import ILiquidatable, ILiquidator
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

        # New Path: ILiquidator Mint-to-Buy
        if isinstance(self.public_manager, ILiquidator):
            # Delegate entirely to the Liquidator (PublicManager) via SettlementSystem
            # This allows PublicManager to Mint-to-Buy if funds are insufficient
            self.settlement_system.process_liquidation(
                self.public_manager,
                agent,
                agent.get_all_items().copy(),
                state.time
            )
            # The PublicManager updates its inventory and mints payment.
            # We must clear the agent's inventory here to reflect the transfer of custody.
            agent.clear_inventory()
            return

        # Legacy Path (Standard Transfer) - Fallback
        # Use Protocol Access
        liq_config = agent.get_liquidation_config()
        haircut = liq_config.haircut
        initial_prices = liq_config.initial_prices
        default_price = liq_config.default_price
        market_prices = liq_config.market_prices

        # Prepare Market Prices for DTO
        # Convert all prices to pennies int
        prices_pennies = {}
        for item_id in agent.get_all_items().keys():
            price = market_prices.get(item_id, 0.0)
            if price <= 0:
                price = initial_prices.get(item_id, default_price)
            prices_pennies[item_id] = int(price)

        # Execute Buyout
        # distress_discount is the multiplier (e.g. 0.8 for 20% haircut)
        request = AssetBuyoutRequestDTO(
            seller_id=agent.id,
            inventory=agent.get_all_items().copy(),
            market_prices=prices_pennies,
            distress_discount=1.0 - haircut
        )

        result = self.public_manager.execute_asset_buyout(request)

        if result.success and result.total_paid_pennies > 0:
            success = self.settlement_system.transfer(
                self.public_manager,
                agent,
                result.total_paid_pennies,
                f"Asset Liquidation (Inventory) - Agent {agent.id}",
                currency=DEFAULT_CURRENCY
            )

            if success:
                logger.info(f"LIQUIDATION_ASSET_SALE | Agent {agent.id} sold inventory to PublicManager for {result.total_paid_pennies}.")
                # Clear Agent Inventory
                agent.clear_inventory()
            else:
                logger.error(f"LIQUIDATION_ASSET_SALE_FAIL | PublicManager failed to pay {result.total_paid_pennies} to Agent {agent.id}.")

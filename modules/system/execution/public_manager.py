from __future__ import annotations
from typing import Dict, List, Any, Optional
import logging
from collections import defaultdict

from modules.system.api import IAssetRecoverySystem, AgentBankruptcyEventDTO, MarketSignalDTO, PublicManagerReportDTO
from modules.finance.api import IFinancialEntity, InsufficientFundsError
from simulation.models import Order

class PublicManager(IAssetRecoverySystem):
    """
    A system-level service responsible for asset recovery and liquidation.
    It acts as a 'Receiver' in bankruptcy proceedings, taking custody of assets
    and liquidating them back into the market to prevent value destruction.

    Implements IAssetRecoverySystem and IFinancialEntity (for atomic settlement).
    """

    def __init__(self, config: Any):
        self.config = config
        self._id: int = -1  # Unique integer ID for system entity
        self.managed_inventory: Dict[str, float] = defaultdict(float)
        self.system_treasury: float = 0.0
        self.logger = logging.getLogger("PublicManager")

        # Tracking for report (resets every tick or tracked cumulatively?)
        # For the report DTO, we likely want "current tick's activity".
        # But since get_status_report might be called anytime, we'll store cumulative or last tick data.
        self.last_tick_recovered_assets: Dict[str, float] = defaultdict(float)
        self.last_tick_revenue: float = 0.0
        self.total_revenue_lifetime: float = 0.0

    # --- IFinancialEntity Implementation ---
    @property
    def id(self) -> int:
        """Returns the unique integer ID for the PublicManager."""
        return self._id

    @property
    def assets(self) -> float:
        return self.system_treasury

    def deposit(self, amount: float) -> None:
        """Deposits funds (alias for deposit_revenue)."""
        self.deposit_revenue(amount)

    def withdraw(self, amount: float) -> None:
        """Withdraws funds from treasury."""
        if amount < 0:
            raise ValueError("Cannot withdraw negative amount.")
        if self.system_treasury < amount:
            raise InsufficientFundsError(f"PublicManager insufficient funds. Required: {amount}, Available: {self.system_treasury}")

        self.system_treasury -= amount
        # Note: withdrawals don't usually track 'revenue', so we don't update last_tick_revenue here.

    # --- IAssetRecoverySystem Implementation ---

    def process_bankruptcy_event(self, event: AgentBankruptcyEventDTO) -> None:
        """Takes ownership of a defunct agent's inventory."""
        # Reset tracking if this is a new tick?
        # Since this can be called multiple times per tick (multiple bankruptcies),
        # we should accumulate for the tick.
        # Ideally, we reset at the start of the tick. But PublicManager doesn't have a 'step' method.
        # We'll rely on generating the report or liquidation orders to reset tracking if needed.
        # For now, just accumulate.

        self.logger.warning(
            f"Processing bankruptcy for Agent {event['agent_id']} at tick {event['tick']}. "
            f"Recovering inventory."
        )
        for item_id, quantity in event['inventory'].items():
            if quantity > 0:
                self.managed_inventory[item_id] += quantity
                self.last_tick_recovered_assets[item_id] += quantity
                self.logger.info(f"Recovered {quantity} of {item_id}.")

    def receive_liquidated_assets(self, inventory: Dict[str, float]) -> None:
        """
        Receives inventory from a liquidated firm via asset buyout.
        Used by LiquidationManager during the 'Asset Liquidation' phase.
        """
        for item_id, quantity in inventory.items():
            if quantity > 0:
                self.managed_inventory[item_id] += quantity
                self.last_tick_recovered_assets[item_id] += quantity
        self.logger.info(f"Received liquidated assets: {inventory}")

    def generate_liquidation_orders(self, market_signals: Dict[str, MarketSignalDTO]) -> List[Order]:
        """
        Generates non-disruptive SELL orders for managed assets.
        This is typically called in Phase 4.5.
        """
        # We can reset "last tick" metrics here, assuming this starts the liquidation cycle for the tick.
        self.last_tick_recovered_assets = defaultdict(float)
        self.last_tick_revenue = 0.0

        orders: List[Order] = []
        items_to_liquidate = list(self.managed_inventory.items())

        # Config defaults
        sell_rate = getattr(self.config, "LIQUIDATION_SELL_RATE", 0.1)
        ask_undercut = getattr(self.config, "LIQUIDATION_ASK_UNDERCUT", 0.05)

        for item_id, quantity in items_to_liquidate:
            if quantity <= 0:
                continue

            market_signal = market_signals.get(item_id)
            if not market_signal:
                # No signal, maybe no market? Skip.
                continue

            best_ask = market_signal.best_ask

            # If no best_ask (no sellers), we need a reference price.
            # Using last_traded_price or config default.
            if best_ask is None or best_ask <= 0:
                best_ask = market_signal.last_traded_price

            if best_ask is None or best_ask <= 0:
                # Fallback to default goods price from config if available, or skip
                # We don't have easy access to GOODS_INITIAL_PRICE here unless in config.
                # Just skip to avoid dumping at 0.
                continue

            # Strategy: Sell a fraction of inventory at a slight discount to the best ask.
            sell_quantity = min(quantity, quantity * sell_rate)

            # Undercut the best ask price
            sell_price = best_ask * (1 - ask_undercut)

            if sell_price <= 0 or sell_quantity <= 0.001:
                continue

            order = Order(
                agent_id=self.id, # Use integer ID
                side="SELL",
                item_id=item_id,
                quantity=sell_quantity,
                price_limit=sell_price,
                market_id=item_id
            )
            orders.append(order)

            # We DO NOT decrement inventory here.
            # Inventory will be decremented in confirm_sale().
            self.logger.info(f"Generated liquidation order for {sell_quantity} of {item_id} at {sell_price}.")

        return orders

    def confirm_sale(self, item_id: str, quantity: float) -> None:
        """
        Confirms a sale transaction and permanently removes assets from inventory.
        Must be called by TransactionManager upon successful trade.
        """
        if item_id in self.managed_inventory:
            self.managed_inventory[item_id] = max(0.0, self.managed_inventory[item_id] - quantity)
            self.logger.debug(f"Confirmed sale of {quantity} {item_id}. Remaining: {self.managed_inventory[item_id]}")
        else:
            self.logger.warning(f"Confirmed sale for {item_id} but item not in managed inventory.")

    def deposit_revenue(self, amount: float) -> None:
        """Deposits revenue from liquidation sales into the system treasury."""
        self.system_treasury += amount
        self.last_tick_revenue += amount
        self.total_revenue_lifetime += amount

    def get_status_report(self) -> PublicManagerReportDTO:
        return PublicManagerReportDTO(
            tick=0, # Placeholder, caller usually knows tick
            newly_recovered_assets=dict(self.last_tick_recovered_assets),
            liquidation_revenue=self.last_tick_revenue,
            managed_inventory_count=sum(self.managed_inventory.values()),
            system_treasury_balance=self.system_treasury
        )

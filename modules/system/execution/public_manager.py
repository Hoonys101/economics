from __future__ import annotations
from typing import Dict, List, Any, Optional
import logging
from collections import defaultdict
from modules.system.api import IAssetRecoverySystem, AgentBankruptcyEventDTO, MarketSignalDTO, PublicManagerReportDTO, CurrencyCode, DEFAULT_CURRENCY, ICurrencyHolder
from modules.finance.api import IFinancialAgent, InsufficientFundsError
from modules.system.constants import ID_PUBLIC_MANAGER
from simulation.models import Order

class PublicManager(IAssetRecoverySystem, ICurrencyHolder, IFinancialAgent):
    """
    A system-level service responsible for asset recovery and liquidation.
    It acts as a 'Receiver' in bankruptcy proceedings, taking custody of assets
    and liquidating them back into the market to prevent value destruction.

    Implements IAssetRecoverySystem and IFinancialAgent (for atomic settlement).
    """

    def __init__(self, config: Any):
        self._id = ID_PUBLIC_MANAGER
        self.config = config
        self.logger = logging.getLogger('PublicManager')
        self.managed_inventory: Dict[str, float] = defaultdict(float)
        self.system_treasury: Dict[CurrencyCode, int] = {DEFAULT_CURRENCY: 0}
        self.logger = logging.getLogger('PublicManager')
        self.last_tick_recovered_assets: Dict[str, float] = defaultdict(float)
        self.last_tick_revenue: Dict[CurrencyCode, int] = {DEFAULT_CURRENCY: 0}
        self.total_revenue_lifetime: Dict[CurrencyCode, int] = {DEFAULT_CURRENCY: 0}

    @property
    def id(self) -> int:
        """Returns the unique integer ID for the PublicManager."""
        return self._id

    def _deposit(self, amount: int, currency: CurrencyCode=DEFAULT_CURRENCY) -> None:
        """Deposits funds (internal use)."""
        if amount < 0:
            self.logger.error(f'Negative deposit attempted: {amount}')
            return
        self.deposit_revenue(amount, currency=currency)

    def _withdraw(self, amount: int, currency: CurrencyCode=DEFAULT_CURRENCY) -> None:
        """Withdraws funds from treasury."""
        if amount < 0:
            raise ValueError('Cannot withdraw negative amount.')
        current_bal = self.system_treasury.get(currency, 0)
        if current_bal < amount:
            raise InsufficientFundsError(f'PublicManager insufficient funds. Required: {amount} {currency}, Available: {current_bal}')
        self.system_treasury[currency] -= amount

    def get_balance(self, currency: CurrencyCode=DEFAULT_CURRENCY) -> int:
        """Returns the current balance for the specified currency."""
        return self.system_treasury.get(currency, 0)

    def get_all_balances(self) -> Dict[CurrencyCode, int]:
        """Returns a copy of all currency balances."""
        return self.system_treasury.copy()

    @property
    def total_wealth(self) -> int:
        """Returns the total wealth in default currency estimation."""
        return sum(self.system_treasury.values())

    def get_assets_by_currency(self) -> Dict[CurrencyCode, int]:
        """Implementation of ICurrencyHolder."""
        return self.system_treasury.copy()

    def process_bankruptcy_event(self, event: AgentBankruptcyEventDTO) -> None:
        """Takes ownership of a defunct agent's inventory."""
        self.logger.warning(f"Processing bankruptcy for Agent {event['agent_id']} at tick {event['tick']}. Recovering inventory.")
        for item_id, quantity in event['inventory'].items():
            if quantity > 0:
                self.managed_inventory[item_id] += quantity
                self.last_tick_recovered_assets[item_id] += quantity
                self.logger.info(f'Recovered {quantity} of {item_id}.')

    def receive_liquidated_assets(self, inventory: Dict[str, float]) -> None:
        """
        Receives inventory from a liquidated firm via asset buyout.
        Used by LiquidationManager during the 'Asset Liquidation' phase.
        """
        for item_id, quantity in inventory.items():
            if quantity > 0:
                self.managed_inventory[item_id] += quantity
                self.last_tick_recovered_assets[item_id] += quantity
        self.logger.info(f'Received liquidated assets: {inventory}')

    def generate_liquidation_orders(self, market_signals: Dict[str, MarketSignalDTO], core_config: Any=None, engine: Any=None) -> List[Order]:
        """
        Generates non-disruptive SELL orders for managed assets.
        This is typically called in Phase 4.5.
        """
        self.last_tick_recovered_assets = defaultdict(float)
        self.last_tick_revenue = {DEFAULT_CURRENCY: 0}
        orders: List[Order] = []
        items_to_liquidate = list(self.managed_inventory.items())
        sell_rate = getattr(self.config, 'LIQUIDATION_SELL_RATE', 0.1)
        ask_undercut = getattr(self.config, 'LIQUIDATION_ASK_UNDERCUT', 0.05)
        for item_id, quantity in items_to_liquidate:
            if quantity <= 0:
                continue
            market_signal = market_signals.get(item_id)
            if not market_signal:
                continue
            best_ask = market_signal.best_ask
            if best_ask is None or best_ask <= 0:
                best_ask = market_signal.last_traded_price
            if best_ask is None or best_ask <= 0:
                continue
            sell_quantity = min(quantity, quantity * sell_rate)
            sell_price = best_ask * (1 - ask_undercut)
            if sell_price <= 0 or sell_quantity <= 0.001:
                continue
            order = Order(agent_id=self.id, side='SELL', item_id=item_id, quantity=sell_quantity, price_pennies=int(sell_price * 100), price_limit=sell_price, market_id=item_id)
            orders.append(order)
            self.logger.info(f'Generated liquidation order for {sell_quantity} of {item_id} at {sell_price}.')
        return orders

    def confirm_sale(self, item_id: str, quantity: float) -> None:
        """
        Confirms a sale transaction and permanently removes assets from inventory.
        Must be called by TransactionManager upon successful trade.
        """
        if item_id in self.managed_inventory:
            self.managed_inventory[item_id] = max(0.0, self.managed_inventory[item_id] - quantity)
            self.logger.debug(f'Confirmed sale of {quantity} {item_id}. Remaining: {self.managed_inventory[item_id]}')
        else:
            self.logger.warning(f'Confirmed sale for {item_id} but item not in managed inventory.')

    def deposit_revenue(self, amount: int, currency: CurrencyCode=DEFAULT_CURRENCY) -> None:
        """Deposits revenue from liquidation sales into the system treasury."""
        if currency not in self.system_treasury:
            self.system_treasury[currency] = 0
        if currency not in self.last_tick_revenue:
            self.last_tick_revenue[currency] = 0
        if currency not in self.total_revenue_lifetime:
            self.total_revenue_lifetime[currency] = 0
        self.system_treasury[currency] += amount
        self.last_tick_revenue[currency] += amount
        self.total_revenue_lifetime[currency] += amount

    def get_status_report(self) -> PublicManagerReportDTO:
        return PublicManagerReportDTO(tick=0, newly_recovered_assets=dict(self.last_tick_recovered_assets), liquidation_revenue=self.last_tick_revenue, managed_inventory_count=sum(self.managed_inventory.values()), system_treasury_balance=self.system_treasury)
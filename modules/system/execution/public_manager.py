from __future__ import annotations
from typing import Dict, List, Any, Optional
import logging
from collections import defaultdict
from modules.system.api import (
    IAssetRecoverySystem, AgentBankruptcyEventDTO, MarketSignalDTO,
    PublicManagerReportDTO, CurrencyCode, DEFAULT_CURRENCY, ICurrencyHolder,
    AssetBuyoutRequestDTO, AssetBuyoutResultDTO, ISystemFinancialAgent, IAgentRegistry
)
from modules.finance.api import IFinancialAgent, InsufficientFundsError, ILiquidator, ISettlementSystem
from modules.simulation.api import IInventoryHandler, IConfigurable
from modules.system.constants import ID_PUBLIC_MANAGER
from simulation.models import Order

class PublicManager(IAssetRecoverySystem, ILiquidator, ICurrencyHolder, IFinancialAgent, ISystemFinancialAgent):
    """
    A system-level service responsible for asset recovery and liquidation.
    It acts as a 'Receiver' in bankruptcy proceedings, taking custody of assets
    and liquidating them back into the market to prevent value destruction.

    Implements IAssetRecoverySystem, ILiquidator, and IFinancialAgent.
    """

    def __init__(self, config: Any):
        self._id = ID_PUBLIC_MANAGER
        self.config = config
        self.logger = logging.getLogger('PublicManager')
        self.managed_inventory: Dict[str, float] = defaultdict(float)
        self.system_treasury: Dict[CurrencyCode, int] = {DEFAULT_CURRENCY: 0}
        self.settlement_system: Optional[ISettlementSystem] = None
        self.agent_registry: Optional[IAgentRegistry] = None
        self.last_tick_recovered_assets: Dict[str, float] = defaultdict(float)
        self.last_tick_revenue: Dict[CurrencyCode, int] = {DEFAULT_CURRENCY: 0}
        self.total_revenue_lifetime: Dict[CurrencyCode, int] = {DEFAULT_CURRENCY: 0}
        self.cumulative_deficit: int = 0

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

    def is_system_agent(self) -> bool:
        """Marker for SettlementSystem to allow overdraft (Soft Budget Constraint)."""
        return True

    def _withdraw(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """
        Withdraws funds from treasury.
        MIGRATION: Soft Budget Constraint - Allows negative balance.
        """
        if amount < 0:
            raise ValueError('Cannot withdraw negative amount.')

        current_bal = self.system_treasury.get(currency, 0)

        # Calculate deficit increase (money created via overdraft)
        deficit_increase = 0
        if current_bal < 0:
            deficit_increase = amount
        elif current_bal < amount:
            deficit_increase = amount - current_bal

        if deficit_increase > 0:
            self.cumulative_deficit += deficit_increase

        # Allow negative balance
        self.system_treasury[currency] = current_bal - amount

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

    # --- IFinancialEntity Implementation ---
    @property
    def balance_pennies(self) -> int:
        return self.get_balance(DEFAULT_CURRENCY)

    def deposit(self, amount_pennies: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self._deposit(amount_pennies, currency)

    def withdraw(self, amount_pennies: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self._withdraw(amount_pennies, currency)

    # --- IFinancialAgent Implementation ---
    def get_liquid_assets(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        return self.get_balance(currency)

    def get_total_debt(self) -> int:
        return 0

    def process_bankruptcy_event(self, event: AgentBankruptcyEventDTO) -> None:
        """Takes ownership of a defunct agent's inventory."""
        self.logger.warning(f"Processing bankruptcy for Agent {event['agent_id']} at tick {event['tick']}. Recovering inventory.")
        for item_id, quantity in event['inventory'].items():
            if quantity > 0:
                self.managed_inventory[item_id] += quantity
                self.last_tick_recovered_assets[item_id] += quantity
                self.logger.info(f'Recovered {quantity} of {item_id}.')

    def execute_asset_buyout(self, request: AssetBuyoutRequestDTO) -> AssetBuyoutResultDTO:
        """
        Purchases assets from a distressed agent.
        Updates internal inventory state but does NOT move funds (caller must execute transfer).
        """
        total_value = 0
        acquired_items = {}

        for item_id, quantity in request.inventory.items():
            if quantity <= 0:
                continue
            price = request.market_prices.get(item_id, 0)
            value = int(price * quantity * request.distress_discount)
            total_value += value
            acquired_items[item_id] = quantity

            # Update inventory immediately
            self.managed_inventory[item_id] += quantity
            self.last_tick_recovered_assets[item_id] += quantity

        self.logger.info(f"Executed Asset Buyout from Agent {request.seller_id}. Paid: {total_value}, Items: {len(acquired_items)}")

        return AssetBuyoutResultDTO(
            success=True,
            total_paid_pennies=total_value,
            items_acquired=acquired_items,
            buyer_id=self.id
        )

    def rollback_asset_buyout(self, request: AssetBuyoutRequestDTO) -> bool:
        """
        Reverses an asset buyout by returning assets from PublicManager's inventory.
        Also reclaims the currency paid.
        """
        total_value = 0
        returned_items = {}

        # 1. Calculate and reverse inventory
        for item_id, quantity in request.inventory.items():
            if quantity <= 0:
                continue

            # Check if we actually have enough in managed inventory to return (Safety)
            current_pm_qty = self.managed_inventory.get(item_id, 0.0)
            qty_to_return = min(quantity, current_pm_qty)

            if qty_to_return > 0:
                self.managed_inventory[item_id] = current_pm_qty - qty_to_return
                returned_items[item_id] = qty_to_return

                # Reverse transient tracking if possible
                if item_id in self.last_tick_recovered_assets:
                     self.last_tick_recovered_assets[item_id] = max(0.0, self.last_tick_recovered_assets[item_id] - qty_to_return)

            # Calculate valuation for currency reversal
            price = request.market_prices.get(item_id, 0)
            value = int(price * quantity * request.distress_discount)
            total_value += value

        # 2. Re-distribute assets to seller if they exist
        if self.agent_registry and returned_items:
             seller = self.agent_registry.get_agent(request.seller_id)
             if seller and isinstance(seller, IInventoryHandler):
                  for item_id, qty in returned_items.items():
                       seller.add_item(item_id, qty, reason="ROLLBACK_BAILOUT")
                  self.logger.info(f"Returned {len(returned_items)} items to Seller {request.seller_id}")

        # 3. Currency Reversal (Seller -> PublicManager)
        if self.settlement_system and total_value > 0:
             seller = None
             if self.agent_registry:
                  seller = self.agent_registry.get_agent(request.seller_id)

             if seller and isinstance(seller, IFinancialAgent):
                  success = self.settlement_system.transfer(
                       debit_agent=seller,
                       credit_agent=self,
                       amount=total_value,
                       memo="ROLLBACK_BAILOUT_RECLAIM",
                       currency=DEFAULT_CURRENCY
                  )
                  if success:
                       # Reverse cumulative deficit
                       self.cumulative_deficit = max(0, self.cumulative_deficit - total_value)
                       self.logger.info(f"Reclaimed {total_value} pennies from Agent {request.seller_id}")
                  else:
                       self.logger.warning(f"Failed to reclaim {total_value} pennies from Agent {request.seller_id} during rollback.")

        self.logger.info(f"Rolled back Asset Buyout from Agent {request.seller_id}. Total Value: {total_value}")
        return True

    def set_agent_registry(self, registry: IAgentRegistry) -> None:
        """Injects the Agent Registry for lookups during rollback."""
        self.agent_registry = registry

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

    def get_deficit(self) -> int:
        return self.cumulative_deficit

    def get_status_report(self) -> PublicManagerReportDTO:
        return PublicManagerReportDTO(
            tick=0,
            newly_recovered_assets=dict(self.last_tick_recovered_assets),
            liquidation_revenue=self.last_tick_revenue,
            managed_inventory_count=sum(self.managed_inventory.values()),
            system_treasury_balance=self.system_treasury,
            cumulative_deficit=self.cumulative_deficit
        )

    def set_settlement_system(self, system: ISettlementSystem) -> None:
        """Injects the SettlementSystem dependency for Mint-to-Buy operations."""
        self.settlement_system = system

    def liquidate_assets(self, bankrupt_agent: IFinancialAgent, assets: Any, tick: int) -> None:
        """
        Implementation of ILiquidator.
        Performs "Mint-to-Buy" asset recovery:
        1. Valuates assets using agent configuration.
        2. Takes custody of assets (Inventory Update).
        3. Mints new money to pay the bankrupt agent (Liquidity Injection).
        """
        if not self.settlement_system:
            self.logger.error("LIQUIDATION_FAIL | SettlementSystem not injected into PublicManager.")
            return

        # 1. Valuation Logic
        # Default fallback values if configuration is missing
        haircut = 0.2
        initial_prices = {}
        default_price = 10.0
        market_prices = {}

        # Attempt to retrieve configuration from the agent
        if isinstance(bankrupt_agent, IConfigurable):
            try:
                liq_config = bankrupt_agent.get_liquidation_config()
                haircut = liq_config.haircut
                initial_prices = liq_config.initial_prices
                default_price = liq_config.default_price
                market_prices = liq_config.market_prices
            except Exception as e:
                self.logger.warning(f"Failed to retrieve liquidation config from Agent {bankrupt_agent.id}: {e}")

        # Calculate valuations in pennies
        prices_pennies = {}
        inventory_assets = assets if isinstance(assets, dict) else {}

        for item_id in inventory_assets.keys():
            price = market_prices.get(item_id, 0.0)
            if price <= 0:
                price = initial_prices.get(item_id, default_price)
            prices_pennies[item_id] = int(price)

        # 2. Asset Buyout (Inventory Update)
        # Construct Request
        request = AssetBuyoutRequestDTO(
            seller_id=bankrupt_agent.id,
            inventory=inventory_assets.copy(),
            market_prices=prices_pennies,
            distress_discount=1.0 - haircut
        )

        # Execute internal inventory update (No funds moved yet)
        result = self.execute_asset_buyout(request)

        # 3. Liquidity Injection (Mint-to-Buy)
        if result.success and result.total_paid_pennies > 0:
            tx = self.settlement_system.create_and_transfer(
                source_authority=self,
                destination=bankrupt_agent,
                amount=result.total_paid_pennies,
                reason="LIQUIDATION_BAILOUT",
                tick=tick,
                currency=DEFAULT_CURRENCY
            )

            if tx:
                # Update accounting for bailout cost (Deficit Spending)
                self.cumulative_deficit += result.total_paid_pennies
                self.logger.info(f"LIQUIDATION_BAILOUT | PublicManager minted {result.total_paid_pennies} to buy assets from Agent {bankrupt_agent.id}.")
            else:
                self.logger.error(f"LIQUIDATION_BAILOUT_FAIL | Failed to mint transfer for Agent {bankrupt_agent.id}.")
from __future__ import annotations
from typing import List, Any, Optional, Union, TYPE_CHECKING
import logging
from simulation.systems.lifecycle.api import IDeathSystem, DeathConfigDTO, IDeathContext
from modules.finance.api import ILiquidatable, IShareholderRegistry, IFinancialEntity
from modules.system.api import IAssetRecoverySystem, ICurrencyHolder, DEFAULT_CURRENCY, AssetBuyoutRequestDTO
from simulation.interfaces.market_interface import IMarket
from modules.simulation.api import IEstateRegistry

from simulation.models import Transaction
if TYPE_CHECKING:
    from simulation.dtos.api import SimulationState
    from simulation.systems.inheritance_manager import InheritanceManager
    from simulation.systems.liquidation_manager import LiquidationManager
    from simulation.finance.api import ISettlementSystem

class DeathSystem(IDeathSystem):
    """
    Handles agent death, liquidation of assets, and inheritance processing.
    Refactored for Protocol Purity and Integer Math.
    """
    def __init__(self, config: DeathConfigDTO,
                 inheritance_manager: InheritanceManager,
                 liquidation_manager: LiquidationManager,
                 settlement_system: ISettlementSystem,
                 public_manager: IAssetRecoverySystem,
                 logger: logging.Logger,
                 estate_registry: Optional[IEstateRegistry] = None):
        self.config = config
        self.inheritance_manager = inheritance_manager
        self.liquidation_manager = liquidation_manager
        self.settlement_system = settlement_system
        self.public_manager = public_manager
        self.logger = logger
        self.estate_registry = estate_registry

    def execute(self, context: IDeathContext) -> List[Transaction]:
        """
        Executes the death phase.
        1. Firm Liquidation (Bankruptcy)
        2. Household Liquidation (Death & Inheritance)
        """
        if not isinstance(context, IDeathContext):
            raise TypeError(f"Expected IDeathContext, got {type(context)}")

        return self._handle_agent_liquidation(context)

    def _handle_agent_liquidation(self, context: IDeathContext) -> List[Transaction]:
        transactions: List[Transaction] = []

        # --- Firm Liquidation ---
        # Identify inactive firms
        inactive_firms = [f for f in context.firms if not f.is_active]

        for firm in inactive_firms:
            # 0. Cancel Orders (Atomicity Fix)
            self._cancel_agent_orders(firm.id, context)

            # 0.5 Recover External Assets (Bank Deposits)
            self._recover_external_assets(firm.id, context, transactions)

            # Delegate strictly to LiquidationManager
            if isinstance(firm, ILiquidatable):
                 # Pass context instead of state (duck typing)
                 self.liquidation_manager.initiate_liquidation(firm, context)

            # Post-Liquidation Cleanup
            # 1. Employees (HR)
            if hasattr(firm, 'hr_state'):
                for employee in firm.hr_state.employees:
                    # Using property or direct access if needed
                    # IOrchestratorAgent usually has is_active, but here we want is_employed
                    # Assuming Employee object or Household agent
                    if hasattr(employee, 'is_employed'):
                        employee.is_employed = False
                        employee.employer_id = None
                firm.hr_state.employees = []

            # 2. Currency Registry
            if isinstance(firm, ICurrencyHolder):
                if context.currency_registry_handler:
                    context.currency_registry_handler.unregister_currency_holder(firm)
                elif context.currency_holders is not None:
                     if firm in context.currency_holders:
                         context.currency_holders.remove(firm)

            # 3. Settlement Index
            if self.settlement_system:
                self.settlement_system.remove_agent_from_all_accounts(firm.id)

        # --- Household Liquidation ---
        # Use property is_active (from IOrchestratorAgent/Household)
        inactive_households = [h for h in context.households if not h.is_active]

        for household in inactive_households:
             # 0. Cancel Orders (Atomicity Fix)
             self._cancel_agent_orders(household.id, context)

             # 0.5 Recover External Assets (Bank Deposits)
             self._recover_external_assets(household.id, context, transactions)

             # Preserve for history/logging if needed
             if context.inactive_agents is not None:
                 context.inactive_agents[household.id] = household

             # Inventory Liquidation (Asset Buyout) via Public Manager
             # Must occur BEFORE inheritance so cash is available for heirs/tax.
             self._liquidate_agent_inventory(household, context, transactions)

             # Inheritance Manager (Executes transactions via side-effects)
             if context.primary_government:
                  # Pass context instead of state (duck typing)
                  inheritance_txs = self.inheritance_manager.process_death(household, context.primary_government, context)
                  transactions.extend(inheritance_txs)

             # Cleanup
             if isinstance(household, ICurrencyHolder):
                if context.currency_registry_handler:
                    context.currency_registry_handler.unregister_currency_holder(household)
                elif context.currency_holders is not None:
                     if household in context.currency_holders:
                         context.currency_holders.remove(household)

             if self.settlement_system:
                self.settlement_system.remove_agent_from_all_accounts(household.id)

        # --- Global List Cleanup ---

        # O(1) Dictionary Cleanup - TD-SYS-PERF-DEATH
        for firm in inactive_firms:
            self._decommission_agent(firm, context)

        for household in inactive_households:
            self._decommission_agent(household, context)

        # Modify lists in place to reflect removals
        context.households[:] = [h for h in context.households if h.is_active]
        context.firms[:] = [f for f in context.firms if f.is_active]

        return transactions

    def _decommission_agent(self, agent: Any, context: IDeathContext) -> None:
        """
        Standardized Decommission: Moves agent to estate and removes from global map.
        Note: List removal (households/firms) is handled in bulk for performance.
        """
        if self.estate_registry:
            self.estate_registry.add_to_estate(agent)

        if agent.id in context.agents:
            del context.agents[agent.id]

    def _recover_external_assets(self, agent_id: int, context: IDeathContext, transactions: List[Transaction]) -> None:
        """
        Recovers assets from external accounts (Banks) before liquidation.
        """
        if not self.settlement_system: return

        # 1. Find Banks using new API
        if hasattr(self.settlement_system, 'get_agent_banks'):
            bank_ids = self.settlement_system.get_agent_banks(agent_id)
        else:
            return

        agent = context.agents.get(agent_id)
        if not agent: return

        for bank_id in bank_ids:
            # 2. Close Account safely via Settlement Transfer
            bank = context.agents.get(bank_id)
            if not bank: continue

            # Check for protocol compliance
            if hasattr(bank, 'get_customer_balance') and hasattr(bank, 'close_account'):
                amount = bank.get_customer_balance(agent_id)
                if amount > 0:
                    # 3. Transfer Real Assets (Cash) from Bank to Agent
                    # Use SettlementSystem to ensure Zero-Sum Integrity (Bank loses Cash, Agent gains Cash)
                    success = self.settlement_system.transfer(
                        debit_agent=bank,
                        credit_agent=agent,
                        amount=amount,
                        memo="Deposit Recovery (Death/Liquidation)",
                        currency=DEFAULT_CURRENCY
                    )

                    if success:
                        # 4. Close the Ledger Account (Remove Liability)
                        bank.close_account(agent_id)

                        # WO-IMPL-LEDGER-HARDENING: Emit Transaction
                        tx = Transaction(
                            buyer_id=bank.id,
                            seller_id=agent.id,
                            item_id=f"deposit_recovery_{agent_id}",
                            quantity=1,
                            price=amount / 100.0,
                            market_id="financial",
                            transaction_type="withdrawal", # Or 'asset_recovery'
                            time=context.time,
                            total_pennies=amount,
                            metadata={"executed": True, "reason": "liquidation_recovery"}
                        )
                        transactions.append(tx)

                        self.logger.info(f"RECOVER_ASSETS | Recovered {amount} from Bank {bank_id} for Agent {agent_id}")
                    else:
                        self.logger.error(f"RECOVER_FAIL | Bank {bank_id} insolvent? Could not return {amount} to {agent_id}")

    def _cancel_agent_orders(self, agent_id: str | int, context: IDeathContext) -> None:
        """
        Scrub agent orders from all markets to ensure atomicity.
        """
        if not context.markets:
            return

        for market in context.markets.values():
            # Check for cancel_orders method (Protocol compliance)
            if isinstance(market, IMarket):
                try:
                    market.cancel_orders(agent_id)
                except Exception as e:
                    self.logger.error(
                        f"ORDER_SCRUB_FAIL | Failed to cancel orders for agent {agent_id} in market {getattr(market, 'id', 'unknown')}: {e}"
                    )

    def _liquidate_agent_inventory(self, agent: Any, context: IDeathContext, transactions: List[Transaction]) -> None:
        """
        Liquidates agent inventory by selling to Public Manager (Asset Buyout).
        Transfers cash to the agent and clears inventory.
        """
        if not self.public_manager or not self.settlement_system:
            return

        inventory = None
        if hasattr(agent, 'inventory'):
             inventory = agent.inventory
        elif hasattr(agent, '_econ_state'):
             inventory = agent._econ_state.inventory

        if not inventory or not isinstance(inventory, dict) or len(inventory) == 0:
            return

        # Prepare Market Prices
        market_prices = {}
        # Simple Logic: Get price from market or default
        default_price_pennies = self.config.default_fallback_price_pennies

        for item_id in inventory.keys():
             price_pennies = default_price_pennies
             # Try to get market price
             if context.markets:
                 if item_id in context.markets:
                     m = context.markets[item_id]
                     if isinstance(m, IMarket):
                         try:
                            p = m.get_price(item_id)
                            if p > 0: price_pennies = int(p * 100)
                         except: pass
                 elif "goods_market" in context.markets: # Fallback to aggregate market
                     m = context.markets["goods_market"]
                     if isinstance(m, IMarket):
                         try:
                            p = m.get_price(item_id)
                            if p > 0: price_pennies = int(p * 100)
                         except: pass

             market_prices[item_id] = price_pennies

        # Execute Buyout
        request = AssetBuyoutRequestDTO(
            seller_id=agent.id,
            inventory=inventory.copy(),
            market_prices=market_prices,
            distress_discount=0.5 # Default distress discount for death/forced sale
        )

        result = self.public_manager.execute_asset_buyout(request)

        if result.success and result.total_paid_pennies > 0:
            # Transfer Cash: PM -> Agent
            success = self.settlement_system.transfer(
                self.public_manager,
                agent,
                result.total_paid_pennies,
                f"Asset Buyout (Death) - Agent {agent.id}",
                currency=DEFAULT_CURRENCY
            )

            if success:
                # WO-IMPL-LEDGER-HARDENING: Emit Transaction
                tx = Transaction(
                    buyer_id=self.public_manager.id if hasattr(self.public_manager, 'id') else "PUBLIC_MANAGER",
                    seller_id=agent.id,
                    item_id=f"asset_buyout_{agent.id}",
                    quantity=1,
                    price=result.total_paid_pennies / 100.0,
                    market_id="financial",
                    transaction_type="asset_buyout",
                    time=context.time,
                    total_pennies=result.total_paid_pennies,
                    metadata={"executed": True}
                )
                transactions.append(tx)

                self.logger.info(f"ASSET_BUYOUT_SUCCESS | Agent {agent.id} sold inventory for {result.total_paid_pennies} pennies.")
                # Clear Inventory
                if hasattr(agent, 'clear_inventory'):
                     agent.clear_inventory()
                elif hasattr(inventory, 'clear'):
                     inventory.clear()
            else:
                 self.logger.error(f"ASSET_BUYOUT_FAIL | Payment failed for Agent {agent.id}")

    def _calculate_inventory_value(self, inventory: dict, markets: dict) -> int:
        """
        Calculates total inventory value in integer pennies.
        """
        total_pennies = 0
        default_price_pennies = self.config.default_fallback_price_pennies

        for item_id, qty in inventory.items():
            price_pennies = default_price_pennies
            # 1. Check Markets
            if item_id in markets:
                m = markets[item_id]
                if isinstance(m, IMarket):
                    try:
                        p_float = m.get_price(item_id)
                        if p_float > 0:
                            price_pennies = int(p_float * 100)
                    except: pass
            elif "goods_market" in markets:
                 m = markets["goods_market"]
                 if isinstance(m, IMarket):
                     try:
                        p_float = m.get_price(item_id)
                        if p_float > 0:
                            price_pennies = int(p_float * 100)
                     except: pass

            total_pennies += int(qty * price_pennies)
        return total_pennies

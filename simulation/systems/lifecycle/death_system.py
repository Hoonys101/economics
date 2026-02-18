from __future__ import annotations
from typing import List, Any
import logging
from simulation.systems.lifecycle.api import IDeathSystem
from simulation.dtos.api import SimulationState
from simulation.models import Transaction
from simulation.systems.inheritance_manager import InheritanceManager
from simulation.systems.liquidation_manager import LiquidationManager
from simulation.finance.api import ISettlementSystem
from modules.system.api import IAssetRecoverySystem, ICurrencyHolder
from simulation.interfaces.market_interface import IMarket
from modules.finance.api import IShareholderRegistry, IFinancialEntity

class DeathSystem(IDeathSystem):
    """
    Handles agent death, liquidation of assets, and inheritance processing.
    """
    def __init__(self, config_module: Any,
                 inheritance_manager: InheritanceManager,
                 liquidation_manager: LiquidationManager,
                 settlement_system: ISettlementSystem,
                 public_manager: IAssetRecoverySystem,
                 logger: logging.Logger):
        self.config = config_module
        self.inheritance_manager = inheritance_manager
        self.liquidation_manager = liquidation_manager
        self.settlement_system = settlement_system
        self.public_manager = public_manager
        self.logger = logger

    def execute(self, state: SimulationState) -> List[Transaction]:
        """
        Executes the death phase.
        1. Firm Liquidation (Bankruptcy)
        2. Household Liquidation (Death & Inheritance)
        3. Global list cleanup
        """
        return self._handle_agent_liquidation(state)

    def _handle_agent_liquidation(self, state: SimulationState) -> List[Transaction]:
        """
        Handles liquidation of inactive firms and households.
        Returns a list of transactions (specifically from Inheritance).
        """
        transactions: List[Transaction] = []

        # --- Firm Liquidation ---
        inactive_firms = [f for f in state.firms if not f.is_active]
        for firm in inactive_firms:
            self.logger.info(
                f"FIRM_LIQUIDATION | Starting liquidation for Firm {firm.id}.",
                extra={"agent_id": firm.id, "tags": ["liquidation"]}
            )

            inv_value = self._calculate_inventory_value(firm.get_all_items(), state.markets)
            capital_value = firm.capital_stock

            # TD-187: Liquidation Waterfall Protocol (Prioritized Claims)
            # Must run BEFORE employees are cleared to calculate severance/wages
            # AND before PublicManager seizure (now handled internally by LiquidationManager)
            # WO-212: initiate_liquidation now handles "Firm Write-offs" (Inventory, Capital Stock) atomically.
            self.liquidation_manager.initiate_liquidation(firm, state)

            # Clear employees
            for employee in firm.hr_state.employees:
                if employee.is_active:
                    employee.is_employed = False
                    employee.employer_id = None
            firm.hr_state.employees = []
            # firm.inventory and firm.capital_stock are cleared in initiate_liquidation -> firm.liquidate_assets

            # Record Liquidation (Destruction of real assets & Escheatment)
            # Only Capital Stock is destroyed now (machines, buildings), inventory is recovered.
            # WO-178: record_liquidation now handles escheatment of residual assets (after dividends) to government.
            government = getattr(state, "government", None)

            self.settlement_system.record_liquidation(
                agent=firm,
                inventory_value=0.0, # Inventory recovered
                capital_value=capital_value,
                recovered_cash=0.0,
                reason="firm_liquidation",
                tick=state.time,
                government_agent=government
            )

            # Clear shareholdings
            # Use Registry if available
            if state.shareholder_registry:
                 for household in state.households:
                      state.shareholder_registry.register_shares(firm.id, household.id, 0.0)
            elif state.stock_market:
                 # Legacy Fallback
                 for household in state.households:
                    if firm.id in household._econ_state.portfolio.to_legacy_dict():
                        del household._econ_state.portfolio.to_legacy_dict()[firm.id]
                        if hasattr(state.stock_market, "update_shareholder"):
                            state.stock_market.update_shareholder(household.id, firm.id, 0)

            # TD-030: Unregister from currency registry immediately
            if isinstance(firm, ICurrencyHolder):
                state.unregister_currency_holder(firm)

            # TD-INT-STRESS-SCALE: Clean up settlement index
            if self.settlement_system:
                self.settlement_system.remove_agent_from_all_accounts(firm.id)

        # --- Household Liquidation (Inheritance) ---
        inactive_households = [h for h in state.households if not h._bio_state.is_active]
        for household in inactive_households:
            # WO-109: Preserve inactive agent for transaction processing
            if hasattr(state, "inactive_agents") and isinstance(state.inactive_agents, dict):
                state.inactive_agents[household.id] = household

            # Capture transactions returned by InheritanceManager
            inheritance_txs = self.inheritance_manager.process_death(household, state.government, state)
            # TD-160: Atomic Execution - Transactions are already executed.
            # Append to state.transactions for logging, but do NOT return them to inter_tick_queue.
            state.transactions.extend(inheritance_txs)

            inv_value = self._calculate_inventory_value(household._econ_state.inventory, state.markets)

            # Phase 3: Asset Recovery for Households
            if household._econ_state.inventory:
                 bankruptcy_event = {
                     "agent_id": household.id,
                     "tick": state.time,
                     "inventory": household._econ_state.inventory.copy()
                 }
                 self.public_manager.process_bankruptcy_event(bankruptcy_event)

            # Record Liquidation (Destruction)
            # Inventory is recovered, so we record 0 destruction for inventory.
            if False and inv_value > 0: # Logic disabled as inventory is recovered
                 self.settlement_system.record_liquidation(
                     agent=household,
                     inventory_value=inv_value,
                     capital_value=0.0,
                     recovered_cash=0.0,
                     reason="household_liquidation_inventory",
                     tick=state.time
                 )

            household._econ_state.inventory.clear()
            household._econ_state.portfolio.to_legacy_dict().clear()
            # Direct access as Household is strongly typed in list
            household._econ_state.portfolio.holdings.clear()

            # Clear shareholdings from registry (TD-275)
            if state.shareholder_registry:
                for firm in state.firms:
                     state.shareholder_registry.register_shares(firm.id, household.id, 0.0)
            elif state.stock_market:
                # Fallback for older StockMarket logic if any
                # Using hasattr only for legacy fallback support
                if hasattr(state.stock_market, "update_shareholder"):
                    # We don't iterate shareholders directly as it's an internal impl detail
                    # Instead we iterate firms and clear for this household
                    for firm in state.firms:
                         state.stock_market.update_shareholder(household.id, firm.id, 0)

            # TD-030: Unregister from currency registry immediately
            if isinstance(household, ICurrencyHolder):
                state.unregister_currency_holder(household)

            # TD-INT-STRESS-SCALE: Clean up settlement index
            if self.settlement_system:
                self.settlement_system.remove_agent_from_all_accounts(household.id)

        # Cleanup Global Lists
        state.households[:] = [h for h in state.households if h._bio_state.is_active]
        state.firms[:] = [f for f in state.firms if f.is_active]

        state.agents.clear()
        state.agents.update({agent.id: agent for agent in state.households + state.firms})
        if state.bank:
             state.agents[state.bank.id] = state.bank
        if hasattr(state, 'government') and state.government:
             state.agents[state.government.id] = state.government
        if hasattr(state, 'central_bank') and state.central_bank:
             state.agents[state.central_bank.id] = state.central_bank
        if hasattr(state, 'escrow_agent') and state.escrow_agent:
             state.agents[state.escrow_agent.id] = state.escrow_agent

        for firm in state.firms:
            firm.hr_state.employees = [
                emp for emp in firm.hr_state.employees if hasattr(emp, 'is_active') and emp.is_active and emp.id in state.agents
            ]

        return transactions

    def _calculate_inventory_value(self, inventory: dict, markets: dict) -> float:
        total_value = 0.0
        default_price = getattr(self.config, "GOODS_INITIAL_PRICE", {}).get("default", 10.0)

        for item_id, qty in inventory.items():
            price = default_price

            # 1. Direct Item Market (Legacy)
            if item_id in markets:
                m = markets[item_id]
                if isinstance(m, IMarket):
                    p = m.get_price(item_id)
                    if p > 0: price = p
                elif hasattr(m, "avg_price") and m.avg_price > 0: # Strict Legacy Fallback
                    price = m.avg_price

            # 2. Goods Market (Standard)
            elif "goods_market" in markets:
                m = markets["goods_market"]
                if isinstance(m, IMarket):
                    p = m.get_price(item_id)
                    if p > 0: price = p

            # 3. Stock Market (Standard)
            elif "stock_market" in markets and item_id.startswith("stock_"):
                 m = markets["stock_market"]
                 if isinstance(m, IMarket):
                    p = m.get_price(item_id)
                    if p > 0: price = p

            total_value += qty * price
        return total_value

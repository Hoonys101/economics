from __future__ import annotations
from typing import List, Any, Optional
import logging
from simulation.systems.lifecycle.api import IDeathSystem
from simulation.dtos.api import SimulationState
from simulation.models import Transaction
from simulation.systems.inheritance_manager import InheritanceManager
from simulation.systems.liquidation_manager import LiquidationManager
from simulation.finance.api import ISettlementSystem
from modules.finance.api import ILiquidatable, IShareholderRegistry, IFinancialEntity
from modules.system.api import IAssetRecoverySystem, ICurrencyHolder, DEFAULT_CURRENCY
from simulation.interfaces.market_interface import IMarket

class DeathSystem(IDeathSystem):
    """
    Handles agent death, liquidation of assets, and inheritance processing.
    Refactored for Protocol Purity and Integer Math.
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
        """
        return self._handle_agent_liquidation(state)

    def _handle_agent_liquidation(self, state: SimulationState) -> List[Transaction]:
        transactions: List[Transaction] = []

        # --- Firm Liquidation ---
        # Identify inactive firms
        inactive_firms = [f for f in state.firms if not f.is_active]

        for firm in inactive_firms:
            # Delegate strictly to LiquidationManager
            if isinstance(firm, ILiquidatable):
                 self.liquidation_manager.initiate_liquidation(firm, state)

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
                state.unregister_currency_holder(firm)

            # 3. Settlement Index
            if self.settlement_system and hasattr(self.settlement_system, 'remove_agent_from_all_accounts'):
                self.settlement_system.remove_agent_from_all_accounts(firm.id)

        # --- Household Liquidation ---
        # Use property is_active (from IOrchestratorAgent/Household)
        inactive_households = [h for h in state.households if not h.is_active]

        for household in inactive_households:
             # Preserve for history/logging if needed
             if state.inactive_agents is not None:
                 state.inactive_agents[household.id] = household

             # Inheritance Manager (Executes transactions via side-effects)
             if hasattr(state, 'government') and state.government:
                  inheritance_txs = self.inheritance_manager.process_death(household, state.government, state)
                  transactions.extend(inheritance_txs)

             # Inventory Liquidation (Bankruptcy Event) via Public Manager
             # Access inventory via property or attribute
             inventory = None
             if hasattr(household, 'inventory'):
                 inventory = household.inventory
             elif hasattr(household, '_econ_state'):
                 inventory = household._econ_state.inventory

             if self.public_manager and inventory:
                 bankruptcy_event = {
                     "agent_id": household.id,
                     "tick": state.time,
                     "inventory": inventory.copy()
                 }
                 self.public_manager.process_bankruptcy_event(bankruptcy_event)

                 # Clear inventory
                 if hasattr(household, 'clear_inventory'):
                     household.clear_inventory()
                 elif hasattr(inventory, 'clear'):
                     inventory.clear()

             # Cleanup
             if isinstance(household, ICurrencyHolder):
                state.unregister_currency_holder(household)

             if self.settlement_system and hasattr(self.settlement_system, 'remove_agent_from_all_accounts'):
                self.settlement_system.remove_agent_from_all_accounts(household.id)

        # --- Global List Cleanup ---
        # Modify lists in place to reflect removals
        state.households[:] = [h for h in state.households if h.is_active]
        state.firms[:] = [f for f in state.firms if f.is_active]

        # Rebuild agents dict
        state.agents.clear()
        state.agents.update({agent.id: agent for agent in state.households + state.firms})
        # Add system agents back
        if state.bank: state.agents[state.bank.id] = state.bank
        if hasattr(state, 'government') and state.government: state.agents[state.government.id] = state.government
        if hasattr(state, 'central_bank') and state.central_bank: state.agents[state.central_bank.id] = state.central_bank
        if hasattr(state, 'escrow_agent') and state.escrow_agent: state.agents[state.escrow_agent.id] = state.escrow_agent

        return transactions

    def _calculate_inventory_value(self, inventory: dict, markets: dict) -> int:
        """
        Calculates total inventory value in integer pennies.
        """
        total_pennies = 0
        default_price_float = getattr(self.config, "GOODS_INITIAL_PRICE", {}).get("default", 10.0)
        default_price_pennies = int(default_price_float * 100)

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

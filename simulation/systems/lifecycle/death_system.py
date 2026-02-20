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
            # 0. Cancel Orders (Atomicity Fix)
            self._cancel_agent_orders(firm.id, state)

            # 0.5 Recover External Assets (Bank Deposits)
            self._recover_external_assets(firm.id, state)

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
            if self.settlement_system:
                self.settlement_system.remove_agent_from_all_accounts(firm.id)

        # --- Household Liquidation ---
        # Use property is_active (from IOrchestratorAgent/Household)
        inactive_households = [h for h in state.households if not h.is_active]

        for household in inactive_households:
             # 0. Cancel Orders (Atomicity Fix)
             self._cancel_agent_orders(household.id, state)

             # 0.5 Recover External Assets (Bank Deposits)
             self._recover_external_assets(household.id, state)

             # Preserve for history/logging if needed
             if state.inactive_agents is not None:
                 state.inactive_agents[household.id] = household

             # Inheritance Manager (Executes transactions via side-effects)
             if state.primary_government:
                  inheritance_txs = self.inheritance_manager.process_death(household, state.primary_government, state)
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

             if self.settlement_system:
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
        if state.primary_government: state.agents[state.primary_government.id] = state.primary_government
        if hasattr(state, 'central_bank') and state.central_bank: state.agents[state.central_bank.id] = state.central_bank
        if hasattr(state, 'escrow_agent') and state.escrow_agent: state.agents[state.escrow_agent.id] = state.escrow_agent

        return transactions

    def _recover_external_assets(self, agent_id: int, state: SimulationState) -> None:
        """
        Recovers assets from external accounts (Banks) before liquidation.
        """
        if not self.settlement_system: return

        # 1. Find Banks using new API
        if hasattr(self.settlement_system, 'get_agent_banks'):
            bank_ids = self.settlement_system.get_agent_banks(agent_id)
        else:
            return

        agent = state.agents.get(agent_id)
        if not agent: return

        for bank_id in bank_ids:
            # 2. Close Account
            bank = state.agents.get(bank_id)
            if bank and hasattr(bank, 'close_account'):
                amount = bank.close_account(agent_id)
                if amount > 0:
                    # 3. Deposit to Wallet (Consolidate Assets)
                    if hasattr(agent, 'deposit'):
                        agent.deposit(amount)
                    elif hasattr(agent, '_deposit'):
                        agent._deposit(amount)
                    self.logger.info(f"RECOVER_ASSETS | Recovered {amount} from Bank {bank_id} for Agent {agent_id}")

    def _cancel_agent_orders(self, agent_id: str | int, state: SimulationState) -> None:
        """
        Scrub agent orders from all markets to ensure atomicity.
        """
        if not state.markets:
            return

        for market in state.markets.values():
            # Check for cancel_orders method (Protocol compliance)
            if isinstance(market, IMarket):
                try:
                    market.cancel_orders(agent_id)
                except Exception as e:
                    self.logger.error(
                        f"ORDER_SCRUB_FAIL | Failed to cancel orders for agent {agent_id} in market {getattr(market, 'id', 'unknown')}: {e}"
                    )

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

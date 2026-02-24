from __future__ import annotations
from typing import List, Any, Dict, Protocol, runtime_checkable, Optional
import logging
from simulation.systems.lifecycle.api import IAgingSystem, IAgingFirm, IFinanceEngine
from simulation.dtos.api import SimulationState
from simulation.models import Transaction
from simulation.systems.demographic_manager import DemographicManager
from modules.system.api import DEFAULT_CURRENCY, ICurrencyHolder
from simulation.interfaces.market_interface import IMarket
from modules.finance.api import IFinancialEntity

class AgingSystem(IAgingSystem):
    """
    Handles aging, needs updates, and distress/grace protocol checks for agents.
    Strictly follows Protocol Purity and Integer Math.
    """
    def __init__(self, config_module: Any, demographic_manager: DemographicManager, logger: logging.Logger):
        self.config = config_module
        self.demographic_manager = demographic_manager
        self.logger = logger

    def execute(self, state: SimulationState) -> List[Transaction]:
        """
        Executes the aging phase.
        1. Biological aging (DemographicManager)
        2. Firm lifecycle checks (Bankruptcy/Grace Protocol)
        3. Household lifecycle checks (Distress)
        """
        # 1. Aging (and internal lifecycle update)
        self.demographic_manager.process_aging(state.households, state.time, state.market_data)

        # 2. Firm Lifecycle (Aging & Bankruptcy Checks)
        self._process_firm_lifecycle(state)

        # 3. Household Lifecycle (Distress Checks)
        self._process_household_lifecycle(state)

        return []

    def _process_firm_lifecycle(self, state: SimulationState) -> None:
        """
        Handles lifecycle updates for all active firms.
        Includes Solvency Gate and WO-167 Grace Protocol.
        Refactored for Protocol Purity.
        """
        # Config values (converted to pennies where applicable)
        assets_threshold_pennies = int(getattr(self.config, "ASSETS_CLOSURE_THRESHOLD", 0.0) * 100)
        closure_turns_threshold = getattr(self.config, "FIRM_CLOSURE_TURNS_THRESHOLD", 5)
        liquidity_inc_rate = getattr(self.config, "LIQUIDITY_NEED_INCREASE_RATE", 1.0)
        grace_period = getattr(self.config, "DISTRESS_GRACE_PERIOD", 5)

        for firm in state.firms:
            if not isinstance(firm, IAgingFirm) or not firm.is_active:
                continue

            firm.age += 1

            # Liquidity Need Increase
            current_need = firm.needs.get("liquidity_need", 0.0)
            firm.needs["liquidity_need"] = min(100.0, current_need + liquidity_inc_rate)

            # Check bankruptcy status (Protocol Purity)
            if isinstance(firm.finance_engine, IFinanceEngine):
                firm.finance_engine.check_bankruptcy(firm.finance_state, firm.config)

            # WO-167: Grace Protocol
            # Check for Cash Crunch (Integer Math)
            current_assets_pennies = 0
            if isinstance(firm, ICurrencyHolder):
                current_assets_pennies = firm.get_balance(DEFAULT_CURRENCY)
            elif isinstance(firm.wallet, IFinancialEntity): # Fallback via wallet
                 current_assets_pennies = firm.wallet.balance_pennies

            liquidity_need_pennies = int(firm.needs.get("liquidity_need", 0.0) * 100)
            is_crunch = current_assets_pennies < liquidity_need_pennies

            # Inventory Value Calculation (Integer Pennies)
            inventory_val_pennies = self._calculate_inventory_value(firm.get_all_items(), state.markets)

            if is_crunch and inventory_val_pennies > 0:
                # Enter or Continue Distress
                firm.finance_state.is_distressed = True
                firm.finance_state.distress_tick_counter += 1

                # If within grace period
                if firm.finance_state.distress_tick_counter <= grace_period:
                    continue
            else:
                # Recovery or No Crunch
                firm.finance_state.is_distressed = False
                firm.finance_state.distress_tick_counter = 0

            # Solvency Gate: Prevent Zombie Timer from killing solvent firms
            # Solvent if assets > 2x threshold
            is_solvent = current_assets_pennies > (assets_threshold_pennies * 2)
            is_bankrupt_by_loss = getattr(firm.finance_state, "consecutive_loss_turns", 0) >= closure_turns_threshold

            # Close if assets depleted OR (bankrupt by loss AND not solvent)
            if current_assets_pennies <= assets_threshold_pennies or (is_bankrupt_by_loss and not is_solvent):

                # Grace Period Check
                if getattr(firm.finance_state, "distress_tick_counter", 0) > grace_period:
                    pass # Allow closure
                elif getattr(firm.finance_state, "is_distressed", False):
                    continue # Safety check: still in grace period

                firm.is_active = False
                self.logger.warning(
                    f"FIRM_INACTIVE | Firm {firm.id} closed. Assets: {current_assets_pennies/100:.2f}, "
                    f"Loss Turns: {getattr(firm.finance_state, 'consecutive_loss_turns', 0)}, Solvent: {is_solvent}"
                )

    def _process_household_lifecycle(self, state: SimulationState) -> None:
        """
        WO-167: Handles distress checks for households.
        Triggers emergency liquidation if starving but solvent.
        """
        survival_threshold = getattr(self.config, "SURVIVAL_NEED_DEATH_THRESHOLD", 100.0)
        distress_threshold = survival_threshold * 0.9
        grace_period = getattr(self.config, "DISTRESS_GRACE_PERIOD", 5)

        for household in state.households:
            # Direct access to _bio_state is unavoidable without DTO setter,
            # but we check if it exists or use property if available.
            # Assuming household is Household object.
            # Use getattr for robustness
            is_active = getattr(household, 'is_active', False)
            if not is_active:
                continue

            # Need is typically in BioState
            # We access via property if possible, else direct
            survival_need = 0.0

            # Prefer property access or known structure
            # Household typically has 'needs' property or '_bio_state.needs'
            needs = getattr(household, 'needs', None)
            if needs is None:
                 bio_state = getattr(household, '_bio_state', None)
                 if bio_state:
                     needs = getattr(bio_state, 'needs', {})

            if needs:
                survival_need = needs.get("survival", 0.0)

            # Check for Distress
            if survival_need > distress_threshold:
                # Inventory check
                has_inventory = False
                # Try property first
                inventory = getattr(household, 'inventory', None)
                if inventory is None:
                     econ_state = getattr(household, '_econ_state', None)
                     if econ_state:
                         inventory = getattr(econ_state, 'inventory', None)

                if inventory:
                    has_inventory = any(qty > 0 for qty in inventory.values())

                # Stocks check
                has_stocks = False
                portfolio = getattr(household, 'portfolio', None)
                if portfolio:
                    holdings = getattr(portfolio, 'holdings', None)
                    if holdings:
                         has_stocks = True
                    else:
                         legacy_dict = getattr(portfolio, 'to_legacy_dict', None)
                         if legacy_dict:
                             has_stocks = any(qty > 0 for qty in legacy_dict().values())

                if has_inventory or has_stocks:
                    # Update distress counter
                    current_counter = getattr(household, 'distress_tick_counter', 0)
                    new_counter = current_counter + 1
                    setattr(household, 'distress_tick_counter', new_counter)

                    if new_counter <= grace_period:
                         # Use method on Household if it exists
                         trigger_method = getattr(household, 'trigger_emergency_liquidation', None)
                         if trigger_method:
                             emergency_orders = trigger_method()

                             # Place orders
                             for order in emergency_orders:
                                 market = state.markets.get(order.market_id)
                                 if isinstance(market, IMarket):
                                     # Check for place_order method on IMarket implementation
                                     place_order = getattr(market, 'place_order', None)
                                     if place_order:
                                         place_order(order, state.time)
                                 elif order.market_id == "stock_market" and state.stock_market:
                                      place_order = getattr(state.stock_market, 'place_order', None)
                                      if place_order:
                                          place_order(order, state.time)

                else:
                    # No assets to sell, nature takes its course
                    pass
            else:
                # Reset distress counter
                if hasattr(household, 'distress_tick_counter'):
                    setattr(household, 'distress_tick_counter', 0)

    def _calculate_inventory_value(self, inventory: dict, markets: dict) -> int:
        """
        Calculates total inventory value in integer pennies.
        """
        total_pennies = 0
        # MIGRATION: Use integer default price (Penny Standard)
        raw_price = getattr(self.config, "DEFAULT_FALLBACK_PRICE", 1000)
        default_price_pennies = int(raw_price)

        for item_id, qty in inventory.items():
            price_pennies = default_price_pennies
            if item_id in markets:
                m = markets[item_id]
                # Check for IMarket protocol
                if isinstance(m, IMarket):
                    try:
                        p_float = m.get_price(item_id)
                        if p_float > 0:
                            price_pennies = int(p_float * 100)
                    except Exception:
                        pass

            total_pennies += int(qty * price_pennies)
        return total_pennies

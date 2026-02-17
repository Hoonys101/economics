from __future__ import annotations
from typing import List, Any
import logging
from simulation.systems.lifecycle.api import IAgingSystem
from simulation.dtos.api import SimulationState
from simulation.models import Transaction
from simulation.systems.demographic_manager import DemographicManager
from modules.system.api import DEFAULT_CURRENCY

class AgingSystem(IAgingSystem):
    """
    Handles aging, needs updates, and distress/grace protocol checks for agents.
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
        Includes WO-167 Grace Protocol for distressed firms.
        """
        assets_threshold = getattr(self.config, "ASSETS_CLOSURE_THRESHOLD", 0.0)
        closure_turns_threshold = getattr(self.config, "FIRM_CLOSURE_TURNS_THRESHOLD", 5)
        liquidity_inc_rate = getattr(self.config, "LIQUIDITY_NEED_INCREASE_RATE", 1.0)
        grace_period = getattr(self.config, "DISTRESS_GRACE_PERIOD", 5)

        for firm in state.firms:
            if not firm.is_active:
                continue

            firm.age += 1

            # Liquidity Need Increase
            firm.needs["liquidity_need"] = min(100.0, firm.needs["liquidity_need"] + liquidity_inc_rate)

            # Check bankruptcy status (logic from FinanceDepartment)
            firm.finance_engine.check_bankruptcy(firm.finance_state, firm.config)

            # WO-167: Grace Protocol
            # Check for Cash Crunch
            current_assets = firm.wallet.get_balance(DEFAULT_CURRENCY)
            is_crunch = current_assets < firm.needs.get("liquidity_need", 0.0)

            # Inventory Value Calculation
            inventory_val = self._calculate_inventory_value(firm.get_all_items(), state.markets)

            if is_crunch and inventory_val > 0:
                # Enter or Continue Distress
                firm.finance_state.is_distressed = True
                firm.finance_state.distress_tick_counter += 1

                # If within grace period
                if firm.finance_state.distress_tick_counter <= grace_period:
                    # Trigger Emergency Liquidation (Manual Logic since proxy is gone)
                    # Use sales engine? Or just post orders.
                    # emergency_orders = []
                    # Note: Original implementation had a placeholder here.
                    # We preserve the logic as is: check grace period, skip closure.

                    # Inject orders into markets (Placeholder from original code)
                    # for order in emergency_orders: ...

                    # SKIP standard closure check
                    continue
            else:
                # Recovery or No Crunch
                firm.finance_state.is_distressed = False
                firm.finance_state.distress_tick_counter = 0

            # Standard Closure Check
            if (current_assets <= assets_threshold or
                    firm.finance_state.consecutive_loss_turns >= closure_turns_threshold):

                # Double check grace period (if we fell through but counter is high)
                if getattr(firm.finance_state, "distress_tick_counter", 0) > grace_period:
                    pass # Allow closure
                elif getattr(firm.finance_state, "is_distressed", False):
                    continue # Should have been caught above, but safety check

                firm.is_active = False
                self.logger.warning(
                    f"FIRM_INACTIVE | Firm {firm.id} closed down. Assets: {current_assets:.2f}, Consecutive Loss Turns: {firm.finance_state.consecutive_loss_turns}",
                    extra={
                        "tick": state.time,
                        "agent_id": firm.id,
                        "assets": current_assets,
                        "consecutive_loss_turns": firm.finance_state.consecutive_loss_turns,
                        "tags": ["firm_closure"],
                    }
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
            if not household._bio_state.is_active:
                continue

            survival_need = household._bio_state.needs.get("survival", 0.0)

            # Check for Distress
            if survival_need > distress_threshold:
                has_inventory = any(qty > 0 for qty in household._econ_state.inventory.values())
                has_stocks = any(qty > 0 for qty in household._econ_state.portfolio.to_legacy_dict().values())

                if has_inventory or has_stocks:
                    household.distress_tick_counter += 1

                    if household.distress_tick_counter <= grace_period:
                         # Use method on Household if it exists (it does in original code)
                         emergency_orders = household.trigger_emergency_liquidation()

                         for order in emergency_orders:
                             market = state.markets.get(order.market_id)
                             if market:
                                 market.place_order(order, state.time)
                             else:
                                 # Fallback for stocks
                                 if order.market_id == "stock_market" and hasattr(state, "stock_market") and state.stock_market:
                                     state.stock_market.place_order(order, state.time)

                else:
                    # No assets to sell, nature takes its course
                    pass
            else:
                household.distress_tick_counter = 0

    def _calculate_inventory_value(self, inventory: dict, markets: dict) -> float:
        total_value = 0.0
        default_price = getattr(self.config, "GOODS_INITIAL_PRICE", {}).get("default", 10.0)

        for item_id, qty in inventory.items():
            price = default_price
            if item_id in markets:
                m = markets[item_id]
                if hasattr(m, "avg_price") and m.avg_price > 0:
                    price = m.avg_price
                elif hasattr(m, "current_price") and m.current_price > 0:
                    price = m.current_price

            total_value += qty * price
        return total_value

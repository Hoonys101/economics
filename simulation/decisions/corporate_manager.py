from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional, Any, Dict
import logging
import random
import math

from simulation.models import Order
from simulation.schemas import FirmActionVector
from simulation.dtos import DecisionContext

if TYPE_CHECKING:
    from simulation.firms import Firm

logger = logging.getLogger(__name__)

class CorporateManager:
    """
    CEO Module (WO-027).
    Translates the 6-channel Aggressiveness Vector (Strategy) into concrete Actions (Tactics).
    Owned by AIDrivenFirmDecisionEngine.
    """

    def __init__(self, config_module: Any, logger: Optional[logging.Logger] = None):
        self.config_module = config_module
        self.logger = logger if logger else logging.getLogger(__name__)

    def realize_ceo_actions(
        self,
        firm: Firm,
        context: DecisionContext,
        action_vector: FirmActionVector
    ) -> List[Order]:
        """
        Main entry point. Orchestrates all channel executions.
        """
        orders: List[Order] = []

        # 1. R&D Channel (Innovation)
        self._manage_r_and_d(firm, action_vector.rd_aggressiveness, context.current_time)

        # 2. Capital Channel (CAPEX)
        self._manage_capex(firm, action_vector.capital_aggressiveness, context.reflux_system, context.current_time)

        # 3. Dividend Channel
        self._manage_dividends(firm, action_vector.dividend_aggressiveness)

        # 4. Debt Channel (Leverage)
        debt_orders = self._manage_debt(firm, action_vector.debt_aggressiveness, context.market_data)
        orders.extend(debt_orders)

        # 5. Pricing Channel (Sales)
        sales_order = self._manage_pricing(firm, action_vector.sales_aggressiveness, context.market_data, context.markets, context.current_time)
        # Note: Sales orders are placed directly via firm.post_ask inside _manage_pricing usually,
        # or returned. Let's stick to returning orders if possible, but firm.post_ask injects brand info.
        # firm.post_ask calls market.place_order immediately. So we don't return it here to avoid duplication.

        # 6. Hiring Channel (Employment)
        hiring_orders = self._manage_hiring(firm, action_vector.hiring_aggressiveness, context.market_data)
        orders.extend(hiring_orders)

        return orders

    def _manage_r_and_d(self, firm: Firm, aggressiveness: float, current_time: int) -> None:
        """
        Innovation Physics.
        Aggressiveness (0.0~1.0) determines % of Revenue spent on R&D.
        """
        if aggressiveness <= 0.1:
            return

        # Budget Calculation
        # Cap at 20% of revenue for max aggressiveness?
        # WO says: Chance = Budget / (Revenue * 0.2)
        revenue_base = max(firm.revenue_this_turn, firm.assets * 0.05) # Fallback to assets if no revenue
        rd_budget_rate = aggressiveness * 0.20 # Max 20%
        budget = revenue_base * rd_budget_rate

        # Affordability
        if firm.assets < budget:
            budget = firm.assets * 0.5 # Sanity cap

        if budget < 10.0:
            return

        # Execution
        firm.assets -= budget
        firm.research_history["total_spent"] += budget

        # Success Logic
        # P = min(1.0, Budget / (Revenue * 0.2)) * Skill_Multiplier
        # Note: Revenue here should probably be "Expected Revenue" or "Last Revenue".
        denominator = max(firm.revenue_this_turn * 0.2, 100.0)
        base_chance = min(1.0, budget / denominator)

        # Skill Multiplier (Avg Employee Skill)
        avg_skill = 1.0
        if firm.employees:
            avg_skill = sum(getattr(e, 'labor_skill', 1.0) for e in firm.employees) / len(firm.employees)

        success_chance = base_chance * avg_skill

        # Roll Dice
        if random.random() < success_chance:
            # SUCCESS!
            firm.research_history["success_count"] += 1
            firm.research_history["last_success_tick"] = current_time

            # Effects
            # 1. Quality Boost
            firm.base_quality += 0.05

            # 2. Productivity Boost
            firm.productivity_factor *= 1.05

            self.logger.info(
                f"R&D SUCCESS | Firm {firm.id} spent {budget:.1f}. Quality {firm.base_quality:.2f}, Prod {firm.productivity_factor:.2f}",
                extra={"agent_id": firm.id, "tick": current_time, "tags": ["innovation", "success"]}
            )
        else:
             self.logger.info(
                f"R&D FAIL | Firm {firm.id} spent {budget:.1f}. Chance {success_chance:.1%}",
                extra={"agent_id": firm.id, "tick": current_time, "tags": ["innovation", "fail"]}
            )

    def _manage_capex(self, firm: Firm, aggressiveness: float, reflux_system: Any, current_time: int) -> None:
        """
        Capacity Expansion.
        """
        if aggressiveness <= 0.2:
            return

        # Budget: Up to 50% of assets if aggressive
        budget = firm.assets * (aggressiveness * 0.5)

        if budget < 100.0:
            return

        # Execution
        firm.assets -= budget

        # Capture Reflux
        if reflux_system:
             reflux_system.capture(budget, str(firm.id), "capex")

        # Add Capital Stock
        # Efficiency inverse of Capital Output Ratio
        efficiency = 1.0 / getattr(self.config_module, "CAPITAL_TO_OUTPUT_RATIO", 2.0)
        added_capital = budget * efficiency
        firm.capital_stock += added_capital

        self.logger.info(
            f"CAPEX | Firm {firm.id} invested {budget:.1f}, added {added_capital:.1f} capital.",
            extra={"agent_id": firm.id, "tick": current_time, "tags": ["capex"]}
        )

    def _manage_dividends(self, firm: Firm, aggressiveness: float) -> None:
        """
        Set Dividend Rate.
        """
        base_rate = getattr(self.config_module, "DIVIDEND_RATE_MIN", 0.1)
        max_rate = getattr(self.config_module, "DIVIDEND_RATE_MAX", 0.5)

        # Linear Mapping
        firm.dividend_rate = base_rate + (aggressiveness * (max_rate - base_rate))

    def _manage_debt(self, firm: Firm, aggressiveness: float, market_data: Dict) -> List[Order]:
        """
        Leverage Management.
        Aggressive (1.0) -> Target High Leverage -> Borrow
        Passive (0.0) -> Target Low Leverage -> Repay
        """
        orders = []

        # 1. Determine Target Leverage (Debt / Assets)
        # 0.0 -> 0%
        # 1.0 -> 200% (High risk)
        target_leverage = aggressiveness * 2.0

        current_debt = 0.0
        debt_info = market_data.get("debt_data", {}).get(firm.id)
        if debt_info:
            current_debt = debt_info.get("total_principal", 0.0)

        current_assets = max(firm.assets, 1.0)
        current_leverage = current_debt / current_assets

        # 2. Action
        if current_leverage < target_leverage:
            # Need to BORROW to reach target (Growth mode)
            # Only borrow if we actually need cash for something?
            # Or leverage up to buy back shares/invest?
            # For now, borrow to hold cash (liquidity) or fund operations.

            # Gap calculation
            desired_debt = current_assets * target_leverage
            borrow_amount = desired_debt - current_debt

            # Cap borrow amount per tick
            borrow_amount = min(borrow_amount, current_assets * 0.5)

            if borrow_amount > 100.0:
                orders.append(
                    Order(firm.id, "LOAN_REQUEST", "loan", borrow_amount, 0.10, "loan")
                )

        elif current_leverage > target_leverage:
            # Need to REPAY (De-leverage)
            excess_debt = current_debt - (current_assets * target_leverage)
            repay_amount = min(excess_debt, firm.assets * 0.5) # Don't drain all cash

            if repay_amount > 10.0 and current_debt > 0:
                 orders.append(
                    Order(firm.id, "REPAYMENT", "loan", repay_amount, 1.0, "loan")
                )

        return orders

    def _manage_pricing(self, firm: Firm, aggressiveness: float, market_data: Dict, markets: Dict, current_time: int) -> Optional[Order]:
        """
        Sales Channel.
        Aggressiveness 1.0 -> Low Price (Volume)
        Aggressiveness 0.0 -> High Price (Margin)
        """
        item_id = firm.specialization
        current_inventory = firm.inventory.get(item_id, 0)

        if current_inventory <= 0:
            return None

        # Anchor Price
        market_price = 0.0
        if item_id in market_data:
             market_price = market_data[item_id].get('avg_price', 0)
        if market_price <= 0:
             market_price = firm.last_prices.get(item_id, 0)
        if market_price <= 0:
             market_price = self.config_module.GOODS.get(item_id, {}).get("production_cost", 10.0)

        # Adjustment
        # Agg=0.5 -> Price=Market
        # Agg=1.0 -> Price=Market * 0.8 (-20%)
        # Agg=0.0 -> Price=Market * 1.2 (+20%)
        adjustment = (0.5 - aggressiveness) * 0.4
        target_price = market_price * (1.0 + adjustment)

        # Solvency Check (from AIDrivenFirmDecisionEngine logic, moved/duplicated here?
        # Ideally we invoke a shared helper or re-implement simple version)
        # Let's re-implement simple version for now.

        # Decay for old inventory
        sales_vol = getattr(firm, 'last_sales_volume', 1.0)
        if sales_vol <= 0: sales_vol = 1.0
        days_on_hand = current_inventory / sales_vol
        decay = max(0.5, 1.0 - (days_on_hand * 0.005))
        target_price *= decay

        target_price = max(target_price, 0.1)
        firm.last_prices[item_id] = target_price

        qty = min(current_inventory, self.config_module.MAX_SELL_QUANTITY)

        # Execute
        target_market = markets.get(item_id)
        if target_market:
            firm.post_ask(item_id, target_price, qty, target_market, current_time)

        return None # Already posted

    def _manage_hiring(self, firm: Firm, aggressiveness: float, market_data: Dict) -> List[Order]:
        """
        Hiring Channel.
        Aggressiveness 1.0 -> High Wage, Hire More
        """
        orders = []
        target_inventory = firm.production_target
        current_inventory = firm.inventory.get(firm.specialization, 0)
        inventory_gap = target_inventory - current_inventory

        if inventory_gap <= 0:
            return []

        needed_labor = max(1, int(inventory_gap / firm.productivity_factor))
        needed_labor = min(needed_labor, 5)

        market_wage = self.config_module.LABOR_MARKET_MIN_WAGE
        if "labor" in market_data and "avg_wage" in market_data["labor"]:
             market_wage = market_data["labor"]["avg_wage"]

        # Wage Offer
        # Agg=0.5 -> Market Wage
        # Agg=1.0 -> Market + 30%
        # Agg=0.0 -> Market - 20%
        adjustment = -0.2 + (aggressiveness * 0.5)
        offer_wage = market_wage * (1.0 + adjustment)
        offer_wage = max(self.config_module.LABOR_MARKET_MIN_WAGE, offer_wage)

        for _ in range(needed_labor):
             orders.append(
                 Order(firm.id, "BUY", "labor", 1, offer_wage, "labor")
             )

        return orders

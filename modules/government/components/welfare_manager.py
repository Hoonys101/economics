from typing import List, Any, Dict, TYPE_CHECKING, Optional
import logging
from simulation.models import Transaction
from modules.government.constants import (
    DEFAULT_ANNUAL_WEALTH_TAX_RATE, DEFAULT_TICKS_PER_YEAR,
    DEFAULT_WEALTH_TAX_THRESHOLD, DEFAULT_UNEMPLOYMENT_BENEFIT_RATIO,
    DEFAULT_STIMULUS_TRIGGER_GDP_DROP, DEFAULT_HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK,
    DEFAULT_BASIC_FOOD_PRICE
)

if TYPE_CHECKING:
    from simulation.agents.government import Government

logger = logging.getLogger(__name__)

class WelfareManager:
    def __init__(self, government: 'Government'):
        self.government = government
        self.config = government.config_module

    def get_survival_cost(self, market_data: Dict[str, Any]) -> float:
        """ Calculates current survival cost based on food prices. """
        avg_food_price = 0.0
        goods_market = market_data.get("goods_market", {})
        if "basic_food_current_sell_price" in goods_market:
            avg_food_price = goods_market["basic_food_current_sell_price"]
        else:
            avg_food_price = getattr(self.config, "GOODS_INITIAL_PRICE", {}).get("basic_food", DEFAULT_BASIC_FOOD_PRICE)

        daily_food_need = getattr(self.config, "HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK", DEFAULT_HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK)
        return max(avg_food_price * daily_food_need, 10.0)

    def provide_household_support(self, household: Any, amount: float, current_tick: int) -> List[Transaction]:
        """Provides subsidies to households (e.g., unemployment, stimulus). Returns transactions."""
        transactions = []
        effective_amount = amount * self.government.welfare_budget_multiplier

        if effective_amount <= 0:
            return []

        # Check budget, issue bonds if needed (Optimistic check)
        if self.government.assets < effective_amount:
            needed = effective_amount - self.government.assets
            # FinanceSystem now returns (bonds, transactions)
            bonds, txs = self.government.finance_system.issue_treasury_bonds(needed, current_tick)
            if not bonds:
                logger.warning(f"BOND_ISSUANCE_FAILED | Failed to raise {needed:.2f} for household support.")
                return []
            transactions.extend(txs)

        # Generate Welfare Transaction
        tx = Transaction(
            buyer_id=self.government.id,
            seller_id=household.id,
            item_id="welfare_support",
            quantity=1.0,
            price=effective_amount,
            market_id="system",
            transaction_type="welfare",
            time=current_tick
        )
        transactions.append(tx)

        self.government.total_spent_subsidies += effective_amount
        self.government.expenditure_this_tick += effective_amount
        self.government.current_tick_stats["welfare_spending"] += effective_amount

        logger.info(
            f"HOUSEHOLD_SUPPORT | Generated support tx of {effective_amount:.2f} to {household.id}",
            extra={"tick": current_tick, "agent_id": self.government.id, "amount": effective_amount, "target_id": household.id}
        )
        return transactions

    def run_welfare_check(self, agents: List[Any], market_data: Dict[str, Any], current_tick: int) -> List[Transaction]:
        """
        Government Main Loop Step.
        Returns List of Transactions.
        """
        transactions = []
        self.government.reset_tick_flow()

        # 1. Calculate Survival Cost (Dynamic)
        survival_cost = self.get_survival_cost(market_data)

        # 2. Wealth Tax & Unemployment Benefit
        wealth_tax_rate_annual = getattr(self.config, "ANNUAL_WEALTH_TAX_RATE", DEFAULT_ANNUAL_WEALTH_TAX_RATE)
        ticks_per_year = getattr(self.config, "TICKS_PER_YEAR", DEFAULT_TICKS_PER_YEAR)
        wealth_tax_rate_tick = wealth_tax_rate_annual / ticks_per_year
        wealth_threshold = getattr(self.config, "WEALTH_TAX_THRESHOLD", DEFAULT_WEALTH_TAX_THRESHOLD)

        unemployment_ratio = getattr(self.config, "UNEMPLOYMENT_BENEFIT_RATIO", DEFAULT_UNEMPLOYMENT_BENEFIT_RATIO)
        benefit_amount = survival_cost * unemployment_ratio

        total_wealth_tax = 0.0
        total_welfare_paid = 0.0

        for agent in agents:
            if not getattr(agent, "is_active", False):
                continue

            if hasattr(agent, "needs") and hasattr(agent, "is_employed"):
                # A. Wealth Tax (Synchronous & Atomic)
                net_worth = agent.assets
                if net_worth > wealth_threshold:
                    tax_amount = (net_worth - wealth_threshold) * wealth_tax_rate_tick
                    # Ensure we don't tax more than they have (safety, though collect_tax checks too)
                    tax_amount = min(tax_amount, agent.assets)

                    if tax_amount > 0 and self.government.settlement_system:
                        # Replaced TaxAgency call with internal collect_tax or direct transfer
                        # Using collect_tax (even if deprecated for external) is fine for internal shortcut
                        # to handle recording.
                        result = self.government.collect_tax(tax_amount, "wealth_tax", agent, current_tick)
                        if result['success']:
                             total_wealth_tax += result['amount_collected']

                # B. Unemployment Benefit
                if not agent.is_employed:
                    txs = self.provide_household_support(agent, benefit_amount, current_tick)
                    transactions.extend(txs)
                    total_welfare_paid += benefit_amount

        # 3. Stimulus Check
        current_gdp = market_data.get("total_production", 0.0)
        self.government.gdp_history.append(current_gdp)
        if len(self.government.gdp_history) > self.government.gdp_history_window:
            self.government.gdp_history.pop(0)

        trigger_drop = getattr(self.config, "STIMULUS_TRIGGER_GDP_DROP", DEFAULT_STIMULUS_TRIGGER_GDP_DROP)

        should_stimulus = False
        if len(self.government.gdp_history) >= 10:
            past_gdp = self.government.gdp_history[-10]
            if past_gdp > 0:
                change = (current_gdp - past_gdp) / past_gdp
                if change <= trigger_drop:
                    should_stimulus = True

        if should_stimulus:
             stimulus_amount = survival_cost * 5.0
             active_households = [a for a in agents if hasattr(a, "is_employed") and getattr(a, "is_active", False)]

             total_stimulus = 0.0
             for h in active_households:
                 txs = self.provide_household_support(h, stimulus_amount, current_tick)
                 transactions.extend(txs)

                 # Calculate total from txs for logging?
                 # Assuming 1 welfare tx per support call
                 for tx in txs:
                     if tx.transaction_type == 'welfare':
                         total_stimulus += tx.price

             if total_stimulus > 0:
                 self.government.last_fiscal_activation_tick = current_tick
                 logger.warning(
                     f"STIMULUS_TRIGGERED | GDP Drop Detected. Generated stimulus txs total {total_stimulus:.2f}.",
                     extra={"tick": current_tick, "agent_id": self.government.id, "gdp_current": current_gdp}
                 )

        return transactions

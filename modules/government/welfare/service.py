from typing import List, Any, Dict, TYPE_CHECKING, Optional
import logging
from simulation.models import Transaction
from modules.government.welfare.api import IWelfareService, IWelfareRecipient
from modules.government.constants import (
    DEFAULT_UNEMPLOYMENT_BENEFIT_RATIO,
    DEFAULT_STIMULUS_TRIGGER_GDP_DROP, DEFAULT_HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK,
    DEFAULT_BASIC_FOOD_PRICE
)
from modules.system.api import DEFAULT_CURRENCY

if TYPE_CHECKING:
    from simulation.agents.government import Government

logger = logging.getLogger(__name__)

class WelfareService(IWelfareService):
    def __init__(self, government: 'Government'):
        self.government = government
        self.config = government.config_module
        self.spending_this_tick: float = 0.0

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
        current_balance = 0.0
        if isinstance(self.government.assets, dict):
             current_balance = self.government.assets.get(DEFAULT_CURRENCY, 0.0)
        else:
             current_balance = float(self.government.assets)

        if current_balance < effective_amount:
            needed = effective_amount - current_balance
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

        # Update local stats
        self.spending_this_tick += effective_amount

        logger.info(
            f"HOUSEHOLD_SUPPORT | Generated support tx of {effective_amount:.2f} to {household.id}",
            extra={"tick": current_tick, "agent_id": self.government.id, "amount": effective_amount, "target_id": household.id}
        )
        return transactions

    def run_welfare_check(self, households: List[Any], market_data: Dict[str, Any], current_tick: int) -> List[Transaction]:
        """
        Identifies households in need and provides basic support.
        Returns a list of payment transactions.
        """
        transactions = []

        # 1. Calculate Survival Cost (Dynamic)
        survival_cost = self.get_survival_cost(market_data)

        # 2. Unemployment Benefit
        unemployment_ratio = getattr(self.config, "UNEMPLOYMENT_BENEFIT_RATIO", DEFAULT_UNEMPLOYMENT_BENEFIT_RATIO)
        benefit_amount = survival_cost * unemployment_ratio

        total_welfare_paid = 0.0

        for agent in households:
            if not isinstance(agent, IWelfareRecipient):
                continue

            if not agent.is_active:
                continue

            # Unemployment Benefit
            if not agent.is_employed:
                txs = self.provide_household_support(agent, benefit_amount, current_tick)
                transactions.extend(txs)
                total_welfare_paid += benefit_amount

        # 3. Stimulus Check
        current_gdp = market_data.get("total_production", 0.0)

        # TD-234: Use record_gdp encapsulation
        self.government.record_gdp(current_gdp)

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
             active_households = [a for a in households if isinstance(a, IWelfareRecipient) and a.is_active]

             total_stimulus = 0.0
             for h in active_households:
                 txs = self.provide_household_support(h, stimulus_amount, current_tick)
                 transactions.extend(txs)

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

    def get_spending_this_tick(self) -> float:
        """Returns total welfare spending for the current tick."""
        return self.spending_this_tick

    def reset_tick_flow(self) -> None:
        """Resets the per-tick spending accumulator."""
        self.spending_this_tick = 0.0

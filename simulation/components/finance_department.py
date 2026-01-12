from __future__ import annotations
from typing import List, Dict, Any, Optional, TYPE_CHECKING
import logging
from collections import deque
from simulation.models import Transaction

if TYPE_CHECKING:
    from simulation.firms import Firm
    from simulation.core_agents import Household
    from simulation.systems.reflux_system import EconomicRefluxSystem

logger = logging.getLogger(__name__)

class FinanceDepartment:
    """
    Manages maintenance fees, corporate taxes, dividend distribution, and tracks financial metrics.
    Extracted from Firm class (SoC Refactor).
    """
    def __init__(self, firm: Firm, config_module: Any):
        self.firm = firm
        self.config_module = config_module

        # Financial State
        self.retained_earnings: float = 0.0
        self.dividends_paid_last_tick: float = 0.0
        self.consecutive_loss_turns: int = 0
        self.current_profit: float = 0.0

        # Period Trackers (Reset daily usually)
        self.revenue_this_turn: float = 0.0
        self.cost_this_turn: float = 0.0
        self.revenue_this_tick: float = 0.0
        self.expenses_this_tick: float = 0.0

        # History
        self.profit_history: deque[float] = deque(maxlen=self.config_module.PROFIT_HISTORY_TICKS)
        self.last_revenue: float = 0.0
        self.last_marketing_spend: float = 0.0

        # Solvency Support
        self.last_daily_expenses: float = 10.0
        self.last_sales_volume: float = 1.0
        self.sales_volume_this_tick: float = 0.0

    def record_revenue(self, amount: float):
        self.revenue_this_turn += amount
        self.revenue_this_tick += amount
        self.current_profit += amount # Basic cash flow add

    def record_expense(self, amount: float):
        self.cost_this_turn += amount
        self.expenses_this_tick += amount
        self.current_profit -= amount

    def pay_maintenance(self, government: Any, reflux_system: Optional[EconomicRefluxSystem], current_time: int):
        """Pay fixed maintenance fee."""
        fee = getattr(self.config_module, "FIRM_MAINTENANCE_FEE", 50.0)
        payment = min(self.firm.assets, fee)

        if payment > 0:
            self.firm.assets -= payment
            self.record_expense(payment)
            government.collect_tax(payment, "firm_maintenance", self.firm.id, current_time)

            self.firm.logger.info(
                f"Paid maintenance fee: {payment:.2f}",
                extra={"tick": current_time, "agent_id": self.firm.id, "tags": ["tax", "maintenance"]}
            )

    def pay_taxes(self, government: Any, current_time: int):
        """Pay corporate tax on profit."""
        net_profit = self.revenue_this_turn - self.cost_this_turn

        if net_profit > 0:
            tax_rate = getattr(self.config_module, "CORPORATE_TAX_RATE", 0.2)
            tax_amount = net_profit * tax_rate

            payment = min(self.firm.assets, tax_amount)

            if payment > 0:
                self.firm.assets -= payment
                government.collect_tax(payment, "corporate_tax", self.firm.id, current_time)

                after_tax_profit = net_profit - payment
                self.retained_earnings += after_tax_profit

                self.firm.logger.info(
                    f"Paid corporate tax: {payment:.2f} on profit {net_profit:.2f}. Retained Earnings increased by {after_tax_profit:.2f}",
                    extra={"tick": current_time, "agent_id": self.firm.id, "tags": ["tax", "corporate_tax"]}
                )

    def distribute_dividends(self, households: List[Household], current_time: int) -> List[Transaction]:
        """Public Shareholders Dividend"""
        transactions = []
        distributable_profit = max(0, self.current_profit * self.firm.dividend_rate)

        # Reset tracker
        self.dividends_paid_last_tick = 0.0

        if distributable_profit > 0:
            for household in households:
                shares = household.shares_owned.get(self.firm.id, 0.0)
                if shares > 0:
                    dividend_amount = distributable_profit * (shares / self.firm.total_shares)
                    transactions.append(
                        Transaction(
                            buyer_id=household.id,
                            seller_id=self.firm.id,
                            item_id="dividend",
                            quantity=dividend_amount,
                            price=1.0,
                            market_id="financial",
                            transaction_type="dividend",
                            time=current_time,
                        )
                    )
                    self.dividends_paid_last_tick += dividend_amount
                    self.firm.logger.info(
                        f"Firm {self.firm.id} distributed {dividend_amount:.2f} dividend to Household {household.id}.",
                        extra={"tick": current_time, "agent_id": self.firm.id, "household_id": household.id, "amount": dividend_amount, "tags": ["dividend"]},
                    )

        # Reset period counters
        self.current_profit = 0.0
        self.revenue_this_turn = 0.0
        self.cost_this_turn = 0.0
        self.revenue_this_tick = 0.0
        self.expenses_this_tick = 0.0

        return transactions

    def distribute_profit_private(self, agents: Dict[int, Any], current_time: int) -> float:
        """Phase 14-1: Private Owner Dividend"""
        if self.firm.owner_id is None:
            return 0.0

        owner = agents.get(self.firm.owner_id)
        if owner is None:
            return 0.0

        # Required Reserves Logic
        maintenance_fee = getattr(self.config_module, "FIRM_MAINTENANCE_FEE", 0.0)

        # Query HR for wage data
        avg_wage = 0.0
        employees = self.firm.hr.employees
        if employees:
            avg_wage = sum(self.firm.hr.employee_wages.values()) / len(employees)

        reserve_period = 20
        weekly_burn_rate = maintenance_fee + (avg_wage * len(employees))
        required_reserves = weekly_burn_rate * reserve_period

        distributable_cash = self.firm.assets - required_reserves

        if distributable_cash > 0:
            dividend_amount = distributable_cash
            self.firm.assets -= dividend_amount
            owner.assets += dividend_amount

            if hasattr(owner, 'income_capital_cumulative'):
                owner.income_capital_cumulative += dividend_amount
            if hasattr(owner, 'capital_income_this_tick'):
                owner.capital_income_this_tick += dividend_amount

            self.retained_earnings -= dividend_amount
            self.dividends_paid_last_tick += dividend_amount

            if self.firm.logger:
                self.firm.logger.info(
                    f"DIVIDEND | Firm {self.firm.id} -> Household {self.firm.owner_id} : ${dividend_amount:.2f}",
                    extra={"tick": current_time, "event": "DIVIDEND", "amount": dividend_amount}
                )
            return dividend_amount

        return 0.0

    def check_bankruptcy(self):
        if self.current_profit < 0:
            self.consecutive_loss_turns += 1
        else:
            self.consecutive_loss_turns = 0

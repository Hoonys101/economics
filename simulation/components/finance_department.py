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

    def process_profit_distribution(self, households: List[Household], government: "Government", current_time: int) -> List[Transaction]:
        """Public Shareholders Dividend"""
        if getattr(self.firm, 'has_bailout_loan', False) and self.current_profit > 0:
            repayment_ratio = getattr(self.config_module, "BAILOUT_REPAYMENT_RATIO", 0.5)
            repayment = self.current_profit * repayment_ratio

            # Ensure total_debt exists before attempting to modify
            if not hasattr(self.firm, 'total_debt'):
                self.firm.total_debt = 0.0

            # Money Leak Fix: Transfer repayment to the government
            self.firm.assets -= repayment
            government.assets += repayment

            self.firm.total_debt -= repayment
            self.current_profit -= repayment
            self.firm.logger.info(f"BAILOUT_REPAYMENT | Firm {self.firm.id} repaid {repayment:.2f} of its bailout loan to the government.")

            # Check if the loan is fully repaid
            if self.firm.total_debt <= 0:
                self.firm.total_debt = 0.0
                self.firm.has_bailout_loan = False
                self.firm.logger.info(f"BAILOUT_PAID_OFF | Firm {self.firm.id} has fully repaid its bailout loan.")

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

    def add_liability(self, amount: float, interest_rate: float):
        """Adds a liability (like a loan) to the firm's balance sheet."""
        # This is a simplified implementation. A real one would track multiple loans.
        self.firm.assets += amount  # The loan increases cash assets
        # In a more complex model, this would be a separate liability account
        # For now, we'll just track the total debt.
        if not hasattr(self.firm, 'total_debt'):
            self.firm.total_debt = 0.0
        self.firm.total_debt += amount

    def calculate_altman_z_score(self) -> float:
        """Calculates the Altman Z-Score for solvency, simplified for this model.

        The formula used is a modified version for non-manufacturing or service companies:
        Z = 1.2*X1 + 1.4*X2 + 3.3*X3

        Where:
            X1 (Working Capital / Total Assets): Measures liquid assets in relation
               to the size of the company. A firm with significant working capital
               is less likely to face immediate financial distress.
               - Working Capital = Firm's cash reserves - total debt.
               - Total Assets = Cash + Capital Stock + Inventory Value.
            X2 (Retained Earnings / Total Assets): Measures cumulative profitability.
               A higher value indicates a history of reinvesting profits,
               strengthening the company's financial foundation.
            X3 (Average Profit / Total Assets): Measures recent operational efficiency.
               Uses a moving average of profit to gauge how effectively the firm
               is generating earnings from its assets.

        Returns:
            The calculated Z-Score. A score below 1.81 typically indicates a firm
            is heading for bankruptcy, while a score above 3.0 suggests a healthy
            financial position.
        """
        total_assets = self.firm.assets + self.firm.capital_stock + self.get_inventory_value()
        if total_assets == 0:
            return 0.0

        # X1: Working Capital / Total Assets
        # Working Capital = Current Assets - Current Liabilities. Assume liabilities are total_debt for now.
        working_capital = self.firm.assets - getattr(self.firm, 'total_debt', 0.0)
        x1 = working_capital / total_assets

        # X2: Retained Earnings / Total Assets
        x2 = self.retained_earnings / total_assets

        # X3: Average Profit / Total Assets
        avg_profit = sum(self.profit_history) / len(self.profit_history) if self.profit_history else 0.0
        x3 = avg_profit / total_assets

        z_score = 1.2 * x1 + 1.4 * x2 + 3.3 * x3
        return z_score

    def check_bankruptcy(self):
        if self.current_profit < 0:
            self.consecutive_loss_turns += 1
        else:
            self.consecutive_loss_turns = 0

    def get_inventory_value(self) -> float:
        """Calculate market value of current inventory."""
        total_val = 0.0
        # If inventory is dict (it is initialized as dict in __init__)
        for good, qty in self.firm.inventory.items():
             # Get price for this good
             price = self.firm.last_prices.get(good, 0.0)
             if price == 0.0:
                 # Fallback to config initial price if available
                 if self.config_module and hasattr(self.config_module, 'GOODS'):
                     price = self.config_module.GOODS.get(good, {}).get('initial_price', 10.0)
                 else:
                     price = 10.0 # Ultimate fallback
             total_val += qty * price
        return total_val

    def calculate_valuation(self) -> float:
        """
        Calculate Firm Valuation based on Net Assets + Profit Potential.
        Formula: Net Assets + (Max(0, Avg_Profit_Last_10) * PER Multiplier)
        """
        net_assets = self.firm.assets + self.get_inventory_value() + self.firm.capital_stock

        avg_profit = 0.0
        if len(self.profit_history) > 0:
            avg_profit = sum(self.profit_history) / len(self.profit_history)

        profit_premium = max(0.0, avg_profit) * getattr(self.config_module, "VALUATION_PER_MULTIPLIER", 10.0)

        self.firm.valuation = net_assets + profit_premium
        return self.firm.valuation

    def get_book_value_per_share(self) -> float:
        """주당 순자산가치(BPS)를 계산합니다. (유통주식수 기준)"""
        outstanding_shares = self.firm.total_shares - self.firm.treasury_shares
        if outstanding_shares <= 0:
            return 0.0

        # Calculate liabilities from bank loans
        liabilities = 0.0
        try:
            loan_market = getattr(self.firm.decision_engine, 'loan_market', None)
            if loan_market and hasattr(loan_market, 'bank') and loan_market.bank:
                debt_summary = loan_market.bank.get_debt_summary(self.firm.id)
                liabilities = debt_summary.get('total_principal', 0.0)
        except Exception:
            pass  # Graceful fallback

        net_assets = self.firm.assets - liabilities
        return max(0.0, net_assets) / outstanding_shares

    def get_market_cap(self, stock_price: Optional[float] = None) -> float:
        """
        시가총액을 계산합니다.

        Args:
            stock_price: 주가 (None이면 순자산가치 기반 계산)

        Returns:
            시가총액
        """
        if stock_price is None:
            stock_price = self.get_book_value_per_share()

        outstanding_shares = self.firm.total_shares - self.firm.treasury_shares
        return outstanding_shares * stock_price

    def get_financial_snapshot(self) -> Dict[str, float]:
        """
        Returns a standardized dictionary of financial metrics for monitoring and analysis.
        This provides a stable interface for CrisisMonitor and FinanceSystem.
        """
        total_assets = self.firm.assets + self.get_inventory_value()

        # Working Capital = Current Assets - Current Liabilities
        # Since we don't have long-term assets/liabilities clearly split yet,
        # we treat total assets as current and total debt as current liabilities.
        current_liabilities = getattr(self.firm, "total_debt", 0.0)
        working_capital = total_assets - current_liabilities

        # Retained Earnings
        retained_earnings = self.retained_earnings

        # Average Profit (last 10 ticks if available)
        avg_profit = self.current_profit
        if self.profit_history:
            recent = list(self.profit_history)[-10:]
            avg_profit = sum(recent) / len(recent)

        return {
            "total_assets": total_assets,
            "working_capital": working_capital,
            "retained_earnings": retained_earnings,
            "average_profit": avg_profit,
            "total_debt": current_liabilities
        }

    def liquidate_assets(self) -> float:
        """
        Liquidate assets.
        CRITICAL FIX (WO-018): Inventory and Capital Stock are written off to zero
        instead of being converted to cash, to prevent money creation from thin air.
        Only existing cash (assets) is returned.
        """
        # 1. Write off Inventory
        self.firm.inventory.clear()

        # 2. Write off Capital Stock
        self.firm.capital_stock = 0.0

        # 3. Write off Automation
        self.firm.automation_level = 0.0

        self.firm.is_bankrupt = True
        return self.firm.assets

    def issue_shares(self, quantity: float, price: float) -> float:
        """
        신규 주식을 발행합니다 (유상증자).

        Args:
            quantity: 발행할 주식 수량
            price: 주당 발행 가격

        Returns:
            조달된 자본금
        """
        if quantity <= 0 or price <= 0:
            return 0.0

        self.firm.total_shares += quantity
        raised_capital = quantity * price
        self.firm.assets += raised_capital

        self.firm.logger.info(
            f"Firm {self.firm.id} issued {quantity:.1f} shares at {price:.2f}, "
            f"raising {raised_capital:.2f} capital. Total shares: {self.firm.total_shares:.1f}",
            extra={
                "agent_id": self.firm.id,
                "quantity": quantity,
                "price": price,
                "raised_capital": raised_capital,
                "total_shares": self.firm.total_shares,
                "tags": ["stock", "issue"]
            }
        )
        return raised_capital

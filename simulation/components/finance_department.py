from __future__ import annotations
from typing import List, Dict, Any, Optional, TYPE_CHECKING
import logging
from collections import deque
from simulation.models import Transaction
from modules.finance.api import InsufficientFundsError

if TYPE_CHECKING:
    from simulation.firms import Firm
    from simulation.core_agents import Household
    from simulation.systems.reflux_system import EconomicRefluxSystem
    from simulation.agents.government import Government

logger = logging.getLogger(__name__)

class FinanceDepartment:
    """
    Manages assets, maintenance fees, corporate taxes, dividend distribution, and tracks financial metrics.
    Centralized Asset Management (WO-103 Phase 1).
    """
    def __init__(self, firm: Firm, config_module: Any, initial_capital: float = 0.0):
        self.firm = firm
        self.config_module = config_module

        # Centralized Assets (WO-103 Phase 1)
        self._cash: float = initial_capital

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

    @property
    def balance(self) -> float:
        return self._cash

    def credit(self, amount: float, description: str = "") -> None:
        """Adds funds to the firm's cash reserves."""
        # Unchecked credit. In some scenarios (correction) negative credit might be theoretically possible
        # but generally discouraged. We accept it to handle external 'assets' property setters robustly.
        self._cash += amount

    def debit(self, amount: float, description: str = "") -> None:
        """
        Deducts funds from the firm's cash reserves.
        Allows negative balance (insolvency) to be tracked rather than crashing,
        but caller should generally check funds first.
        """
        self._cash -= amount

    def calculate_and_debit_holding_costs(self, reflux_system: Optional[EconomicRefluxSystem] = None, settlement_system: Any = None) -> float:
        """Calculates and pays inventory holding costs."""
        inventory_value = self.get_inventory_value()
        holding_cost = inventory_value * self.config_module.INVENTORY_HOLDING_COST_RATE

        if holding_cost > 0:
            if settlement_system and reflux_system:
                settlement_system.transfer(self.firm, reflux_system, holding_cost, "fixed_cost")
            else:
                # Strict Mode: Log Critical
                logger.critical("FINANCE_STRICT_MODE_VIOLATION | Missing settlement or reflux system for holding costs.")

            self.record_expense(holding_cost)

        return holding_cost

    def record_revenue(self, amount: float):
        self.revenue_this_turn += amount
        self.revenue_this_tick += amount
        self.current_profit += amount

    def record_expense(self, amount: float):
        self.cost_this_turn += amount
        self.expenses_this_tick += amount
        self.current_profit -= amount

    def pay_maintenance(self, government: Government, reflux_system: Optional[EconomicRefluxSystem], current_time: int, settlement_system: Any = None):
        """Pay fixed maintenance fee."""
        fee = getattr(self.config_module, "FIRM_MAINTENANCE_FEE", 50.0)
        payment = min(self._cash, fee) # Cap at available cash

        if payment > 0:
            # Debit handled by Government -> FinanceSystem -> SettlementSystem -> Firm.withdraw
            # But wait, collect_tax handles transfer IF finance_system is set on government.
            # If not, we fallback to debit?
            # WO strictness: We rely on government.collect_tax to do the transfer.
            # government.collect_tax calls self.finance_system.collect_corporate_tax.
            # Which calls settlement_system.transfer.
            # So we don't need to manually transfer here IF government handles it.
            # BUT, if government doesn't have finance_system set up (legacy), collect_tax might fail or just log.
            # We should assume Government is compliant (Step 3).
            government.collect_tax(payment, "firm_maintenance", self.firm, current_time)
            self.record_expense(payment)

            self.firm.logger.info(
                f"Paid maintenance fee: {payment:.2f}",
                extra={"tick": current_time, "agent_id": self.firm.id, "tags": ["tax", "maintenance"]}
            )

    def pay_taxes(self, government: Government, current_time: int, settlement_system: Any = None):
        """Pay corporate tax on profit."""
        net_profit = self.revenue_this_turn - self.cost_this_turn

        if net_profit > 0:
            tax_rate = getattr(self.config_module, "CORPORATE_TAX_RATE", 0.2)
            tax_amount = net_profit * tax_rate

            payment = min(self._cash, tax_amount) # Cap at available cash

            if payment > 0:
                # Debit handled by Government -> FinanceSystem -> SettlementSystem -> Firm.withdraw
                government.collect_tax(payment, "corporate_tax", self.firm, current_time)

                after_tax_profit = net_profit - payment
                self.retained_earnings += after_tax_profit

                self.firm.logger.info(
                    f"Paid corporate tax: {payment:.2f} on profit {net_profit:.2f}. Retained Earnings increased by {after_tax_profit:.2f}",
                    extra={"tick": current_time, "agent_id": self.firm.id, "tags": ["tax", "corporate_tax"]}
                )

    def process_profit_distribution(self, households: List[Household], government: Government, current_time: int, settlement_system: Any = None) -> List[Transaction]:
        """Public Shareholders Dividend"""
        if getattr(self.firm, 'has_bailout_loan', False) and self.current_profit > 0:
            repayment_ratio = getattr(self.config_module, "BAILOUT_REPAYMENT_RATIO", 0.5)
            repayment = self.current_profit * repayment_ratio

            # Ensure total_debt exists
            if not hasattr(self.firm, 'total_debt'):
                self.firm.total_debt = 0.0

            # Bailout repayment
            if settlement_system:
                settlement_system.transfer(self.firm, government, repayment, "bailout_repayment")
            else:
                logger.critical("FINANCE_STRICT_MODE_VIOLATION | Missing settlement system for bailout repayment.")

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

                    # TransactionProcessor handles "dividend" type transactions by transferring assets.
                    # It calls settlement_system.transfer if available.
                    # So we just emit the transaction, we do NOT manually debit here.
                    # Wait, the previous code did NOT debit here either!
                    # It just appended Transaction.
                    # BUT `process_profit_distribution` calls `process_profit_distribution`... wait.
                    # The previous code logic:
                    # transactions.append(...)
                    # self.dividends_paid_last_tick += dividend_amount
                    # It relies on TransactionProcessor to execute the dividend transfer.
                    # And TransactionProcessor calls `seller.assets -= trade_value` (or settlement transfer).

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

    def distribute_profit_private(self, agents: Dict[int, Any], current_time: int, settlement_system: Any = None) -> float:
        """Phase 14-1: Private Owner Dividend"""
        if self.firm.owner_id is None:
            return 0.0

        owner = agents.get(self.firm.owner_id)
        if owner is None:
            return 0.0

        maintenance_fee = getattr(self.config_module, "FIRM_MAINTENANCE_FEE", 0.0)

        # Query HR for wage data
        avg_wage = 0.0
        employees = self.firm.hr.employees
        if employees:
            avg_wage = sum(self.firm.hr.employee_wages.values()) / len(employees)

        reserve_period = 20
        weekly_burn_rate = maintenance_fee + (avg_wage * len(employees))
        required_reserves = weekly_burn_rate * reserve_period

        distributable_cash = self._cash - required_reserves

        if distributable_cash > 0:
            dividend_amount = distributable_cash

            if settlement_system:
                settlement_system.transfer(self.firm, owner, dividend_amount, "private_dividend")
            else:
                logger.critical("FINANCE_STRICT_MODE_VIOLATION | Missing settlement system for private dividend.")

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
        self.credit(amount, "Liability Addition")
        if not hasattr(self.firm, 'total_debt'):
            self.firm.total_debt = 0.0
        self.firm.total_debt += amount

    def calculate_altman_z_score(self) -> float:
        total_assets = self._cash + self.firm.capital_stock + self.get_inventory_value()
        if total_assets == 0:
            return 0.0

        working_capital = self._cash - getattr(self.firm, 'total_debt', 0.0)
        x1 = working_capital / total_assets
        x2 = self.retained_earnings / total_assets
        avg_profit = sum(self.profit_history) / len(self.profit_history) if self.profit_history else 0.0
        x3 = avg_profit / total_assets

        z_score = 1.2 * x1 + 1.4 * x2 + 3.3 * x3
        return z_score

    def check_bankruptcy(self):
        if self.current_profit < 0:
            self.consecutive_loss_turns += 1
        else:
            self.consecutive_loss_turns = 0

    def calculate_valuation(self) -> float:
        """
        Calculate Firm Valuation based on Net Assets + Profit Potential.
        Formula: Net Assets + (Max(0, Avg_Profit_Last_10) * PER Multiplier)
        """
        net_assets = self._cash + self.get_inventory_value() + self.firm.capital_stock

        avg_profit = 0.0
        if len(self.profit_history) > 0:
            avg_profit = sum(self.profit_history) / len(self.profit_history)

        profit_premium = max(0.0, avg_profit) * getattr(self.config_module, "VALUATION_PER_MULTIPLIER", 10.0)

        self.firm.valuation = net_assets + profit_premium
        return self.firm.valuation

    def get_inventory_value(self) -> float:
        """Calculate market value of current inventory."""
        total_val = 0.0
        for good, qty in self.firm.inventory.items():
             price = self.firm.last_prices.get(good, 0.0)
             if price == 0.0:
                 if self.config_module and hasattr(self.config_module, 'GOODS'):
                     price = self.config_module.GOODS.get(good, {}).get('initial_price', 10.0)
                 else:
                     price = 10.0
             total_val += qty * price
        return total_val

    def get_financial_snapshot(self) -> Dict[str, float]:
        # WO-106: Include Capital Stock in Total Assets for correct accounting
        total_assets = self._cash + self.get_inventory_value() + getattr(self.firm, 'capital_stock', 0.0)

        current_liabilities = getattr(self.firm, "total_debt", 0.0)
        working_capital = total_assets - current_liabilities

        retained_earnings = self.retained_earnings

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

    def issue_shares(self, quantity: float, price: float) -> float:
        if quantity <= 0 or price <= 0:
            return 0.0

        self.firm.total_shares += quantity
        raised_capital = quantity * price
        self.credit(raised_capital, "Share Issue")

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

    def get_book_value_per_share(self) -> float:
        """주당 순자산가치(BPS)를 계산합니다."""
        outstanding_shares = self.firm.total_shares - self.firm.treasury_shares
        if outstanding_shares <= 0:
            return 0.0

        liabilities = 0.0
        try:
            loan_market = getattr(self.firm.decision_engine, 'loan_market', None)
            if loan_market and hasattr(loan_market, 'bank') and loan_market.bank:
                debt_summary = loan_market.bank.get_debt_summary(self.firm.id)
                liabilities = debt_summary.get('total_principal', 0.0)
        except Exception:
            pass

        net_assets = self._cash - liabilities
        return max(0.0, net_assets) / outstanding_shares

    def get_market_cap(self, stock_price: Optional[float] = None) -> float:
        if stock_price is None:
            stock_price = self.get_book_value_per_share()

        outstanding_shares = self.firm.total_shares - self.firm.treasury_shares
        return outstanding_shares * stock_price

    def get_assets(self) -> float:
        """Returns the current assets (cash) of the firm."""
        return self._cash

    def invest_in_automation(self, amount: float, settlement_system: Any = None, reflux_system: Any = None) -> bool:
        if self._cash >= amount:
            if settlement_system and reflux_system:
                settlement_system.transfer(self.firm, reflux_system, amount, "automation_investment")
            else:
                logger.critical("FINANCE_STRICT_MODE_VIOLATION | Missing settlement/reflux for automation inv.")
                return False
            return True
        return False

    def invest_in_rd(self, amount: float, settlement_system: Any = None, reflux_system: Any = None) -> bool:
        if self._cash >= amount:
            if settlement_system and reflux_system:
                settlement_system.transfer(self.firm, reflux_system, amount, "rd_investment")
            else:
                logger.critical("FINANCE_STRICT_MODE_VIOLATION | Missing settlement/reflux for RD inv.")
                return False

            self.record_expense(amount)
            return True
        return False

    def invest_in_capex(self, amount: float, settlement_system: Any = None, reflux_system: Any = None) -> bool:
        if self._cash >= amount:
            if settlement_system and reflux_system:
                settlement_system.transfer(self.firm, reflux_system, amount, "capex")
            else:
                logger.critical("FINANCE_STRICT_MODE_VIOLATION | Missing settlement/reflux for CAPEX inv.")
                return False
            return True
        return False

    def set_dividend_rate(self, rate: float) -> None:
        self.firm.dividend_rate = rate

    def pay_severance(self, employee: Household, amount: float, settlement_system: Any = None) -> bool:
        if self._cash >= amount:
            if settlement_system:
                settlement_system.transfer(self.firm, employee, amount, "severance")
            else:
                logger.critical("FINANCE_STRICT_MODE_VIOLATION | Missing settlement for severance.")
                return False

            self.record_expense(amount)
            return True
        return False

    def pay_ad_hoc_tax(self, amount: float, tax_type: str, government: Government, current_time: int) -> bool:
        if self._cash >= amount:
            # Debit handled by Government -> FinanceSystem -> SettlementSystem -> Firm.withdraw
            government.collect_tax(amount, tax_type, self.firm, current_time)
            self.record_expense(amount)
            return True
        return False

from __future__ import annotations
from typing import List, Dict, Any, Optional, TYPE_CHECKING
import logging
from collections import deque
from simulation.models import Transaction, Order
from modules.finance.api import InsufficientFundsError

if TYPE_CHECKING:
    from simulation.firms import Firm
    from simulation.dtos.config_dtos import FirmConfigDTO
    from simulation.core_agents import Household
    from modules.finance.api import IFinancialEntity

logger = logging.getLogger(__name__)

class FinanceDepartment:
    """
    Manages assets, maintenance fees, corporate taxes, dividend distribution, and tracks financial metrics.
    Centralized Asset Management (WO-103 Phase 1).
    """
    def __init__(self, firm: Firm, config: FirmConfigDTO, initial_capital: float = 0.0):
        self.firm = firm
        self.config = config

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
        self.profit_history: deque[float] = deque(maxlen=self.config.profit_history_ticks)
        self.last_revenue: float = 0.0
        self.last_marketing_spend: float = 0.0

        # Solvency Support
        self.last_daily_expenses: float = 10.0
        self.last_sales_volume: float = 1.0
        self.sales_volume_this_tick: float = 0.0

        # WO-167: Grace Protocol (Distress Mode)
        self.is_distressed: bool = False
        self.distress_tick_counter: int = 0

    @property
    def balance(self) -> float:
        return self._cash

    def credit(self, amount: float, description: str = "") -> None:
        """Adds funds to the firm's cash reserves."""
        self._cash += amount

    def debit(self, amount: float, description: str = "") -> None:
        """
        Deducts funds from the firm's cash reserves.
        """
        self._cash -= amount

    def record_revenue(self, amount: float):
        self.revenue_this_turn += amount
        self.revenue_this_tick += amount
        self.current_profit += amount

    def record_expense(self, amount: float):
        self.cost_this_turn += amount
        self.expenses_this_tick += amount
        self.current_profit -= amount

    def generate_holding_cost_transaction(self, government: IFinancialEntity, current_time: int) -> Optional[Transaction]:
        """Generates inventory holding cost transaction."""
        inventory_value = self.get_inventory_value()
        holding_cost = inventory_value * self.config.inventory_holding_cost_rate

        if holding_cost > 0:
            # We record expense so Profit calc later in tick is correct
            self.record_expense(holding_cost)

            return Transaction(
                buyer_id=self.firm.id,
                seller_id=government.id, # Capture to Gov/Reflux
                item_id="holding_cost",
                quantity=1.0,
                price=holding_cost,
                market_id="system",
                transaction_type="holding_cost",
                time=current_time
            )
        return None

    def generate_maintenance_transaction(self, government: IFinancialEntity, current_time: int) -> Optional[Transaction]:
        """Generates maintenance fee transaction."""
        fee = self.config.firm_maintenance_fee

        # Optimistic check
        payment = min(self._cash, fee)

        if payment > 0:
            self.record_expense(payment)
            self.firm.logger.info(
                f"Generated maintenance fee tx: {payment:.2f}",
                extra={"tick": current_time, "agent_id": self.firm.id, "tags": ["tax", "maintenance"]}
            )
            return Transaction(
                buyer_id=self.firm.id,
                seller_id=government.id,
                item_id="firm_maintenance",
                quantity=1.0,
                price=payment,
                market_id="system",
                transaction_type="tax",
                time=current_time
            )
        return None

    def generate_tax_transaction(self, government: IFinancialEntity, current_time: int) -> Optional[Transaction]:
        """Generates corporate tax transaction."""
        net_profit = self.revenue_this_turn - self.cost_this_turn

        if net_profit > 0:
            tax_rate = self.config.corporate_tax_rate
            tax_amount = net_profit * tax_rate

            # Optimistic check
            payment = min(self._cash, tax_amount)

            if payment > 0:
                after_tax_profit = net_profit - payment
                self.retained_earnings += after_tax_profit

                self.firm.logger.info(
                    f"Generated corporate tax tx: {payment:.2f} on profit {net_profit:.2f}.",
                    extra={"tick": current_time, "agent_id": self.firm.id, "tags": ["tax", "corporate_tax"]}
                )

                return Transaction(
                    buyer_id=self.firm.id,
                    seller_id=government.id,
                    item_id="corporate_tax",
                    quantity=1.0,
                    price=payment,
                    market_id="system",
                    transaction_type="tax",
                    time=current_time
                )
        return None

    def generate_marketing_transaction(self, government: IFinancialEntity, current_time: int, amount: float) -> Optional[Transaction]:
        """Generates marketing spend transaction."""
        if amount > 0:
            self.record_expense(amount)
            return Transaction(
                buyer_id=self.firm.id,
                seller_id=government.id, # Reflux/Gov capture
                item_id="marketing",
                quantity=1.0,
                price=amount,
                market_id="system",
                transaction_type="marketing",
                time=current_time
            )
        return None

    def process_profit_distribution(self, households: List[Household], government: IFinancialEntity, current_time: int) -> List[Transaction]:
        """
        Public Shareholders Dividend & Bailout Repayment.
        Returns List of Transactions.
        """
        transactions = []

        # 1. Bailout Repayment
        if getattr(self.firm, 'has_bailout_loan', False) and self.current_profit > 0:
            repayment_ratio = self.config.bailout_repayment_ratio
            repayment = self.current_profit * repayment_ratio

            # Optimistic update of debt state (assuming tx succeeds)
            # If it fails, we might drift. But TransactionProcessor should be reliable if funds exist.
            # We assume funds exist if current_profit > 0 (implies we made money).

            # Ensure total_debt exists
            if not hasattr(self.firm, 'total_debt'):
                self.firm.total_debt = 0.0

            transactions.append(
                Transaction(
                    buyer_id=self.firm.id,
                    seller_id=government.id,
                    item_id="bailout_repayment",
                    quantity=1.0,
                    price=repayment,
                    market_id="system",
                    transaction_type="repayment",
                    time=current_time
                )
            )

            self.firm.total_debt -= repayment
            self.current_profit -= repayment
            self.firm.logger.info(f"BAILOUT_REPAYMENT | Generated repayment tx {repayment:.2f}.")

            if self.firm.total_debt <= 0:
                self.firm.total_debt = 0.0
                self.firm.has_bailout_loan = False

        # 2. Dividends
        distributable_profit = max(0, self.current_profit * self.firm.dividend_rate)
        self.dividends_paid_last_tick = 0.0

        if distributable_profit > 0:
            for household in households:
                shares = household.shares_owned.get(self.firm.id, 0.0)
                if shares > 0:
                    dividend_amount = distributable_profit * (shares / self.firm.total_shares)
                    transactions.append(
                        Transaction(
                            buyer_id=self.firm.id,
                            seller_id=household.id,
                            item_id="dividend",
                            quantity=1.0, # 1 unit of dividend event
                            price=dividend_amount, # Cash amount
                            market_id="financial",
                            transaction_type="dividend",
                            time=current_time,
                        )
                    )
                    self.dividends_paid_last_tick += dividend_amount

        # Reset period counters
        self.current_profit = 0.0
        self.revenue_this_turn = 0.0
        self.cost_this_turn = 0.0
        self.revenue_this_tick = 0.0
        self.expenses_this_tick = 0.0

        return transactions

    def distribute_profit_private(self, agents: Dict[int, Any], government: IFinancialEntity, current_time: int) -> List[Transaction]:
        """Phase 14-1: Private Owner Dividend Transaction Generation"""
        if self.firm.owner_id is None:
            return []

        owner = agents.get(self.firm.owner_id)
        if owner is None:
            return []

        maintenance_fee = self.config.firm_maintenance_fee

        # Query HR for wage data
        avg_wage = 0.0
        employees = self.firm.hr.employees
        if employees:
            avg_wage = sum(self.firm.hr.employee_wages.values()) / len(employees)

        reserve_period = 20
        weekly_burn_rate = maintenance_fee + (avg_wage * len(employees))
        required_reserves = weekly_burn_rate * reserve_period

        distributable_cash = self._cash - required_reserves

        transactions = []
        if distributable_cash > 0:
            dividend_amount = distributable_cash

            transactions.append(
                Transaction(
                    buyer_id=self.firm.id,
                    seller_id=owner.id,
                    item_id="private_dividend",
                    quantity=1.0,
                    price=dividend_amount,
                    market_id="financial",
                    transaction_type="dividend",
                    time=current_time
                )
            )

            # Optimistic state update
            if hasattr(owner, 'income_capital_cumulative'):
                owner.income_capital_cumulative += dividend_amount
            if hasattr(owner, 'capital_income_this_tick'):
                owner.capital_income_this_tick += dividend_amount

            self.retained_earnings -= dividend_amount
            self.dividends_paid_last_tick += dividend_amount

        return transactions

    def generate_financial_transactions(self, government: IFinancialEntity, households: List[Household], current_time: int) -> List[Transaction]:
        """Consolidates all financial outflow generation logic."""
        transactions = []

        # 1. Holding Costs
        tx_holding = self.generate_holding_cost_transaction(government, current_time)
        if tx_holding:
            transactions.append(tx_holding)

        # 2. Maintenance
        tx_maint = self.generate_maintenance_transaction(government, current_time)
        if tx_maint:
            transactions.append(tx_maint)

        # 3. Corporate Tax
        tx_tax = self.generate_tax_transaction(government, current_time)
        if tx_tax:
            transactions.append(tx_tax)

        # 4. Profit Distribution (Public)
        txs_public = self.process_profit_distribution(households, government, current_time)
        transactions.extend(txs_public)

        return transactions

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

    def get_estimated_unit_cost(self, item_id: str) -> float:
        """
        Estimates the unit cost of production/operation for a given item.
        Used as a price floor for dynamic pricing.
        WO-157: Use Production Target as denominator to avoid Death Spiral (Low Sales -> High Cost -> High Price).
        """
        target = getattr(self.firm, 'production_target', 10.0)
        denominator = max(1.0, target)

        # Use last daily expenses as proxy for total cost
        return self.last_daily_expenses / denominator

    def check_bankruptcy(self):
        if self.current_profit < 0:
            self.consecutive_loss_turns += 1
        else:
            self.consecutive_loss_turns = 0

    def check_cash_crunch(self) -> bool:
        """
        WO-167: Evaluates if the firm is in a 'Cash Crunch'.
        Defined as Cash < 0 or Cash < 10% of expected expenses.
        """
        threshold = 0.1 * self.last_daily_expenses
        return self._cash < 0 or self._cash < threshold

    def trigger_emergency_liquidation(self) -> List[Order]:
        """
        WO-167: Generates emergency sell orders for all inventory items at 80% market price.
        """
        orders = []
        for good, qty in self.firm.inventory.items():
            if qty <= 0:
                continue

            # Determine price: 80% of market average, or last known price, or initial price
            price = self.firm.last_prices.get(good, 0.0)
            if price == 0.0:
                if self.config and self.config.goods:
                    price = self.config.goods.get(good, {}).get('initial_price', 10.0)
                else:
                    price = 10.0

            liquidation_price = price * 0.8

            order = Order(
                agent_id=self.firm.id,
                side="SELL",
                item_id=good,
                quantity=qty,
                price_limit=liquidation_price,
                market_id=good
            )
            orders.append(order)

            self.firm.logger.warning(
                f"GRACE_PROTOCOL | Firm {self.firm.id} triggering emergency liquidation for {good}. Qty: {qty}, Price: {liquidation_price:.2f}",
                extra={"agent_id": self.firm.id, "tags": ["grace_protocol", "liquidation"]}
            )

        return orders

    def calculate_valuation(self) -> float:
        """
        Calculate Firm Valuation based on Net Assets + Profit Potential.
        Formula: Net Assets + (Max(0, Avg_Profit_Last_10) * PER Multiplier)
        """
        net_assets = self._cash + self.get_inventory_value() + self.firm.capital_stock

        avg_profit = 0.0
        if len(self.profit_history) > 0:
            avg_profit = sum(self.profit_history) / len(self.profit_history)

        profit_premium = max(0.0, avg_profit) * self.config.valuation_per_multiplier

        self.firm.valuation = net_assets + profit_premium
        return self.firm.valuation

    def get_inventory_value(self) -> float:
        """Calculate market value of current inventory."""
        total_val = 0.0
        for good, qty in self.firm.inventory.items():
             price = self.firm.last_prices.get(good, 0.0)
             if price == 0.0:
                 if self.config and self.config.goods:
                     price = self.config.goods.get(good, {}).get('initial_price', 10.0)
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
                debt_status = loan_market.bank.get_debt_status(str(self.firm.id))
                liabilities = debt_status.get('total_outstanding_debt', 0.0)
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

    def invest_in_automation(self, amount: float, government: Optional[IFinancialEntity] = None) -> bool:
        if self._cash < amount:
            return False

        if hasattr(self.firm, 'settlement_system') and self.firm.settlement_system and government:
            transfer_success = self.firm.settlement_system.transfer(self.firm, government, amount, "Automation Investment")
            if transfer_success:
                return True
            else:
                self.firm.logger.warning(f"Automation investment of {amount:.2f} failed due to failed settlement transfer.")
                return False
        else:
            self.firm.logger.warning("INVESTMENT_BLOCKED | Missing SettlementSystem or Government for Automation.")
            return False

    def invest_in_rd(self, amount: float, government: Optional[IFinancialEntity] = None) -> bool:
        if self._cash < amount:
            return False

        if hasattr(self.firm, 'settlement_system') and self.firm.settlement_system and government:
            transfer_success = self.firm.settlement_system.transfer(self.firm, government, amount, "R&D Investment")
            if transfer_success:
                self.record_expense(amount)
                return True
            else:
                self.firm.logger.warning(f"R&D investment of {amount:.2f} failed due to failed settlement transfer.")
                return False
        else:
            self.firm.logger.warning("INVESTMENT_BLOCKED | Missing SettlementSystem or Government for R&D.")
            return False

    def invest_in_capex(self, amount: float, government: Optional[IFinancialEntity] = None) -> bool:
        if self._cash < amount:
            return False

        if hasattr(self.firm, 'settlement_system') and self.firm.settlement_system and government:
            transfer_success = self.firm.settlement_system.transfer(self.firm, government, amount, "CAPEX")
            if transfer_success:
                return True
            else:
                self.firm.logger.warning(f"CAPEX investment of {amount:.2f} failed due to failed settlement transfer.")
                return False
        else:
            self.firm.logger.warning("INVESTMENT_BLOCKED | Missing SettlementSystem or Government for CAPEX.")
            return False

    def set_dividend_rate(self, rate: float) -> None:
        self.firm.dividend_rate = rate

    def pay_severance(self, employee: Household, amount: float) -> bool:
        if self._cash >= amount:
            # AUDIT-ECONOMIC: Strictly enforce SettlementSystem.
            if hasattr(self.firm, 'settlement_system') and self.firm.settlement_system:
                if self.firm.settlement_system.transfer(self.firm, employee, amount, "Severance Pay"):
                    self.record_expense(amount)
                    return True
                return False
            else:
                self.firm.logger.critical(
                    f"PAY_SEVERANCE_FAIL | Firm {self.firm.id} missing SettlementSystem. Direct mutation blocked."
                )
                return False
        return False

    def pay_ad_hoc_tax(self, amount: float, tax_type: str, government: Any, current_time: int) -> bool:
        """
        Pay an ad-hoc tax (e.g. from internal order).
        government expected to be Government or GovernmentFiscalProxy (must have collect_tax).
        """
        if self._cash >= amount:
            # Debit handled by Government -> FinanceSystem -> SettlementSystem -> Firm.withdraw
            # Or via Proxy
            if hasattr(government, 'collect_tax'):
                government.collect_tax(amount, tax_type, self.firm, current_time)
                self.record_expense(amount)
                return True
        return False

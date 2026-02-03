from __future__ import annotations
from typing import List, Dict, Any, Optional, TYPE_CHECKING
import logging
from collections import deque
from simulation.models import Transaction, Order
from modules.finance.api import InsufficientFundsError
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY # Added for Phase 33

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
    Refactored for Multi-Currency support (Phase 33).
    """
    def __init__(self, firm: Firm, config: FirmConfigDTO, initial_capital: float = 0.0):
        self.firm = firm
        self.config = config

        # Centralized Assets (WO-103 Phase 1)
        self._balance: Dict[CurrencyCode, float] = {DEFAULT_CURRENCY: initial_capital}

        # Financial State
        self.retained_earnings: float = 0.0 # This might stay float as a net equity measure
        self.dividends_paid_last_tick: float = 0.0
        self.consecutive_loss_turns: int = 0
        self.current_profit: Dict[CurrencyCode, float] = {DEFAULT_CURRENCY: 0.0}

        # Period Trackers
        self.revenue_this_turn: Dict[CurrencyCode, float] = {DEFAULT_CURRENCY: 0.0}
        self.cost_this_turn: Dict[CurrencyCode, float] = {DEFAULT_CURRENCY: 0.0}
        self.revenue_this_tick: Dict[CurrencyCode, float] = {DEFAULT_CURRENCY: 0.0}
        self.expenses_this_tick: Dict[CurrencyCode, float] = {DEFAULT_CURRENCY: 0.0}

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
    def balance(self) -> Dict[CurrencyCode, float]:
        return self._balance

    def credit(self, amount: float, description: str = "", currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """Adds funds to the firm's cash reserves."""
        if currency not in self._balance:
            self._balance[currency] = 0.0
        self._balance[currency] += amount

    def debit(self, amount: float, description: str = "", currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """Deducts funds from the firm's cash reserves."""
        if currency not in self._balance:
            self._balance[currency] = 0.0
        self._balance[currency] -= amount

    def record_revenue(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY):
        if currency not in self.revenue_this_turn:
            self.revenue_this_turn[currency] = 0.0
            self.revenue_this_tick[currency] = 0.0
            self.current_profit[currency] = 0.0
        
        self.revenue_this_turn[currency] += amount
        self.revenue_this_tick[currency] += amount
        self.current_profit[currency] += amount

    def record_expense(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY):
        if currency not in self.cost_this_turn:
            self.cost_this_turn[currency] = 0.0
            self.expenses_this_tick[currency] = 0.0
            self.current_profit[currency] = 0.0
            
        self.cost_this_turn[currency] += amount
        self.expenses_this_tick[currency] += amount
        self.current_profit[currency] -= amount

    def generate_holding_cost_transaction(self, government: IFinancialEntity, current_time: int) -> Optional[Transaction]:
        """Generates inventory holding cost transaction."""
        inventory_value = self.get_inventory_value()
        holding_cost = inventory_value * self.config.inventory_holding_cost_rate

        if holding_cost > 0:
            self.record_expense(holding_cost)
            return Transaction(
                buyer_id=self.firm.id,
                seller_id=government.id,
                item_id="holding_cost",
                quantity=1.0,
                price=holding_cost,
                market_id="system",
                transaction_type="holding_cost",
                time=current_time,
                currency=DEFAULT_CURRENCY
            )
        return None

    def generate_maintenance_transaction(self, government: IFinancialEntity, current_time: int) -> Optional[Transaction]:
        """Generates maintenance fee transaction."""
        fee = self.config.firm_maintenance_fee
        payment = min(self._balance.get(DEFAULT_CURRENCY, 0.0), fee)

        if payment > 0:
            self.record_expense(payment)
            return Transaction(
                buyer_id=self.firm.id,
                seller_id=government.id,
                item_id="firm_maintenance",
                quantity=1.0,
                price=payment,
                market_id="system",
                transaction_type="tax",
                time=current_time,
                currency=DEFAULT_CURRENCY
            )
        return None

    def generate_marketing_transaction(self, government: IFinancialEntity, current_time: int, amount: float) -> Optional[Transaction]:
        """Generates marketing spend transaction."""
        if amount > 0:
            self.record_expense(amount)
            return Transaction(
                buyer_id=self.firm.id,
                seller_id=government.id,
                item_id="marketing",
                quantity=1.0,
                price=amount,
                market_id="system",
                transaction_type="marketing",
                time=current_time,
                currency=DEFAULT_CURRENCY
            )
        return None

    def process_profit_distribution(self, households: List[Household], government: IFinancialEntity, current_time: int) -> List[Transaction]:
        """Public Shareholders Dividend & Bailout Repayment."""
        transactions = []
        usd_profit = self.current_profit.get(DEFAULT_CURRENCY, 0.0)

        # 1. Bailout Repayment
        if getattr(self.firm, 'has_bailout_loan', False) and usd_profit > 0:
            repayment_ratio = self.config.bailout_repayment_ratio
            repayment = usd_profit * repayment_ratio

            transactions.append(
                Transaction(
                    buyer_id=self.firm.id,
                    seller_id=government.id,
                    item_id="bailout_repayment",
                    quantity=1.0,
                    price=repayment,
                    market_id="system",
                    transaction_type="repayment",
                    time=current_time,
                    currency=DEFAULT_CURRENCY
                )
            )

            if hasattr(self.firm, 'total_debt'):
                self.firm.total_debt -= repayment
            self.current_profit[DEFAULT_CURRENCY] -= repayment
            usd_profit -= repayment

            if getattr(self.firm, 'total_debt', 0.0) <= 0:
                self.firm.has_bailout_loan = False

        # 2. Dividends
        distributable_profit = max(0, usd_profit * self.firm.dividend_rate)
        self.dividends_paid_last_tick = 0.0

        if distributable_profit > 0:
            total_shares = self.firm.total_shares
            if total_shares > 0:
                for household in households:
                    shares = household._econ_state.portfolio.to_legacy_dict().get(self.firm.id, 0.0)
                    if shares > 0:
                        dividend_amount = distributable_profit * (shares / total_shares)
                        transactions.append(
                            Transaction(
                                buyer_id=self.firm.id,
                                seller_id=household.id,
                                item_id="dividend",
                                quantity=1.0,
                                price=dividend_amount,
                                market_id="financial",
                                transaction_type="dividend",
                                time=current_time,
                                currency=DEFAULT_CURRENCY
                            )
                        )
                        self.dividends_paid_last_tick += dividend_amount

        # Reset period counters
        for cur in self.current_profit:
             self.current_profit[cur] = 0.0
             self.revenue_this_turn[cur] = 0.0
             self.cost_this_turn[cur] = 0.0
             self.revenue_this_tick[cur] = 0.0
             self.expenses_this_tick[cur] = 0.0

        return transactions

    def distribute_profit_private(self, agents: Dict[int, Any], government: IFinancialEntity, current_time: int) -> List[Transaction]:
        """Phase 14-1: Private Owner Dividend Transaction Generation"""
        if self.firm.owner_id is None:
            return []

        owner = agents.get(self.firm.owner_id)
        if owner is None:
            return []

        maintenance_fee = self.config.firm_maintenance_fee
        avg_wage = 0.0
        employees = self.firm.hr.employees
        if employees:
            avg_wage = sum(self.firm.hr.employee_wages.values()) / len(employees)

        reserve_period = 20
        weekly_burn_rate = maintenance_fee + (avg_wage * len(employees))
        required_reserves = weekly_burn_rate * reserve_period

        usd_balance = self._balance.get(DEFAULT_CURRENCY, 0.0)
        distributable_cash = usd_balance - required_reserves

        transactions = []
        if distributable_cash > 0:
            transactions.append(
                Transaction(
                    buyer_id=self.firm.id,
                    seller_id=owner.id,
                    item_id="private_dividend",
                    quantity=1.0,
                    price=distributable_cash,
                    market_id="financial",
                    transaction_type="dividend",
                    time=current_time,
                    currency=DEFAULT_CURRENCY
                )
            )
            self.dividends_paid_last_tick += distributable_cash

        return transactions

    def generate_financial_transactions(self, government: IFinancialEntity, households: List[Household], current_time: int) -> List[Transaction]:
        """Consolidates all financial outflow generation logic."""
        transactions = []
        tx_holding = self.generate_holding_cost_transaction(government, current_time)
        if tx_holding: transactions.append(tx_holding)
        tx_maint = self.generate_maintenance_transaction(government, current_time)
        if tx_maint: transactions.append(tx_maint)
        txs_public = self.process_profit_distribution(households, government, current_time)
        transactions.extend(txs_public)
        return transactions

    def add_liability(self, amount: float, interest_rate: float):
        if not hasattr(self.firm, 'total_debt'):
            self.firm.total_debt = 0.0
        self.firm.total_debt += amount

    def calculate_altman_z_score(self) -> float:
        usd_balance = self._balance.get(DEFAULT_CURRENCY, 0.0)
        total_assets = usd_balance + self.firm.capital_stock + self.get_inventory_value()
        if total_assets == 0: return 0.0
        working_capital = usd_balance - getattr(self.firm, 'total_debt', 0.0)
        x1 = working_capital / total_assets
        x2 = self.retained_earnings / total_assets
        avg_profit = sum(self.profit_history) / len(self.profit_history) if self.profit_history else 0.0
        x3 = avg_profit / total_assets
        return 1.2 * x1 + 1.4 * x2 + 3.3 * x3

    def get_estimated_unit_cost(self, item_id: str) -> float:
        target = getattr(self.firm, 'production_target', 10.0)
        return self.last_daily_expenses / max(1.0, target)

    def check_bankruptcy(self):
        if self.current_profit.get(DEFAULT_CURRENCY, 0.0) < 0:
            self.consecutive_loss_turns += 1
        else:
            self.consecutive_loss_turns = 0
        threshold = getattr(self.config, "bankruptcy_consecutive_loss_threshold", 20)
        if self.consecutive_loss_turns >= threshold:
            self.firm.is_bankrupt = True

    def check_cash_crunch(self) -> bool:
        threshold = 0.1 * self.last_daily_expenses
        return self._balance.get(DEFAULT_CURRENCY, 0.0) < threshold

    def trigger_emergency_liquidation(self) -> List[Order]:
        orders = []
        for good, qty in self.firm.inventory.items():
            if qty <= 0: continue
            price = self.firm.last_prices.get(good, 10.0)
            order = Order(
                agent_id=self.firm.id, side="SELL", item_id=good,
                quantity=qty, price_limit=price * 0.8, market_id=good,
                currency=DEFAULT_CURRENCY
            )
            orders.append(order)
        return orders

    def calculate_valuation(self) -> float:
        usd_balance = self._balance.get(DEFAULT_CURRENCY, 0.0)
        net_assets = usd_balance + self.get_inventory_value() + self.firm.capital_stock
        avg_profit = sum(self.profit_history) / len(self.profit_history) if self.profit_history else 0.0
        self.firm.valuation = net_assets + max(0.0, avg_profit) * self.config.valuation_per_multiplier
        return self.firm.valuation

    def get_inventory_value(self) -> float:
        total_val = 0.0
        for good, qty in self.firm.inventory.items():
             price = self.firm.last_prices.get(good, 10.0)
             total_val += qty * price
        return total_val

    def get_financial_snapshot(self) -> Dict[str, float]:
        usd_balance = self._balance.get(DEFAULT_CURRENCY, 0.0)
        total_assets = usd_balance + self.get_inventory_value() + getattr(self.firm, 'capital_stock', 0.0)
        current_liabilities = getattr(self.firm, "total_debt", 0.0)
        avg_profit = self.current_profit.get(DEFAULT_CURRENCY, 0.0)
        if self.profit_history:
            recent = list(self.profit_history)[-10:]
            avg_profit = sum(recent) / len(recent)
        return {
            "total_assets": total_assets,
            "working_capital": total_assets - current_liabilities,
            "retained_earnings": self.retained_earnings,
            "average_profit": avg_profit,
            "total_debt": current_liabilities
        }

    def issue_shares(self, quantity: float, price: float) -> float:
        if quantity <= 0 or price <= 0: return 0.0
        self.firm.total_shares += quantity
        return quantity * price

    def get_book_value_per_share(self) -> float:
        outstanding_shares = self.firm.total_shares - self.firm.treasury_shares
        if outstanding_shares <= 0: return 0.0
        debt = getattr(self.firm, 'total_debt', 0.0)
        net_assets = self._balance.get(DEFAULT_CURRENCY, 0.0) - debt
        return max(0.0, net_assets) / outstanding_shares

    def get_market_cap(self, stock_price: Optional[float] = None) -> float:
        if stock_price is None: stock_price = self.get_book_value_per_share()
        return (self.firm.total_shares - self.firm.treasury_shares) * stock_price

    def get_assets(self) -> float:
        return self._balance.get(DEFAULT_CURRENCY, 0.0)

    def invest_in_automation(self, amount: float, government: Optional[IFinancialEntity] = None) -> bool:
        if self._balance.get(DEFAULT_CURRENCY, 0.0) < amount: return False
        if not self.firm.settlement_system or not government: return False
        return self.firm.settlement_system.transfer(self.firm, government, amount, "Automation", currency=DEFAULT_CURRENCY)

    def invest_in_rd(self, amount: float, government: Optional[IFinancialEntity] = None) -> bool:
        if self._balance.get(DEFAULT_CURRENCY, 0.0) < amount: return False
        if not self.firm.settlement_system or not government: return False
        if self.firm.settlement_system.transfer(self.firm, government, amount, "R&D", currency=DEFAULT_CURRENCY):
            self.record_expense(amount)
            return True
        return False

    def invest_in_capex(self, amount: float, government: Optional[IFinancialEntity] = None) -> bool:
        if self._balance.get(DEFAULT_CURRENCY, 0.0) < amount: return False
        if not self.firm.settlement_system or not government: return False
        return self.firm.settlement_system.transfer(self.firm, government, amount, "CAPEX", currency=DEFAULT_CURRENCY)

    def set_dividend_rate(self, rate: float) -> None:
        self.firm.dividend_rate = rate

    def pay_severance(self, employee: Household, amount: float) -> bool:
        if self._balance.get(DEFAULT_CURRENCY, 0.0) >= amount and self.firm.settlement_system:
            if self.firm.settlement_system.transfer(self.firm, employee, amount, "Severance", currency=DEFAULT_CURRENCY):
                self.record_expense(amount)
                return True
        return False

    def pay_ad_hoc_tax(self, amount: float, tax_type: str, government: Any, current_time: int) -> bool:
        if self._balance.get(DEFAULT_CURRENCY, 0.0) >= amount and self.firm.settlement_system:
            if self.firm.settlement_system.transfer(self.firm, government, amount, tax_type, currency=DEFAULT_CURRENCY):
                self.record_expense(amount)
                return True
        return False

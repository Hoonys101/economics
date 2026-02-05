from __future__ import annotations
from typing import List, Dict, Any, Optional, TYPE_CHECKING, Union
import logging
from collections import deque
from simulation.models import Transaction, Order
from modules.finance.api import IFinancialEntity, InsufficientFundsError, IFinanceDepartment
from modules.finance.dtos import MoneyDTO, MultiCurrencyWalletDTO
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY

if TYPE_CHECKING:
    from simulation.firms import Firm
    from simulation.dtos.config_dtos import FirmConfigDTO
    from simulation.core_agents import Household

logger = logging.getLogger(__name__)

class FinanceDepartment(IFinanceDepartment):
    """
    Manages assets, maintenance fees, corporate taxes, dividend distribution, and tracks financial metrics.
    Centralized Asset Management (WO-103 Phase 1).
    Refactored for Multi-Currency support (Phase 33, TD-213-B).
    """
    def __init__(self, firm: Firm, config: FirmConfigDTO, initial_capital: float = 0.0):
        self.firm = firm
        self.config = config
        self.primary_currency: CurrencyCode = DEFAULT_CURRENCY # Could be from config in future

        # Financial State
        self.retained_earnings: float = 0.0 # Kept as float (primary currency equivalent)
        self.dividends_paid_last_tick: float = 0.0 # Primary currency equivalent
        self.consecutive_loss_turns: int = 0
        self.current_profit: Dict[CurrencyCode, float] = {DEFAULT_CURRENCY: 0.0}

        # Period Trackers
        self.revenue_this_turn: Dict[CurrencyCode, float] = {DEFAULT_CURRENCY: 0.0}
        self.cost_this_turn: Dict[CurrencyCode, float] = {DEFAULT_CURRENCY: 0.0}
        self.revenue_this_tick: Dict[CurrencyCode, float] = {DEFAULT_CURRENCY: 0.0}
        self.expenses_this_tick: Dict[CurrencyCode, float] = {DEFAULT_CURRENCY: 0.0}

        # History
        self.profit_history: deque[float] = deque(maxlen=self.config.profit_history_ticks) # In primary currency
        self.last_revenue: float = 0.0 # In primary currency
        self.last_marketing_spend: float = 0.0 # In primary currency

        # Solvency Support
        self.last_daily_expenses: float = 10.0 # In primary currency
        self.last_sales_volume: float = 1.0
        self.sales_volume_this_tick: float = 0.0

        # WO-167: Grace Protocol (Distress Mode)
        self.is_distressed: bool = False
        self.distress_tick_counter: int = 0

    @property
    def balance(self) -> Dict[CurrencyCode, float]:
        return self.firm.wallet.get_all_balances()

    def get_balance(self, currency: CurrencyCode) -> float:
        return self.firm.wallet.get_balance(currency)

    def deposit(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """Deposits a specific amount of a given currency."""
        self.firm.wallet.add(amount, currency)

    def withdraw(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """Withdraws a specific amount of a given currency. Raises InsufficientFundsError."""
        current_bal = self.firm.wallet.get_balance(currency)
        if current_bal < amount:
            raise InsufficientFundsError(
                f"Insufficient funds for withdrawal",
                required=MoneyDTO(amount=amount, currency=currency),
                available=MoneyDTO(amount=current_bal, currency=currency)
            )
        self.firm.wallet.subtract(amount, currency)

    def credit(self, amount: float, description: str = "", currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """Legacy helper: Adds funds to the firm's cash reserves."""
        self.deposit(amount, currency)

    def debit(self, amount: float, description: str = "", currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """Legacy helper: Deducts funds from the firm's cash reserves."""
        self.withdraw(amount, currency)

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

    def _convert_to_primary(self, amount: float, currency: CurrencyCode, exchange_rates: Dict[CurrencyCode, float]) -> float:
        """Helper to convert any currency to primary currency."""
        if currency == self.primary_currency:
            return amount
        # Rate is 1 unit of Currency = X units of DEFAULT_CURRENCY?
        # Typically exchange rates are relative to DEFAULT_CURRENCY (USD).
        # Assuming exchange_rates[CUR] is price of CUR in USD.
        # If primary is USD, then amount * rate.
        rate = exchange_rates.get(currency, 0.0)
        # If rate is 0/missing, assume 0 value or 1.0 parity? Spec says use exchange_rates.
        # Assuming exchange_rates has valid rates.
        return amount * rate

    def generate_holding_cost_transaction(self, government: IFinancialEntity, current_time: int) -> Optional[Transaction]:
        """Generates inventory holding cost transaction."""
        # This uses get_inventory_value which currently assumes hardcoded price logic.
        # We'll stick to primary currency for internal cost calculation for now.
        inventory_value = self.get_inventory_value() # Returns float (assumed primary)
        holding_cost = inventory_value * self.config.inventory_holding_cost_rate

        if holding_cost > 0:
            self.record_expense(holding_cost, self.primary_currency)
            return Transaction(
                buyer_id=self.firm.id,
                seller_id=government.id,
                item_id="holding_cost",
                quantity=1.0,
                price=holding_cost,
                market_id="system",
                transaction_type="holding_cost",
                time=current_time,
                currency=self.primary_currency
            )
        return None

    def generate_maintenance_transaction(self, government: IFinancialEntity, current_time: int) -> Optional[Transaction]:
        """Generates maintenance fee transaction."""
        fee = self.config.firm_maintenance_fee
        current_balance = self.firm.wallet.get_balance(self.primary_currency)
        payment = min(current_balance, fee)

        if payment > 0:
            self.record_expense(payment, self.primary_currency)
            return Transaction(
                buyer_id=self.firm.id,
                seller_id=government.id,
                item_id="firm_maintenance",
                quantity=1.0,
                price=payment,
                market_id="system",
                transaction_type="tax",
                time=current_time,
                currency=self.primary_currency
            )
        return None

    def generate_marketing_transaction(self, government: IFinancialEntity, current_time: int, amount: float) -> Optional[Transaction]:
        """
        Generates marketing spend transaction.
        Amount is expected to be in primary currency.
        """
        if amount > 0:
            self.record_expense(amount, self.primary_currency)
            return Transaction(
                buyer_id=self.firm.id,
                seller_id=government.id,
                item_id="marketing",
                quantity=1.0,
                price=amount,
                market_id="system",
                transaction_type="marketing",
                time=current_time,
                currency=self.primary_currency
            )
        return None

    def process_profit_distribution(self, households: List[Household], government: IFinancialEntity, current_time: int, exchange_rates: Dict[CurrencyCode, float]) -> List[Transaction]:
        """Public Shareholders Dividend & Bailout Repayment (Multi-Currency)."""
        transactions = []

        # Calculate total profit in primary currency for history tracking
        total_profit_primary = 0.0
        for cur, profit in self.current_profit.items():
            total_profit_primary += self._convert_to_primary(profit, cur, exchange_rates)

        self.profit_history.append(total_profit_primary)

        # Bailout Repayment (Only in Primary Currency usually, but let's check debt currency)
        # Assuming debt is in primary currency (USD)
        usd_profit = self.current_profit.get(DEFAULT_CURRENCY, 0.0)

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
            usd_profit -= repayment # Update local var

            if getattr(self.firm, 'total_debt', 0.0) <= 0:
                self.firm.has_bailout_loan = False

        # Dividends (Multi-Currency)
        self.dividends_paid_last_tick = 0.0

        total_shares = self.firm.total_shares

        for cur, profit in self.current_profit.items():
            distributable_profit = max(0, profit * self.firm.dividend_rate)
            if distributable_profit > 0 and total_shares > 0:
                # Add to total paid (converted)
                self.dividends_paid_last_tick += self._convert_to_primary(distributable_profit, cur, exchange_rates)

                for household in households:
                    # TD-233: Use portfolio property (LoD fix)
                    shares = household.portfolio.get_stock_quantity(self.firm.id)
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
                                currency=cur
                            )
                        )

        # Reset period counters
        # TD-213-B: Update last_revenue before reset
        total_revenue_primary = 0.0
        for cur, amount in self.revenue_this_turn.items():
            total_revenue_primary += self._convert_to_primary(amount, cur, exchange_rates)
        self.last_revenue = total_revenue_primary

        for cur in list(self.current_profit.keys()): # List copy to avoid runtime error if we modify keys
             self.current_profit[cur] = 0.0
             self.revenue_this_turn[cur] = 0.0
             self.cost_this_turn[cur] = 0.0
             self.revenue_this_tick[cur] = 0.0
             self.expenses_this_tick[cur] = 0.0

        return transactions

    def generate_financial_transactions(self, government: IFinancialEntity, households: List[Household], current_time: int, exchange_rates: Dict[CurrencyCode, float]) -> List[Transaction]:
        """Consolidates all financial outflow generation logic."""
        transactions = []
        tx_holding = self.generate_holding_cost_transaction(government, current_time)
        if tx_holding: transactions.append(tx_holding)
        tx_maint = self.generate_maintenance_transaction(government, current_time)
        if tx_maint: transactions.append(tx_maint)
        txs_public = self.process_profit_distribution(households, government, current_time, exchange_rates)
        transactions.extend(txs_public)
        return transactions

    def add_liability(self, amount: float, interest_rate: float):
        if not hasattr(self.firm, 'total_debt'):
            self.firm.total_debt = 0.0
        self.firm.total_debt += amount

    def calculate_altman_z_score(self, exchange_rates: Optional[Dict[CurrencyCode, float]] = None) -> float:
        # TD-240: Multi-currency support
        if exchange_rates is None:
            exchange_rates = {DEFAULT_CURRENCY: 1.0}

        # Calculate Total Assets (Sum of all currencies converted + Capital + Inventory)
        usd_balance = 0.0
        for cur, amount in self.firm.wallet.get_all_balances().items():
             usd_balance += self._convert_to_primary(amount, cur, exchange_rates)

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
        # Bankruptcy based on primary currency profit or total?
        # Logic says: "consecutive loss turns".
        # We track profit history in primary currency.
        # But here we check self.current_profit before reset?
        # Wait, check_bankruptcy is usually called BEFORE profit distribution/reset?
        # If check_bankruptcy assumes current_profit is not yet reset, we need to sum it up.

        # NOTE: logic in original was: `if self.current_profit.get(DEFAULT_CURRENCY, 0.0) < 0:`
        # We should check total profit converted.
        # But we might not have exchange rates here easily.
        # Let's rely on primary currency profit for simplicity/robustness if rates not avail.
        # OR, assuming check_bankruptcy is called in a context where we just check primary.

        primary_profit = self.current_profit.get(self.primary_currency, 0.0)

        if primary_profit < 0:
            self.consecutive_loss_turns += 1
        else:
            self.consecutive_loss_turns = 0

        threshold = getattr(self.config, "bankruptcy_consecutive_loss_threshold", 20)
        if self.consecutive_loss_turns >= threshold:
            self.firm.is_bankrupt = True

    def check_cash_crunch(self) -> bool:
        threshold = 0.1 * self.last_daily_expenses
        return self.firm.wallet.get_balance(self.primary_currency) < threshold

    def trigger_emergency_liquidation(self) -> List[Order]:
        orders = []
        for good, qty in self.firm.inventory.items():
            if qty <= 0: continue
            price = self.firm.last_prices.get(good, 10.0)
            order = Order(
                agent_id=self.firm.id, side="SELL", item_id=good,
                quantity=qty, price_limit=price * 0.8, market_id=good,
                currency=self.primary_currency
            )
            orders.append(order)
        return orders

    def calculate_valuation(self, exchange_rates: Dict[CurrencyCode, float] = None) -> MoneyDTO:
        """
        Calculates the firm's total valuation, converted to its primary currency.
        """
        if exchange_rates is None:
            exchange_rates = {DEFAULT_CURRENCY: 1.0}

        total_assets_val = 0.0
        # Cash
        for cur, amount in self.firm.wallet.get_all_balances().items():
            total_assets_val += self._convert_to_primary(amount, cur, exchange_rates)

        # Inventory & Capital Stock (Assuming priced in primary)
        total_assets_val += self.get_inventory_value() + self.firm.capital_stock

        avg_profit = sum(self.profit_history) / len(self.profit_history) if self.profit_history else 0.0
        valuation_amt = total_assets_val + max(0.0, avg_profit) * self.config.valuation_per_multiplier

        self.firm.valuation = valuation_amt # Store float in firm for legacy/cache

        return MoneyDTO(amount=valuation_amt, currency=self.primary_currency)

    def get_inventory_value(self) -> float:
        total_val = 0.0
        for good, qty in self.firm.inventory.items():
             price = self.firm.last_prices.get(good, 10.0)
             total_val += qty * price
        return total_val

    def get_financial_snapshot(self) -> Dict[str, Union[MoneyDTO, MultiCurrencyWalletDTO, float]]:
        """
        Returns a comprehensive, currency-aware snapshot.
        """
        wallet_dto = MultiCurrencyWalletDTO(balances=self.firm.wallet.get_all_balances())

        # Total assets (estimated in primary for float fields, or return wallet)
        # Spec says: Dict[str, MoneyDTO | MultiCurrencyWalletDTO]
        # But existing code expects keys like "working_capital" as floats maybe?
        # We will provide structured data.

        # Calculating legacy float metrics for backward compat where feasible
        usd_balance = self.firm.wallet.get_balance(DEFAULT_CURRENCY)
        total_assets = usd_balance + self.get_inventory_value() + getattr(self.firm, 'capital_stock', 0.0)
        current_liabilities = getattr(self.firm, "total_debt", 0.0)

        avg_profit = 0.0
        if self.profit_history:
            recent = list(self.profit_history)[-10:]
            avg_profit = sum(recent) / len(recent)

        return {
            "wallet": wallet_dto,
            "total_assets_est": MoneyDTO(amount=total_assets, currency=DEFAULT_CURRENCY), # Approximate
            "working_capital_est": MoneyDTO(amount=total_assets - current_liabilities, currency=DEFAULT_CURRENCY),
            "retained_earnings_dto": MoneyDTO(amount=self.retained_earnings, currency=self.primary_currency),
            "average_profit_dto": MoneyDTO(amount=avg_profit, currency=self.primary_currency),
            "total_debt": MoneyDTO(amount=current_liabilities, currency=DEFAULT_CURRENCY),
            # Legacy keys (float) if needed by other systems (optional but helpful)
            "total_assets": total_assets,
            "working_capital": total_assets - current_liabilities,
            "retained_earnings": self.retained_earnings,
            "average_profit": avg_profit,
        }

    def issue_shares(self, quantity: float, price: float) -> float:
        if quantity <= 0 or price <= 0: return 0.0
        self.firm.total_shares += quantity
        return quantity * price

    def get_book_value_per_share(self) -> MoneyDTO:
        outstanding_shares = self.firm.total_shares - self.firm.treasury_shares
        if outstanding_shares <= 0:
            return MoneyDTO(amount=0.0, currency=self.primary_currency)

        debt = getattr(self.firm, 'total_debt', 0.0)
        # Net Assets in primary currency
        net_assets = self.firm.wallet.get_balance(self.primary_currency) - debt
        # Note: This ignores other currency holdings if not converted.
        # Ideally should convert all, but requires exchange rates which we don't have here easily.
        # Assuming book value is roughly primary currency based.

        val = max(0.0, net_assets) / outstanding_shares
        return MoneyDTO(amount=val, currency=self.primary_currency)

    def get_market_cap(self, stock_price: Optional[float] = None) -> float:
        # Returns float (primary currency)
        if stock_price is None:
            bv = self.get_book_value_per_share()
            stock_price = bv['amount']
        return (self.firm.total_shares - self.firm.treasury_shares) * stock_price

    def get_assets(self) -> float:
        """Legacy accessor: returns primary currency balance."""
        return self.firm.wallet.get_balance(self.primary_currency)

    def invest_in_automation(self, amount: float, government: Optional[IFinancialEntity] = None) -> bool:
        if self.firm.wallet.get_balance(self.primary_currency) < amount: return False
        if not self.firm.settlement_system or not government: return False
        return self.firm.settlement_system.transfer(self.firm, government, amount, "Automation", currency=self.primary_currency)

    def invest_in_rd(self, amount: float, government: Optional[IFinancialEntity] = None) -> bool:
        if self.firm.wallet.get_balance(self.primary_currency) < amount: return False
        if not self.firm.settlement_system or not government: return False
        if self.firm.settlement_system.transfer(self.firm, government, amount, "R&D", currency=self.primary_currency):
            self.record_expense(amount, self.primary_currency)
            return True
        return False

    def invest_in_capex(self, amount: float, government: Optional[IFinancialEntity] = None) -> bool:
        if self.firm.wallet.get_balance(self.primary_currency) < amount: return False
        if not self.firm.settlement_system or not government: return False
        return self.firm.settlement_system.transfer(self.firm, government, amount, "CAPEX", currency=self.primary_currency)

    def set_dividend_rate(self, new_rate: float) -> None:
        self.firm.dividend_rate = new_rate

    def pay_severance(self, employee: Household, amount: float) -> bool:
        if self.firm.wallet.get_balance(self.primary_currency) >= amount and self.firm.settlement_system:
            if self.firm.settlement_system.transfer(self.firm, employee, amount, "Severance", currency=self.primary_currency):
                self.record_expense(amount, self.primary_currency)
                return True
        return False

    def pay_ad_hoc_tax(self, amount: float, currency: CurrencyCode, reason: str, government: Any, current_time: int) -> None:
        if self.firm.wallet.get_balance(currency) >= amount and self.firm.settlement_system:
            if self.firm.settlement_system.transfer(self.firm, government, amount, reason, currency=currency):
                self.record_expense(amount, currency)

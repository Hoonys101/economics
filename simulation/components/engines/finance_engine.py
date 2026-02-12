from __future__ import annotations
from typing import List, Dict, Any, Optional, TYPE_CHECKING
import logging
from simulation.models import Transaction, Order
from simulation.components.state.firm_state_models import FinanceState
from modules.finance.api import InsufficientFundsError, IShareholderRegistry
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY
from modules.finance.dtos import MoneyDTO, MultiCurrencyWalletDTO
from simulation.dtos.context_dtos import FinancialTransactionContext

if TYPE_CHECKING:
    from simulation.dtos.config_dtos import FirmConfigDTO

logger = logging.getLogger(__name__)

class FinanceEngine:
    """
    Stateless Engine for Finance operations.
    Manages asset tracking, transaction generation, and financial health metrics.
    MIGRATION: Uses integer pennies for transactions and state.
    """

    def generate_financial_transactions(
        self,
        state: FinanceState,
        firm_id: int,
        balances: Dict[CurrencyCode, int],
        config: FirmConfigDTO,
        current_time: int,
        context: FinancialTransactionContext,
        inventory_value: float # Float dollars passed from orchestrator
    ) -> List[Transaction]:
        """
        Consolidates all financial outflow generation logic.
        """
        transactions = []
        gov_id = context.government_id

        # 1. Holding Cost
        # Inventory value is float dollars. Rate is float. Cost is float dollars.
        # Convert to pennies.
        holding_cost_float = inventory_value * config.inventory_holding_cost_rate
        holding_cost_pennies = int(holding_cost_float * 100)

        if holding_cost_pennies > 0 and gov_id is not None:
            self._record_expense(state, holding_cost_pennies, DEFAULT_CURRENCY)
            transactions.append(
                Transaction(
                    buyer_id=firm_id,
                    seller_id=gov_id,
                    item_id="holding_cost",
                    quantity=1.0,
                    price=holding_cost_pennies,
                    market_id="system",
                    transaction_type="holding_cost",
                    time=current_time,
                    currency=DEFAULT_CURRENCY
                )
            )

        # 2. Maintenance Fee
        fee_float = config.firm_maintenance_fee
        fee_pennies = int(fee_float * 100)

        current_balance = balances.get(DEFAULT_CURRENCY, 0)
        payment = min(current_balance, fee_pennies)

        if payment > 0 and gov_id is not None:
            self._record_expense(state, payment, DEFAULT_CURRENCY)
            transactions.append(
                Transaction(
                    buyer_id=firm_id,
                    seller_id=gov_id,
                    item_id="firm_maintenance",
                    quantity=1.0,
                    price=payment,
                    market_id="system",
                    transaction_type="tax",
                    time=current_time,
                    currency=DEFAULT_CURRENCY
                )
            )

        # 3. Profit Distribution (Dividends & Bailout Repayment)
        txs_public = self._process_profit_distribution(
            state, firm_id, config, current_time, context
        )
        transactions.extend(txs_public)

        return transactions

    def _record_expense(self, state: FinanceState, amount: int, currency: CurrencyCode):
        if currency not in state.cost_this_turn:
            state.cost_this_turn[currency] = 0
            state.expenses_this_tick[currency] = 0
            state.current_profit[currency] = 0

        state.cost_this_turn[currency] += amount
        state.expenses_this_tick[currency] += amount
        state.current_profit[currency] -= amount

    def _process_profit_distribution(
        self,
        state: FinanceState,
        firm_id: int,
        config: FirmConfigDTO,
        current_time: int,
        context: FinancialTransactionContext
    ) -> List[Transaction]:
        """Internal helper for dividends and bailout repayment."""
        transactions = []
        exchange_rates = context.market_context.get('exchange_rates', {})
        gov_id = context.government_id
        registry = context.shareholder_registry

        # Helper
        def convert(amt: int, cur: str) -> int:
            if cur == DEFAULT_CURRENCY: return amt
            rate = exchange_rates.get(cur, 1.0)
            return int(amt * rate)

        # 1. Update Profit History
        total_profit_primary = 0
        for cur, profit in state.current_profit.items():
            total_profit_primary += convert(profit, cur)

        state.profit_history.append(total_profit_primary)

        # 2. Bailout Repayment
        usd_profit = state.current_profit.get(DEFAULT_CURRENCY, 0)
        if state.has_bailout_loan and usd_profit > 0 and gov_id is not None:
            repayment_ratio = config.bailout_repayment_ratio
            repayment = int(usd_profit * repayment_ratio)

            if repayment > 0:
                transactions.append(
                    Transaction(
                        buyer_id=firm_id,
                        seller_id=gov_id,
                        item_id="bailout_repayment",
                        quantity=1.0,
                        price=repayment,
                        market_id="system",
                        transaction_type="repayment",
                        time=current_time,
                        currency=DEFAULT_CURRENCY
                    )
                )

                state.total_debt_pennies -= repayment
                state.current_profit[DEFAULT_CURRENCY] -= repayment
                if state.total_debt_pennies <= 0:
                    state.has_bailout_loan = False

        # 3. Dividends
        state.dividends_paid_last_tick_pennies = 0
        shareholders = registry.get_shareholders_of_firm(firm_id) if registry else []

        for cur, profit in state.current_profit.items():
            distributable_profit = max(0, int(profit * state.dividend_rate))
            if distributable_profit > 0 and state.total_shares > 0 and shareholders:
                state.dividends_paid_last_tick_pennies += convert(distributable_profit, cur)

                for shareholder in shareholders:
                    shares = shareholder['quantity']
                    agent_id = shareholder['agent_id']

                    if agent_id == firm_id: continue # Treasury shares

                    if shares > 0:
                        # Share ratio is float. Result is pennies.
                        dividend_amount = int(distributable_profit * (shares / state.total_shares))
                        transactions.append(
                            Transaction(
                                buyer_id=firm_id,
                                seller_id=agent_id,
                                item_id="dividend",
                                quantity=1.0,
                                price=dividend_amount,
                                market_id="financial",
                                transaction_type="dividend",
                                time=current_time,
                                currency=cur
                            )
                        )

        # 4. Reset Period Counters
        total_revenue_primary = 0
        for cur, amount in state.revenue_this_turn.items():
            total_revenue_primary += convert(amount, cur)
        state.last_revenue_pennies = total_revenue_primary

        for cur in list(state.current_profit.keys()):
             state.current_profit[cur] = 0
             state.revenue_this_turn[cur] = 0
             state.cost_this_turn[cur] = 0

        return transactions

    def check_bankruptcy(self, state: FinanceState, config: FirmConfigDTO):
        """Checks bankruptcy condition based on consecutive losses."""
        primary_profit = state.current_profit.get(DEFAULT_CURRENCY, 0)

        if primary_profit < 0:
            state.consecutive_loss_turns += 1
        else:
            state.consecutive_loss_turns = 0

        threshold = config.bankruptcy_consecutive_loss_threshold
        if state.consecutive_loss_turns >= threshold:
            state.is_bankrupt = True

    def calculate_valuation(
        self,
        state: FinanceState,
        balances: Dict[CurrencyCode, int],
        config: FirmConfigDTO,
        inventory_value: float,
        capital_stock: float,
        context: Optional[FinancialTransactionContext]
    ) -> int:
        """
        Calculates firm valuation in pennies.
        """
        exchange_rates = context.market_context.get('exchange_rates', {}) if context else {DEFAULT_CURRENCY: 1.0}

        def convert(amt: int, cur: str) -> int:
            rate = exchange_rates.get(cur, 1.0) if cur != DEFAULT_CURRENCY else 1.0
            return int(amt * rate)

        total_assets_val = 0
        for cur, amount in balances.items():
             total_assets_val += convert(amount, cur)

        # Add Inventory & Capital (convert from float dollars to pennies)
        total_assets_val += int(inventory_value * 100)
        total_assets_val += int(capital_stock * 100)

        # Profit is int pennies
        avg_profit = sum(state.profit_history) / len(state.profit_history) if state.profit_history else 0.0

        valuation = total_assets_val + int(max(0.0, avg_profit) * config.valuation_per_multiplier)

        state.valuation_pennies = valuation
        return valuation

    def invest_in_automation(
        self,
        state: FinanceState,
        firm_id: int,
        balances: Dict[CurrencyCode, int],
        amount: int,
        context: FinancialTransactionContext,
        current_time: int
    ) -> Optional[Transaction]:
        """
        Creates investment transaction for automation.
        """
        current_balance = balances.get(DEFAULT_CURRENCY, 0)
        if current_balance < amount:
            return None

        if context.government_id is None:
            return None

        return Transaction(
            buyer_id=firm_id,
            seller_id=context.government_id,
            item_id="Automation",
            quantity=1.0,
            price=amount,
            market_id="system",
            transaction_type="investment",
            time=current_time,
            currency=DEFAULT_CURRENCY
        )

    def invest_in_rd(
        self,
        state: FinanceState,
        firm_id: int,
        balances: Dict[CurrencyCode, int],
        amount: int,
        context: FinancialTransactionContext,
        current_time: int
    ) -> Optional[Transaction]:
        """
        Creates investment transaction for R&D.
        """
        current_balance = balances.get(DEFAULT_CURRENCY, 0)
        if current_balance < amount:
            return None

        if context.government_id is None:
            return None

        return Transaction(
            buyer_id=firm_id,
            seller_id=context.government_id,
            item_id="R&D",
            quantity=1.0,
            price=amount,
            market_id="system",
            transaction_type="investment",
            time=current_time,
            currency=DEFAULT_CURRENCY
        )

    def invest_in_capex(
        self,
        state: FinanceState,
        firm_id: int,
        balances: Dict[CurrencyCode, int],
        amount: int,
        context: FinancialTransactionContext,
        current_time: int
    ) -> Optional[Transaction]:
        """
        Creates investment transaction for CAPEX.
        """
        current_balance = balances.get(DEFAULT_CURRENCY, 0)
        if current_balance < amount:
            return None

        if context.government_id is None:
            return None

        return Transaction(
            buyer_id=firm_id,
            seller_id=context.government_id,
            item_id="CAPEX",
            quantity=1.0,
            price=amount,
            market_id="system",
            transaction_type="investment",
            time=current_time,
            currency=DEFAULT_CURRENCY
        )

    def pay_ad_hoc_tax(
        self,
        state: FinanceState,
        firm_id: int,
        balances: Dict[CurrencyCode, int],
        amount: int,
        currency: CurrencyCode,
        reason: str,
        context: FinancialTransactionContext,
        current_time: int
    ) -> Optional[Transaction]:
        """
        Creates tax payment transaction.
        """
        current_balance = balances.get(currency, 0)
        if current_balance < amount:
            return None

        if context.government_id is None:
            return None

        return Transaction(
            buyer_id=firm_id,
            seller_id=context.government_id,
            item_id=reason,
            quantity=1.0,
            price=amount,
            market_id="system",
            transaction_type="tax",
            time=current_time,
            currency=currency
        )

    def record_expense(self, state: FinanceState, amount: int, currency: CurrencyCode):
        """Public method to record expense (e.g. after successful transaction execution)."""
        self._record_expense(state, amount, currency)

    def get_estimated_unit_cost(self, state: FinanceState, item_id: str, config: FirmConfigDTO) -> float:
        """
        Estimates unit cost for pricing floors (Returns float dollars).
        """
        # 1. Try Config Base Cost
        goods_config = config.goods.get(item_id, {})
        base_cost = goods_config.get("base_cost", 0.0)
        if base_cost > 0:
            return base_cost

        # 2. Heuristic: Total Expenses / Total Production (if available)
        return config.default_unit_cost

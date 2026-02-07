from __future__ import annotations
from typing import List, Dict, Any, Optional, TYPE_CHECKING
import logging
from simulation.models import Transaction, Order
from simulation.components.state.firm_state_models import FinanceState
from modules.finance.api import IFinancialEntity, InsufficientFundsError, IShareholderRegistry
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY, MarketContextDTO
from modules.finance.dtos import MoneyDTO, MultiCurrencyWalletDTO

if TYPE_CHECKING:
    from simulation.dtos.config_dtos import FirmConfigDTO

logger = logging.getLogger(__name__)

class FinanceEngine:
    """
    Stateless Engine for Finance operations.
    Manages asset tracking, transaction generation, and financial health metrics.
    """

    def generate_financial_transactions(
        self,
        state: FinanceState,
        firm_id: int,
        wallet: IFinancialEntity,
        config: FirmConfigDTO,
        government: Any,
        shareholder_registry: IShareholderRegistry,
        current_time: int,
        market_context: MarketContextDTO,
        inventory_value: float # Passed from orchestrator
    ) -> List[Transaction]:
        """
        Consolidates all financial outflow generation logic.
        """
        transactions = []

        # 1. Holding Cost
        holding_cost = inventory_value * config.inventory_holding_cost_rate
        if holding_cost > 0:
            self._record_expense(state, holding_cost, DEFAULT_CURRENCY)
            transactions.append(
                Transaction(
                    buyer_id=firm_id,
                    seller_id=government.id,
                    item_id="holding_cost",
                    quantity=1.0,
                    price=holding_cost,
                    market_id="system",
                    transaction_type="holding_cost",
                    time=current_time,
                    currency=DEFAULT_CURRENCY
                )
            )

        # 2. Maintenance Fee
        fee = config.firm_maintenance_fee
        current_balance = wallet.get_balance(DEFAULT_CURRENCY) if hasattr(wallet, 'get_balance') else wallet.assets
        payment = min(current_balance, fee)

        if payment > 0:
            self._record_expense(state, payment, DEFAULT_CURRENCY)
            transactions.append(
                Transaction(
                    buyer_id=firm_id,
                    seller_id=government.id,
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
            state, firm_id, config, shareholder_registry, government, current_time, market_context
        )
        transactions.extend(txs_public)

        return transactions

    def _record_expense(self, state: FinanceState, amount: float, currency: CurrencyCode):
        if currency not in state.cost_this_turn:
            state.cost_this_turn[currency] = 0.0
            state.expenses_this_tick[currency] = 0.0
            state.current_profit[currency] = 0.0

        state.cost_this_turn[currency] += amount
        state.expenses_this_tick[currency] += amount
        state.current_profit[currency] -= amount

    def _process_profit_distribution(
        self,
        state: FinanceState,
        firm_id: int,
        config: FirmConfigDTO,
        shareholder_registry: IShareholderRegistry,
        government: Any,
        current_time: int,
        market_context: MarketContextDTO
    ) -> List[Transaction]:
        """Internal helper for dividends and bailout repayment."""
        transactions = []
        exchange_rates = market_context['exchange_rates']

        # Helper
        def convert(amt, cur):
            if cur == DEFAULT_CURRENCY: return amt
            rate = exchange_rates.get(cur, 0.0)
            return amt * rate

        # 1. Update Profit History
        total_profit_primary = 0.0
        for cur, profit in state.current_profit.items():
            total_profit_primary += convert(profit, cur)

        state.profit_history.append(total_profit_primary)

        # 2. Bailout Repayment
        usd_profit = state.current_profit.get(DEFAULT_CURRENCY, 0.0)
        if state.has_bailout_loan and usd_profit > 0:
            repayment_ratio = config.bailout_repayment_ratio
            repayment = usd_profit * repayment_ratio

            transactions.append(
                Transaction(
                    buyer_id=firm_id,
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

            state.total_debt -= repayment
            state.current_profit[DEFAULT_CURRENCY] -= repayment
            if state.total_debt <= 0:
                state.has_bailout_loan = False

        # 3. Dividends
        state.dividends_paid_last_tick = 0.0
        shareholders = shareholder_registry.get_shareholders_of_firm(firm_id)

        for cur, profit in state.current_profit.items():
            distributable_profit = max(0, profit * state.dividend_rate)
            if distributable_profit > 0 and state.total_shares > 0 and shareholders:
                state.dividends_paid_last_tick += convert(distributable_profit, cur)

                for shareholder in shareholders:
                    shares = shareholder['quantity']
                    agent_id = shareholder['agent_id']

                    if agent_id == firm_id: continue # Treasury shares

                    if shares > 0:
                        dividend_amount = distributable_profit * (shares / state.total_shares)
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
        total_revenue_primary = 0.0
        for cur, amount in state.revenue_this_turn.items():
            total_revenue_primary += convert(amount, cur)
        state.last_revenue = total_revenue_primary

        for cur in list(state.current_profit.keys()):
             state.current_profit[cur] = 0.0
             state.revenue_this_turn[cur] = 0.0
             state.cost_this_turn[cur] = 0.0
             # Note: revenue_this_tick and expenses_this_tick are reset in finalize_tick

        return transactions

    def check_bankruptcy(self, state: FinanceState, config: FirmConfigDTO):
        """Checks bankruptcy condition based on consecutive losses."""
        # Check primary currency profit as proxy
        primary_profit = state.current_profit.get(DEFAULT_CURRENCY, 0.0)

        if primary_profit < 0:
            state.consecutive_loss_turns += 1
        else:
            state.consecutive_loss_turns = 0

        threshold = getattr(config, "bankruptcy_consecutive_loss_threshold", 20)
        if state.consecutive_loss_turns >= threshold:
            state.is_bankrupt = True

    def calculate_valuation(
        self,
        state: FinanceState,
        wallet: IFinancialEntity,
        config: FirmConfigDTO,
        inventory_value: float,
        market_context: Optional[MarketContextDTO]
    ) -> float:
        """Calculates firm valuation."""
        exchange_rates = market_context['exchange_rates'] if market_context else {DEFAULT_CURRENCY: 1.0}

        def convert(amt, cur):
            rate = exchange_rates.get(cur, 1.0) if cur != DEFAULT_CURRENCY else 1.0
            return amt * rate

        # Total Assets (Cash + Inventory + Capital)
        total_assets_val = 0.0
        # Cash
        if hasattr(wallet, 'get_all_balances'):
             for cur, amount in wallet.get_all_balances().items():
                 total_assets_val += convert(amount, cur)
        else:
             total_assets_val = wallet.assets

        total_assets_val += inventory_value + state.capital_stock # Assume capital stock in primary val

        avg_profit = sum(state.profit_history) / len(state.profit_history) if state.profit_history else 0.0
        valuation = total_assets_val + max(0.0, avg_profit) * config.valuation_per_multiplier

        state.valuation = valuation # Cache
        return valuation

    def invest_in_automation(
        self,
        state: FinanceState,
        wallet: IFinancialEntity,
        amount: float,
        government: Any,
        settlement_system: Any
    ) -> bool:
        """
        Executes investment in automation.
        """
        # Balance check
        current_balance = wallet.get_balance(DEFAULT_CURRENCY) if hasattr(wallet, 'get_balance') else wallet.assets
        if current_balance < amount:
            return False

        if not settlement_system or not government:
            return False

        return settlement_system.transfer(wallet, government, amount, "Automation", currency=DEFAULT_CURRENCY)

    def invest_in_rd(
        self,
        state: FinanceState,
        wallet: IFinancialEntity,
        amount: float,
        government: Any,
        settlement_system: Any
    ) -> bool:
        """
        Executes investment in R&D. Records expense.
        """
        current_balance = wallet.get_balance(DEFAULT_CURRENCY) if hasattr(wallet, 'get_balance') else wallet.assets
        if current_balance < amount:
            return False

        if not settlement_system or not government:
            return False

        if settlement_system.transfer(wallet, government, amount, "R&D", currency=DEFAULT_CURRENCY):
            self._record_expense(state, amount, DEFAULT_CURRENCY)
            return True
        return False

    def invest_in_capex(
        self,
        state: FinanceState,
        wallet: IFinancialEntity,
        amount: float,
        government: Any,
        settlement_system: Any
    ) -> bool:
        """
        Executes investment in CAPEX.
        """
        current_balance = wallet.get_balance(DEFAULT_CURRENCY) if hasattr(wallet, 'get_balance') else wallet.assets
        if current_balance < amount:
            return False

        if not settlement_system or not government:
            return False

        return settlement_system.transfer(wallet, government, amount, "CAPEX", currency=DEFAULT_CURRENCY)

    def pay_ad_hoc_tax(
        self,
        state: FinanceState,
        wallet: IFinancialEntity,
        amount: float,
        currency: CurrencyCode,
        reason: str,
        government: Any,
        settlement_system: Any,
        current_time: int
    ) -> bool:
        """
        Pays an ad-hoc tax.
        """
        current_balance = wallet.get_balance(currency) if hasattr(wallet, 'get_balance') else wallet.assets
        if current_balance < amount:
            return False

        if settlement_system.transfer(wallet, government, amount, reason, currency=currency):
            self._record_expense(state, amount, currency)
            return True
        return False

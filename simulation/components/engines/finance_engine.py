from __future__ import annotations
from typing import List, Dict, Any, Optional, TYPE_CHECKING
import logging
from simulation.models import Transaction, Order
from simulation.components.state.firm_state_models import FinanceState
from modules.finance.api import InsufficientFundsError, IShareholderRegistry
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY
from modules.finance.dtos import MoneyDTO, MultiCurrencyWalletDTO
from simulation.dtos.context_dtos import FinancialTransactionContext
from modules.firm.api import FinanceDecisionInputDTO, BudgetPlanDTO, IFinanceEngine

if TYPE_CHECKING:
    from modules.simulation.dtos.api import FirmConfigDTO

logger = logging.getLogger(__name__)

class FinanceEngine(IFinanceEngine):
    """
    Stateless Engine for Finance operations.
    Manages asset tracking, transaction generation, and financial health metrics.
    MIGRATION: Uses integer pennies for transactions and state.
    """

    def plan_budget(self, input_dto: FinanceDecisionInputDTO) -> BudgetPlanDTO:
        """
        Plans the budget for the upcoming tick based on current state and priorities.
        """
        firm_snapshot = input_dto.firm_snapshot
        finance_state = firm_snapshot.finance
        balance = finance_state.balance.get(DEFAULT_CURRENCY, 0)

        # 1. Solvency Check (Operating Runway)
        # Assuming simple rule: Keep 2 ticks of expenses as buffer if possible
        # We don't have explicit "last tick total expenses" easily accessible in DTO
        # except logic or history.
        # But we can look at cost_this_turn if it was from previous tick?
        # FinanceState has expenses_this_tick. If snapshot is taken before reset, it has last tick's expenses.
        # But reset happens at end of tick. Decision happens in Phase 1.
        # So expenses_this_tick is from *current* tick (0 so far).
        # We can use profit_history or heuristics.

        total_budget = balance

        # Priorities:
        # 1. Debt Repayment (if mandated or critical)
        # 2. Labor (Wages)
        # 3. Production (Inputs) - Not explicitly budgeted here but part of OPEX
        # 4. Marketing
        # 5. Capital/Automation (Investment)
        # 6. Dividends

        # Debt
        debt_repayment = 0
        # AI Debt Awareness: Use explicit DTO fields
        total_debt = getattr(finance_state, 'total_debt_pennies', 0)
        avg_interest_rate = getattr(finance_state, 'average_interest_rate', 0.0)

        # 1. Budget for Interest (Committed)
        estimated_interest = 0
        if total_debt > 0:
            # Daily interest approximation (assuming 365 ticks/year default)
            estimated_interest = int(total_debt * avg_interest_rate / 365)
            # Ensure we don't budget more than we have
            allocated_interest = min(estimated_interest, total_budget)
            total_budget -= allocated_interest

        # 2. Budget for Principal Repayment
        if total_debt > 0:
            # Strategy: If distressed (low Z-score or losses), prioritize deleveraging
            is_distressed = (finance_state.altman_z_score < 1.8) or (finance_state.consecutive_loss_turns > 4)
            repayment_rate = 0.05 if is_distressed else 0.005 # 5% vs 0.5% per tick

            target_repayment = int(total_debt * repayment_rate)
            debt_repayment = min(target_repayment, total_budget)
            total_budget -= debt_repayment

        # Dividend
        dividend_payout = 0
        # Only pay dividends if we have excess cash?
        # Usually dividends are from profits, handled in generate_financial_transactions.
        # But here we set a "budget" cap.
        # If generate_financial_transactions handles it based on profit, we can set this to 0 or MAX.
        # Let's say we reserve amount equal to last profit * dividend_rate
        last_profit = finance_state.profit_history[-1] if finance_state.profit_history else 0
        if last_profit > 0:
            dividend_payout = int(last_profit * finance_state.dividend_rate)
            # But we don't subtract from budget yet, as this is "planned"
            # And dividend is usually paid after OPEX.

        # Labor Budget
        # Estimate from current employees
        # current_wage_bill = sum(w for w in firm_snapshot.hr.employees_data.values().wage)
        # But we need to allow for hiring.
        # Let's give 50% of remaining liquid assets to Labor + Production?
        # Or use System2 guidance?

        # For now, simple allocation:
        # Reserve for Survival/Maintenance?

        # We return the "Plan" which acts as constraints for other engines.

        # Strategy Adjustment
        strategy = firm_snapshot.strategy
        marketing_priority = 0.1
        capital_priority = 0.1

        if str(strategy) == "FirmStrategy.MARKET_SHARE":
            marketing_priority = 0.3
        elif str(strategy) == "FirmStrategy.PROFIT_MAXIMIZATION":
            capital_priority = 0.2

        available_for_ops = total_budget

        labor_budget = int(available_for_ops * 0.6)
        marketing_budget = int(available_for_ops * marketing_priority)
        capital_budget = int(available_for_ops * capital_priority)

        # Ensure we have enough for current employees?
        # That logic is in HREngine (fire if can't pay).
        # Here we just say "You have X to spend".

        return BudgetPlanDTO(
            total_budget_pennies=balance,
            labor_budget_pennies=labor_budget,
            capital_budget_pennies=capital_budget,
            marketing_budget_pennies=marketing_budget,
            dividend_payout_pennies=dividend_payout,
            debt_repayment_pennies=debt_repayment,
            is_solvent=balance > 0 # Simple solvency check
        )

    def generate_financial_transactions(
        self,
        state: FinanceState,
        firm_id: int,
        balances: Dict[CurrencyCode, int],
        config: FirmConfigDTO,
        current_time: int,
        context: FinancialTransactionContext,
        inventory_value: int # MIGRATION: Int pennies
    ) -> List[Transaction]:
        """
        Consolidates all financial outflow generation logic.
        """
        transactions = []
        gov_id = context.government_id

        # 1. Holding Cost
        # Inventory value is int pennies. Rate is float.
        holding_cost_float = inventory_value * config.inventory_holding_cost_rate
        holding_cost_pennies = int(holding_cost_float)

        if holding_cost_pennies > 0 and gov_id is not None:
            transactions.append(
                Transaction(
                    buyer_id=firm_id,
                    seller_id=gov_id,
                    item_id="holding_cost",
                    quantity=1.0,
                    price=holding_cost_pennies / 100.0,
                    market_id="system",
                    transaction_type="holding_cost",
                    time=current_time,
                    currency=DEFAULT_CURRENCY
                , total_pennies=holding_cost_pennies)
            )

        # 2. Maintenance Fee
        fee_pennies = config.firm_maintenance_fee

        current_balance = balances.get(DEFAULT_CURRENCY, 0)
        payment = min(current_balance, fee_pennies)

        if payment > 0 and gov_id is not None:
            transactions.append(
                Transaction(
                    buyer_id=firm_id,
                    seller_id=gov_id,
                    item_id="firm_maintenance",
                    quantity=1.0,
                    price=payment / 100.0,
                    market_id="system",
                    transaction_type="tax",
                    time=current_time,
                    currency=DEFAULT_CURRENCY
                , total_pennies=payment)
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
        exchange_rates = context.market_context.exchange_rates or {}
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
                        price=repayment / 100.0,
                        market_id="system",
                        transaction_type="repayment",
                        time=current_time,
                        currency=DEFAULT_CURRENCY
                    , total_pennies=repayment)
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
                                price=dividend_amount / 100.0,
                                market_id="financial",
                                transaction_type="dividend",
                                time=current_time,
                                currency=cur
                            , total_pennies=dividend_amount)
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
        inventory_value: int, # MIGRATION: Int pennies
        capital_stock: int, # MIGRATION: Int pennies
        context: Optional[FinancialTransactionContext]
    ) -> int:
        """
        Calculates firm valuation in pennies.
        """
        exchange_rates = (context.market_context.exchange_rates or {}) if context else {DEFAULT_CURRENCY: 1.0}

        def convert(amt: int, cur: str) -> int:
            rate = exchange_rates.get(cur, 1.0) if cur != DEFAULT_CURRENCY else 1.0
            return int(amt * rate)

        total_assets_val = 0
        for cur, amount in balances.items():
             total_assets_val += convert(amount, cur)

        # Add Inventory & Capital (Already in pennies)
        total_assets_val += inventory_value
        total_assets_val += capital_stock

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
            price=amount / 100.0,
            market_id="system",
            transaction_type="investment",
            time=current_time,
            currency=DEFAULT_CURRENCY
        , total_pennies=amount)

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
            price=amount / 100.0,
            market_id="system",
            transaction_type="investment",
            time=current_time,
            currency=DEFAULT_CURRENCY
        , total_pennies=amount)

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
            price=amount / 100.0,
            market_id="system",
            transaction_type="investment",
            time=current_time,
            currency=DEFAULT_CURRENCY
        , total_pennies=amount)

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
            price=amount / 100.0,
            market_id="system",
            transaction_type="tax",
            time=current_time,
            currency=currency
        , total_pennies=amount)

    def record_expense(self, state: FinanceState, amount: int, currency: CurrencyCode):
        """Public method to record expense (e.g. after successful transaction execution)."""
        self._record_expense(state, amount, currency)

    def get_estimated_unit_cost(self, state: FinanceState, item_id: str, config: FirmConfigDTO) -> int:
        """
        Estimates unit cost for pricing floors (Returns int pennies).
        """
        # 1. Try Config Base Cost
        goods_config = config.goods.get(item_id, {})
        base_cost = goods_config.get("base_cost", 0) # MIGRATION: int
        if base_cost > 0:
            return base_cost

        # 2. Heuristic: Total Expenses / Total Production (if available)
        return config.default_unit_cost

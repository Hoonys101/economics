from typing import Any, List, Tuple
import logging
from simulation.systems.api import ITransactionHandler, TransactionContext
from simulation.models import Transaction
from simulation.core_agents import Household, Skill
from simulation.firms import Firm
from modules.system.api import DEFAULT_CURRENCY
from modules.finance.utils.currency_math import round_to_pennies
from modules.finance.api import IIncomeTracker

logger = logging.getLogger(__name__)

class LaborTransactionHandler(ITransactionHandler):
    """
    Handles 'labor' and 'research_labor' transactions.
    Enforces atomic settlement (Wage + Income Tax).
    """

    def handle(self, tx: Transaction, buyer: Any, seller: Any, context: TransactionContext) -> bool:
        # SSoT: Use total_pennies directly (Strict Schema Enforced)
        trade_value = tx.total_pennies

        # 1. Prepare Settlement (Calculate tax intents)
        # Note: TransactionProcessor used market_data.get("goods_market")?
        # But TaxationSystem.calculate_tax_intents signature expects 'market_data'.
        intents = context.taxation_system.calculate_tax_intents(tx, buyer, seller, context.government, context.market_data)

        credits: List[Tuple[Any, int, str]] = []
        seller_net_amount = trade_value
        buyer_total_cost = trade_value

        # Variables for logging or tracking
        seller_tax_paid = 0
        buyer_tax_paid = 0

        for intent in intents:
            amount_int = int(intent.amount)
            credits.append((context.government, amount_int, intent.reason))
            if intent.payer_id == seller.id:
                # If Seller (Worker) pays, deduct from their receipt (Withholding)
                seller_net_amount -= amount_int
                seller_tax_paid += amount_int
            elif intent.payer_id == buyer.id:
                # If Buyer (Firm) pays, it's extra cost
                buyer_total_cost += amount_int
                buyer_tax_paid += amount_int

        # Add Net Wage Credit to Seller
        credits.append((seller, int(seller_net_amount), f"labor_wage:{tx.transaction_type}"))

        # 2. Execute Settlement (Atomic)
        # Buyer pays Total Cost (Gross + Buyer Tax) implicitly by covering all credits
        # Actually settle_atomic sums up credits.
        # Credits = [Tax1, Tax2, SellerNet]
        # Sum = Tax1 + Tax2 + (Trade - TaxSeller)
        # If Buyer pays TaxBuyer (Tax1) and Seller pays TaxSeller (Tax2):
        # Total Debit = TaxBuyer + TaxSeller + (Trade - TaxSeller) = TaxBuyer + Trade
        # This matches buyer_total_cost. Correct.

        settlement_success = context.settlement_system.settle_atomic(buyer, credits, context.time)

        # 3. Apply Side-Effects
        if settlement_success:
            # Record Revenue for Tax Purposes
            for intent in intents:
                context.government.record_revenue({
                     "success": True,
                     "amount_collected": intent.amount,
                     "tax_type": intent.reason,
                     "payer_id": intent.payer_id,
                     "payee_id": intent.payee_id,
                     "error_message": None
                })

            self._apply_labor_effects(tx, buyer, seller, seller_net_amount, buyer_total_cost, context)

        return settlement_success

    def _apply_labor_effects(self, tx: Transaction, buyer: Any, seller: Any, seller_net_income: int, buyer_total_cost: int, context: TransactionContext):
        """
        Applies employment updates and productivity effects.
        """
        # 1. Household Logic (Seller)
        if isinstance(seller, Household):
            if seller.is_employed and seller.employer_id is not None and seller.employer_id != buyer.id:
                # Need to remove from previous employer
                previous_employer = context.agents.get(seller.employer_id) or context.inactive_agents.get(seller.employer_id)
                if isinstance(previous_employer, Firm):
                    previous_employer.hr_engine.remove_employee(previous_employer.hr_state, seller)

            seller.is_employed = True
            seller.employer_id = buyer.id
            # Use trade_value (gross wage) for current_wage_pennies
            # Assuming trade_value equals the gross wage for the period
            trade_value = tx.total_pennies
            seller.current_wage_pennies = trade_value
            seller.needs["labor_need"] = 0.0

            # Net Income Tracking
            if isinstance(seller, IIncomeTracker):
                seller.add_labor_income(int(seller_net_income))

        # 2. Firm Logic (Buyer)
        if isinstance(buyer, Firm):
            trade_value = tx.total_pennies
            # HR Update
            if seller not in buyer.hr_state.employees:
                buyer.hr_engine.hire(buyer.hr_state, seller, trade_value, context.time)
            else:
                 buyer.hr_state.employee_wages[seller.id] = trade_value

            # Finance Update
            buyer.finance_engine.record_expense(buyer.finance_state, int(buyer_total_cost), DEFAULT_CURRENCY)

            # Research Labor Productivity Boost
            if tx.transaction_type == "research_labor" and isinstance(seller, Household):
                research_skill = seller.skills.get("research", Skill("research")).value
                multiplier = getattr(context.config_module, "RND_PRODUCTIVITY_MULTIPLIER", 0.0)
                buyer.productivity_factor += (research_skill * multiplier)

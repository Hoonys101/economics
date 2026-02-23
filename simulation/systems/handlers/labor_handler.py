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
        print(f"DEBUG_LABOR_HANDLER | Handling {tx.transaction_type} for {buyer.id} -> {seller.id}")
        try:
            # SSoT: Use total_pennies directly (Strict Schema Enforced)
            trade_value = tx.total_pennies

            # Special Handling for HIRE (Phase 4.1): No financial transfer, just state update
            if tx.transaction_type == "HIRE":
                # Extract mismatch penalty from metadata if available
                # Logic: major_compatibility influences initial productivity or training cost?
                # We will store a productivity modifier in the firm's HR state.
                self._apply_labor_effects(tx, buyer, seller, 0, 0, context)
                return True

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
        except Exception as e:
            print(f"DEBUG_LABOR_HANDLER | ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _apply_labor_effects(self, tx: Transaction, buyer: Any, seller: Any, seller_net_income: int, buyer_total_cost: int, context: TransactionContext):
        """
        Applies employment updates and productivity effects.
        """
        # 1. Household Logic (Seller)
        if isinstance(seller, Household):
            if seller.is_employed and seller.employer_id is not None and seller.employer_id != buyer.id:
                # Need to remove from previous employer
                # context.agents is a dict of ID -> Agent
                # However, in TransactionProcessor, context.agents might not be fully populated in mocks.
                # Use robust lookup or pass explicit dependency if possible.
                # Assuming context.agents works.
                prev_id = seller.employer_id
                if context.agents and prev_id in context.agents:
                    previous_employer = context.agents[prev_id]
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
            # For HIRE transactions, net_income passed is 0, so this adds 0 (Correct).
            if isinstance(seller, IIncomeTracker):
                seller.add_labor_income(int(seller_net_income))

        # 2. Firm Logic (Buyer)
        if isinstance(buyer, Firm):
            trade_value = tx.total_pennies
            # HR Update
            if seller not in buyer.hr_state.employees:
                buyer.hr_engine.hire(buyer.hr_state, seller, trade_value, context.time)

                # Phase 4.1: Apply Mismatch Penalty (Skill Modifier)
                if tx.metadata:
                    compatibility = tx.metadata.get("major_compatibility", "MISMATCH")
                    modifier = 1.0
                    if compatibility == "MISMATCH":
                        modifier = 0.8
                    elif compatibility == "PARTIAL":
                        modifier = 0.9

                    # Store modifier in employee data (HRState)
                    # HREngine.hire adds to employees list, but we need to update employees_data dict
                    if seller.id not in buyer.hr_state.employees_data:
                        buyer.hr_state.employees_data[seller.id] = {}

                    # Apply penalty to skill record directly in Firm's view (not Agent's true skill)
                    # We can store 'skill_modifier' which ProductionEngine should use.
                    # Or simpler: Pre-multiply the skill stored in employees_data.
                    # However, employees_data entries usually mirror agent state.
                    # Let's add a 'productivity_modifier' field.
                    buyer.hr_state.employees_data[seller.id]["productivity_modifier"] = modifier

            else:
                 buyer.hr_state.employee_wages[seller.id] = trade_value

            # Finance Update (Skip if cost is 0, e.g. HIRE)
            if buyer_total_cost > 0:
                buyer.finance_engine.record_expense(buyer.finance_state, int(buyer_total_cost), DEFAULT_CURRENCY)

            # Research Labor Productivity Boost
            if tx.transaction_type == "research_labor" and isinstance(seller, Household):
                research_skill = seller.skills.get("research", Skill("research")).value
                multiplier = getattr(context.config_module, "RND_PRODUCTIVITY_MULTIPLIER", 0.0)
                buyer.productivity_factor += (research_skill * multiplier)

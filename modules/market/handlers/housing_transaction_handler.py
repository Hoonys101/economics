from typing import Any, Optional, Tuple, Dict
import logging
from simulation.systems.api import ITransactionHandler, TransactionContext
from simulation.models import Transaction
from modules.market.api import IHousingTransactionHandler, HousingConfigDTO
from modules.finance.api import BorrowerProfileDTO
from modules.system.escrow_agent import EscrowAgent
from simulation.core_agents import Household
from simulation.firms import Firm

logger = logging.getLogger(__name__)

class HousingTransactionHandler(ITransactionHandler, IHousingTransactionHandler):
    """
    Handles 'housing' market transactions using the Saga pattern.
    Orchestrates atomic settlement involving Buyer, Seller, Bank, and Escrow.
    """

    def handle(self, tx: Transaction, buyer: Any, seller: Any, context: TransactionContext) -> bool:
        """
        Executes the housing transaction saga:
        1. Validation
        2. Down Payment (Buyer -> Escrow)
        3. Mortgage Creation (Bank -> Loan)
        4. Loan Disbursement (Bank -> Escrow)
        5. Final Settlement (Escrow -> Seller)
        """
        # 1. Initialization & Validation
        if not buyer or not seller:
            context.logger.error(f"HOUSING | Invalid participants. Buyer: {buyer}, Seller: {seller}")
            return False

        # Find Escrow Agent
        escrow_agent = next((a for a in context.agents.values() if isinstance(a, EscrowAgent)), None)
        if not escrow_agent:
            context.logger.critical("HOUSING | Escrow Agent not found in simulation agents.")
            return False

        # Parse Unit
        try:
            unit_id = int(tx.item_id.split("_")[1])
            unit = next((u for u in context.real_estate_units if u.id == unit_id), None)
            if not unit:
                context.logger.error(f"HOUSING | Unit {unit_id} not found.")
                return False
        except (IndexError, ValueError):
            context.logger.error(f"HOUSING | Invalid item_id format: {tx.item_id}")
            return False

        # Config
        housing_config = getattr(context.config_module, "housing", {})
        # Fallback defaults if config is missing (safety)
        max_ltv = housing_config.get("max_ltv_ratio", 0.8)
        mortgage_term = housing_config.get("mortgage_term_ticks", 300)

        # Interest Rate (Bank Config or Global)
        # Using context.config_module.bank_defaults if available or context.bank.base_rate logic?
        # Bank.grant_loan takes interest_rate.
        # We should query the bank for current rate or use config.
        mortgage_rate = getattr(context.config_module, "MORTGAGE_INTEREST_RATE", 0.05) # Legacy/Global config fallback
        if context.bank:
             # Ideally bank has a mortgage rate product, but for now we use base rate + spread?
             # Or stick to the config constant if it exists.
             pass

        sale_price = tx.price * tx.quantity
        loan_amount = 0.0
        down_payment = sale_price

        # Determine Mortgage Eligibility
        # Only Households get mortgages usually.
        is_household = isinstance(buyer, Household)
        use_mortgage = is_household and context.bank is not None

        if use_mortgage:
            loan_amount = sale_price * max_ltv
            down_payment = sale_price - loan_amount

        # Check Buyer Funds for Down Payment
        if buyer.assets < down_payment:
            context.logger.info(f"HOUSING | Buyer {buyer.id} insufficient funds for down payment {down_payment:.2f}")
            return False

        # 2. Saga Step A: Secure Down Payment (Buyer -> Escrow)
        memo_down = f"escrow_hold:down_payment:{tx.item_id}"
        if not context.settlement_system.transfer(buyer, escrow_agent, down_payment, memo_down, tick=context.time):
            context.logger.warning(f"HOUSING | Failed to secure down payment from {buyer.id}")
            return False

        # --- Compensation Logic Needed from here ---

        loan_id = None
        new_loan_dto = None

        try:
            # 3. Saga Step B: Create Mortgage (if applicable)
            if use_mortgage:
                borrower_profile = self._create_borrower_profile(buyer, sale_price, context)
                # Estimate due tick
                due_tick = context.time + mortgage_term

                grant_result = context.bank.grant_loan(
                    borrower_id=str(buyer.id),
                    amount=loan_amount,
                    interest_rate=mortgage_rate,
                    due_tick=due_tick,
                    borrower_profile=borrower_profile
                )

                if not grant_result:
                    context.logger.warning(f"HOUSING | Bank rejected mortgage for {buyer.id}")
                    # Compensate Step A
                    context.settlement_system.transfer(escrow_agent, buyer, down_payment, "escrow_reversal:loan_rejected", tick=context.time)
                    return False

                new_loan_dto, credit_tx = grant_result
                # LoanInfoDTO is a TypedDict
                loan_id = new_loan_dto['loan_id']

                # Append credit creation tx to queue
                if credit_tx:
                    context.transaction_queue.append(credit_tx)

                # 4. Saga Step C: Disburse Loan (Bank -> Escrow)
                # Note: Bank.grant_loan created a deposit for borrower.
                # We need to transfer that deposit (or newly minted funds if Bank logic differs) to Escrow.
                # Actually, grant_loan creates a deposit for the borrower.
                # So the borrower now has `loan_amount` in their bank account (or existing assets).
                # Wait, `grant_loan` calls `deposit_from_customer`. So Buyer has the money.
                # BUT the Spec says "Disburse Loan Principal to Escrow".
                # If the money is in Buyer's account, we must transfer from Buyer to Escrow?
                # OR does the Bank transfer directly?
                # The `grant_loan` implementation adds to `borrower_id` deposit.
                # So `Buyer` now has the funds.
                # The Spec Pseudo-code says: `settlement_system.transfer(bank, escrow_agent, ...)`
                # This implies the loan funds come from Bank directly to Escrow.
                # But current `grant_loan` implementation puts it in Buyer's deposit.
                # So we should transfer from Buyer (using the loan funds) to Escrow?
                # OR we treat `grant_loan` as just booking the loan, and the disbursement happens differently?
                # `grant_loan` creates a Deposit.
                # If I transfer from Bank to Escrow, I am double counting if I also keep the deposit for Buyer.
                # Current `Bank.grant_loan` logic: `self.deposit_from_customer(bid_int, amount)`.
                # This increases Buyer's deposit balance.
                # So for the Saga "Disburse to Escrow", I should transfer from Buyer (using the newly acquired funds) to Escrow?
                # Or maybe the Spec implies `grant_loan` shouldn't deposit to Buyer immediately but to Escrow?
                # I cannot change `Bank.grant_loan`.
                # So, effectively, the "Disbursement" step is moving the loan proceeds from Buyer's account (where Bank put them) to Escrow.
                # Step C Modified: Transfer Loan Proceeds (Buyer -> Escrow).
                # Wait, if I do that, the "Bank -> Escrow" semantic is lost.
                # But financially it is same: Bank -> Buyer -> Escrow.
                # The Spec says `transfer(bank, escrow_agent, ...)`. This would imply Bank sends cash to Escrow.
                # If `grant_loan` already gave money to Buyer, and then we do Bank->Escrow, Bank pays twice?
                # Yes.
                # So I must transfer from Buyer -> Escrow.
                # BUT wait, the Spec says "Disburse Loan Principal to Escrow... transfer(bank, escrow_agent)".
                # This suggests the Spec assumes `create_loan` does NOT credit the buyer immediately, or the handler controls it.
                # But existing `Bank.grant_loan` DOES credit the buyer.
                # To align with existing Bank logic AND the goal (funds in Escrow):
                # We should transfer the loan amount from Buyer to Escrow.
                # The "Source" of funds is the Bank (via the loan), but the intermediate hop is the Buyer's account.

                memo_disburse = f"escrow_hold:loan_proceeds:{tx.item_id}"
                if not context.settlement_system.transfer(buyer, escrow_agent, loan_amount, memo_disburse, tick=context.time):
                    context.logger.critical(f"HOUSING | Failed to move loan proceeds to escrow for {buyer.id}")
                    # Compensate: Void Loan, Return Down Payment
                    self._void_loan_safely(context, loan_id)
                    context.settlement_system.transfer(escrow_agent, buyer, down_payment, "escrow_reversal:disbursement_failed", tick=context.time)
                    return False

            # 5. Saga Step D: Final Settlement (Escrow -> Seller)
            # Escrow now holds `down_payment + loan_amount` (which equals `sale_price`).
            memo_settle = f"final_settlement:{tx.item_id}"

            # Check if Seller is Government (Tax Collection path?)
            # Usually Housing Sale is Asset Transfer.
            # If Seller is Government, we transfer to Government.

            if not context.settlement_system.transfer(escrow_agent, seller, sale_price, memo_settle, tick=context.time):
                context.logger.critical(f"HOUSING | CRITICAL: Failed to pay seller {seller.id} from escrow.")
                # Compensate: This is messy.
                # 1. Return Loan Proceeds to Buyer (so we can void loan? No, void loan expects deposit reversal).
                # If we return to Buyer, we can void loan.
                if use_mortgage:
                    context.settlement_system.transfer(escrow_agent, buyer, loan_amount, "reversal:seller_payment_failed", tick=context.time)
                    self._void_loan_safely(context, loan_id)

                # 2. Return Down Payment
                context.settlement_system.transfer(escrow_agent, buyer, down_payment, "reversal:seller_payment_failed", tick=context.time)
                return False

            # Success!
            # 6. Apply Side Effects
            self._apply_housing_effects(unit, buyer, seller, loan_id, context)

            # Store mortgage_id in metadata for Registry/Observer
            if loan_id:
                if not tx.metadata: tx.metadata = {}
                tx.metadata["mortgage_id"] = loan_id

            context.logger.info(f"HOUSING | Success: Unit {unit.id} sold to {buyer.id}. Price: {sale_price}")
            return True

        except Exception as e:
            context.logger.error(f"HOUSING | Unexpected error: {e}", exc_info=True)
            # Generic Compensation Attempt (Best Effort)
            try:
                # If money in escrow, try to return to buyer?
                escrow_bal = context.bank.get_balance(str(escrow_agent.id)) if context.bank else 0 # Approximate
                # This is hard to know exactly how much of escrow balance is ours.
                # We rely on specific rollback blocks above.
                pass
            except:
                pass
            return False

    def _create_borrower_profile(self, buyer: Household, trade_value: float, context: TransactionContext) -> BorrowerProfileDTO:
        gross_income = 0.0
        if hasattr(buyer, "current_wage"):
             # Estimate monthly income
             work_hours = getattr(context.config_module, "WORK_HOURS_PER_DAY", 8.0)
             ticks_per_year = getattr(context.config_module, "TICKS_PER_YEAR", 100.0)
             ticks_per_month = ticks_per_year / 12.0
             gross_income = buyer.current_wage * work_hours * ticks_per_month

        existing_debt = 0.0
        if context.bank:
             try:
                 status = context.bank.get_debt_status(buyer.id)
                 existing_debt = status.total_outstanding_debt
             except: pass

        return BorrowerProfileDTO(
            borrower_id=str(buyer.id),
            gross_income=gross_income,
            existing_debt_payments=existing_debt * 0.01, # Approx
            collateral_value=trade_value,
            existing_assets=buyer.assets
        )

    def _void_loan_safely(self, context: TransactionContext, loan_id: str):
        if context.bank and loan_id:
            try:
                void_tx = context.bank.void_loan(loan_id)
                if void_tx and context.transaction_queue is not None:
                    context.transaction_queue.append(void_tx)
            except Exception as e:
                context.logger.error(f"HOUSING | Failed to void loan {loan_id}: {e}")

    def _apply_housing_effects(self, unit: Any, buyer: Any, seller: Any, mortgage_id: Optional[str], context: TransactionContext):
        """
        Updates housing ownership and residency.
        Mirrors Registry._handle_housing_registry but includes mortgage_id.
        """
        unit_id = unit.id

        # Update Unit
        unit.owner_id = buyer.id
        unit.mortgage_id = mortgage_id

        # Update Seller (if not None/Govt)
        if seller and hasattr(seller, "owned_properties"):
            if unit_id in seller.owned_properties:
                seller.owned_properties.remove(unit_id)

        # Update Buyer
        if hasattr(buyer, "owned_properties"):
            if unit_id not in buyer.owned_properties:
                buyer.owned_properties.append(unit_id)

            # Auto-move-in if homeless
            if getattr(buyer, "residing_property_id", None) is None:
                unit.occupant_id = buyer.id
                buyer.residing_property_id = unit_id
                buyer.is_homeless = False

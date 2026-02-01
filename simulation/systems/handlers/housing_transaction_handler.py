from typing import Any, Optional
import logging
from simulation.systems.api import ITransactionHandler, TransactionContext
from simulation.models import Transaction
from modules.finance.api import BorrowerProfileDTO
from simulation.agents.government import Government

logger = logging.getLogger(__name__)

class HousingTransactionHandler(ITransactionHandler):
    """
    Handles 'housing' market transactions (Purchases & Mortgages).
    Implements ITransactionHandler contract.
    Refactored from HousingSystem.process_transaction.
    """

    def handle(self, transaction: Transaction, buyer: Any, seller: Any, context: TransactionContext) -> bool:
        """
        Executes the housing transaction:
        1. Identifies Unit and Agents.
        2. Application & Granting of Mortgage (if needed).
        3. Disbursement of Loan (Bank -> Buyer).
        4. Payment (Buyer -> Seller) via Escrow or Direct Transfer.
        5. Updates Unit Mortgage State.
        """
        # 1. Resolve Seller if missing (e.g. ID -1 for Government/Bank)
        if seller is None:
            if transaction.seller_id == -1:
                # Assuming -1 represents Government or Bank. HousingSystem implied Govt often acts as fallback.
                seller = context.government
            else:
                context.logger.error(f"HOUSING | Seller {transaction.seller_id} not found.")
                return False

        if buyer is None:
            context.logger.error(f"HOUSING | Buyer {transaction.buyer_id} not found.")
            return False

        try:
            # Parse Unit ID
            # Transaction item_id expected format: "unit_{id}"
            unit_id_str = transaction.item_id.split("_")[1]
            unit_id = int(unit_id_str)
            unit = next((u for u in context.real_estate_units if u.id == unit_id), None)

            if not unit:
                context.logger.warning(f"HOUSING | Unit {transaction.item_id} not found in state.")
                return False

            # 2. Mortgage Logic
            # Only Households get mortgages. Firms/Govt pay cash.
            # We assume 'owned_properties' existence implies eligibility or checking type
            is_household_buyer = hasattr(buyer, "owned_properties") and hasattr(buyer, "residing_property_id")

            loan_id = None
            loan_amount = 0.0

            # Retrieve Config
            ltv_ratio = getattr(context.config_module, "MORTGAGE_LTV_RATIO", 0.8)
            mortgage_term = getattr(context.config_module, "MORTGAGE_TERM_TICKS", 300)
            mortgage_rate = getattr(context.config_module, "MORTGAGE_INTEREST_RATE", 0.05)

            trade_value = transaction.price * transaction.quantity

            if is_household_buyer and context.bank:
                loan_amount = trade_value * ltv_ratio

                # Construct BorrowerProfileDTO
                gross_income = 0.0
                if hasattr(buyer, "current_wage"):
                    work_hours = getattr(context.config_module, "WORK_HOURS_PER_DAY", 8.0)
                    ticks_per_year = getattr(context.config_module, "TICKS_PER_YEAR", 100.0)
                    ticks_per_month = ticks_per_year / 12.0
                    gross_income = buyer.current_wage * work_hours * ticks_per_month

                existing_debt_payments = 0.0
                try:
                    debt_status = context.bank.get_debt_status(buyer.id)
                    total_debt = debt_status.get("total_outstanding_debt", 0.0)
                    monthly_payment_rate = getattr(context.config_module, "ESTIMATED_DEBT_PAYMENT_RATIO", 0.01)
                    existing_debt_payments = total_debt * monthly_payment_rate
                except Exception:
                    pass

                borrower_profile = BorrowerProfileDTO(
                    borrower_id=str(buyer.id),
                    gross_income=gross_income,
                    existing_debt_payments=existing_debt_payments,
                    collateral_value=trade_value,
                    existing_assets=buyer.assets
                )

                due_tick = context.time + mortgage_term

                # Grant Loan
                grant_result = context.bank.grant_loan(
                    borrower_id=str(buyer.id),
                    amount=loan_amount,
                    interest_rate=mortgage_rate,
                    due_tick=due_tick,
                    borrower_profile=borrower_profile
                )

                if grant_result:
                    loan_info, credit_tx = grant_result
                    loan_id = loan_info["loan_id"]

                    if credit_tx and context.transaction_queue is not None:
                         context.transaction_queue.append(credit_tx)

                    # 3. Disbursement: Bank -> Buyer
                    disbursement_success = context.settlement_system.transfer(
                        context.bank, buyer, loan_amount, "loan_disbursement", tick=context.time
                    )

                    if not disbursement_success:
                         context.logger.error(f"LOAN_DISBURSEMENT_FAIL | Bank could not transfer {loan_amount} to {buyer.id}. Voiding loan.")
                         void_tx = context.bank.void_loan(loan_id)
                         if void_tx and context.transaction_queue is not None: context.transaction_queue.append(void_tx)
                         return False

                    # Deposit Cleanup (Liability Reduction)
                    if hasattr(context.bank, "withdraw_for_customer"):
                        withdraw_success = context.bank.withdraw_for_customer(buyer.id, loan_amount)
                        if not withdraw_success:
                             context.logger.error(f"LOAN_WITHDRAW_FAIL | Could not reduce deposit for {buyer.id}. Rolling back.")
                             context.settlement_system.transfer(buyer, context.bank, loan_amount, "loan_rollback", tick=context.time)
                             void_tx = context.bank.void_loan(loan_id)
                             if void_tx and context.transaction_queue is not None: context.transaction_queue.append(void_tx)
                             return False

                    # Update Unit Mortgage State (Pre-emptively, rolled back if sale fails)
                    unit.mortgage_id = loan_id
                else:
                    unit.mortgage_id = None
            else:
                unit.mortgage_id = None

            # 4. Process Payment (Buyer -> Seller)
            payment_success = False

            # Check for Government Tax Collection path
            if isinstance(seller, Government):
                # Use collect_tax which uses SettlementSystem internally
                # Note: collect_tax handles transfer.
                tax_result = seller.collect_tax(trade_value, "asset_sale", buyer, context.time)
                payment_success = tax_result["success"]
            else:
                # Standard Transfer
                payment_success = context.settlement_system.transfer(
                    buyer, seller, trade_value, f"purchase_unit_{unit.id}", tick=context.time
                )

            if not payment_success:
                 context.logger.error(f"HOUSING_PAYMENT_FAIL | Buyer {buyer.id} could not pay {trade_value} to Seller {seller.id}. Rolling back.")

                 # Rollback Loan
                 if loan_id and context.bank:
                      # Reverse Disbursement
                      context.settlement_system.transfer(buyer, context.bank, loan_amount, "loan_rollback", tick=context.time)

                      # Void Loan
                      try:
                          void_tx = context.bank.void_loan(loan_id)
                          if void_tx and context.transaction_queue is not None: context.transaction_queue.append(void_tx)
                      except Exception as e:
                          context.logger.warning(f"ROLLBACK_WARNING | void_loan failed during rollback: {e}")

                      unit.mortgage_id = None

                 return False

            # Success
            # Side effect: Update ownership (Registry-like logic)
            # The Registry had _handle_housing_registry logic:
            # "unit.owner_id = buyer.id", update seller/buyer owned_properties, auto-move-in.
            # HousingTransactionHandler here did NOT have explicit ownership update code in the try block logic I read before.
            # Wait, let me check the previous file content again.

            # The previous file content:
            # ...
            # 4. Process Payment ...
            # ...
            # return True

            # It seems HousingTransactionHandler implementation I read missed the actual ownership update?!
            # Or maybe I missed it?
            # Let me re-read the previous file content from my context.
            # I read it in tool output.
            # It ends with:
            # logger.info(f"REAL_ESTATE | Sold Unit {unit.id} to {buyer.id}. ...")
            # return True

            # It assumes caller or Registry updates ownership?
            # But TransactionProcessor says "elif tx.transaction_type == 'housing': pass".
            # It relied on Registry logic?
            # Registry._handle_housing_registry does the update.
            # BUT HousingTransactionHandler is an ISpecializedTransactionHandler.
            # TransactionManager calls it:
            # if tx.transaction_type in self.handlers: success = handler.handle(...)
            # Then: "3. State Commitment (Registry & Accounting)... if success: registry.update_ownership(...)"

            # Aha! TransactionManager calls registry.update_ownership AFTER handler returns success.
            # The new TransactionProcessor (Dispatcher) in Spec has:
            # "success = handler.handle(...)"
            # "Post-processing (e.g., effects queue)..."
            # It does NOT call registry.update_ownership explicitly in the loop example in Spec!
            # The Spec for GoodsTransactionHandler puts side-effects INSIDE the handler.
            # So I MUST put ownership update logic INSIDE HousingTransactionHandler.

            self._apply_housing_effects(unit, buyer, seller, context)

            context.logger.info(
                f"REAL_ESTATE | Sold Unit {unit.id} to {buyer.id}. Price: {trade_value:.2f} Loan: {loan_amount}",
                extra={"tick": context.time, "tags": ["real_estate"]}
            )
            return True

        except Exception as e:
            context.logger.error(f"HOUSING_ERROR | {e}", extra={"error": str(e)})
            return False

    def _apply_housing_effects(self, unit: Any, buyer: Any, seller: Any, context: TransactionContext):
        """
        Updates housing ownership and residency.
        Migrated from Registry._handle_housing_registry.
        """
        unit_id = unit.id

        # Update Unit
        unit.owner_id = buyer.id

        # Update Seller (if not None/Govt)
        if seller and hasattr(seller, "owned_properties"):
            if unit_id in seller.owned_properties:
                seller.owned_properties.remove(unit_id)

        # Update Buyer
        if hasattr(buyer, "owned_properties"):
            if unit_id not in buyer.owned_properties:
                buyer.owned_properties.append(unit_id)

            # Housing System Logic: Auto-move-in if homeless
            if getattr(buyer, "residing_property_id", None) is None:
                unit.occupant_id = buyer.id
                buyer.residing_property_id = unit_id
                buyer.is_homeless = False

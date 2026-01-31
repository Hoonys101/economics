from typing import Any, Optional
import logging
from simulation.systems.api import ISpecializedTransactionHandler
from simulation.models import Transaction
from simulation.dtos.api import SimulationState
from modules.finance.api import BorrowerProfileDTO
from simulation.agents.government import Government

logger = logging.getLogger(__name__)

class HousingTransactionHandler(ISpecializedTransactionHandler):
    """
    Handles 'housing' market transactions (Purchases & Mortgages).
    Implements ISpecializedTransactionHandler contract.
    Refactored from HousingSystem.process_transaction.
    """

    def handle(self, transaction: Transaction, buyer: Any, seller: Any, state: SimulationState) -> bool:
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
                seller = state.government
            else:
                logger.error(f"HOUSING | Seller {transaction.seller_id} not found.")
                return False

        if buyer is None:
            logger.error(f"HOUSING | Buyer {transaction.buyer_id} not found.")
            return False

        try:
            # Parse Unit ID
            # Transaction item_id expected format: "unit_{id}"
            unit_id_str = transaction.item_id.split("_")[1]
            unit_id = int(unit_id_str)
            unit = next((u for u in state.real_estate_units if u.id == unit_id), None)

            if not unit:
                logger.warning(f"HOUSING | Unit {transaction.item_id} not found in state.")
                return False

            # 2. Mortgage Logic
            # Only Households get mortgages. Firms/Govt pay cash.
            # We assume 'owned_properties' existence implies eligibility or checking type
            is_household_buyer = hasattr(buyer, "owned_properties") and hasattr(buyer, "residing_property_id")

            loan_id = None
            loan_amount = 0.0

            # Retrieve Config
            ltv_ratio = getattr(state.config_module, "MORTGAGE_LTV_RATIO", 0.8)
            mortgage_term = getattr(state.config_module, "MORTGAGE_TERM_TICKS", 300)
            mortgage_rate = getattr(state.config_module, "MORTGAGE_INTEREST_RATE", 0.05)

            trade_value = transaction.price * transaction.quantity

            if is_household_buyer and state.bank:
                loan_amount = trade_value * ltv_ratio

                # Construct BorrowerProfileDTO
                gross_income = 0.0
                if hasattr(buyer, "current_wage"):
                    work_hours = getattr(state.config_module, "WORK_HOURS_PER_DAY", 8.0)
                    ticks_per_year = getattr(state.config_module, "TICKS_PER_YEAR", 100.0)
                    ticks_per_month = ticks_per_year / 12.0
                    gross_income = buyer.current_wage * work_hours * ticks_per_month

                existing_debt_payments = 0.0
                try:
                    debt_status = state.bank.get_debt_status(buyer.id)
                    total_debt = debt_status.get("total_outstanding_debt", 0.0)
                    monthly_payment_rate = getattr(state.config_module, "ESTIMATED_DEBT_PAYMENT_RATIO", 0.01)
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

                due_tick = state.time + mortgage_term

                # Grant Loan
                grant_result = state.bank.grant_loan(
                    borrower_id=str(buyer.id),
                    amount=loan_amount,
                    interest_rate=mortgage_rate,
                    due_tick=due_tick,
                    borrower_profile=borrower_profile
                )

                if grant_result:
                    loan_info, credit_tx = grant_result
                    loan_id = loan_info["loan_id"]

                    if credit_tx:
                         state.transactions.append(credit_tx)

                    # 3. Disbursement: Bank -> Buyer
                    disbursement_success = state.settlement_system.transfer(
                        state.bank, buyer, loan_amount, "loan_disbursement", tick=state.time
                    )

                    if not disbursement_success:
                         logger.error(f"LOAN_DISBURSEMENT_FAIL | Bank could not transfer {loan_amount} to {buyer.id}. Voiding loan.")
                         void_tx = state.bank.void_loan(loan_id)
                         if void_tx: state.transactions.append(void_tx)
                         return False

                    # Deposit Cleanup (Liability Reduction)
                    if hasattr(state.bank, "withdraw_for_customer"):
                        withdraw_success = state.bank.withdraw_for_customer(buyer.id, loan_amount)
                        if not withdraw_success:
                             logger.error(f"LOAN_WITHDRAW_FAIL | Could not reduce deposit for {buyer.id}. Rolling back.")
                             state.settlement_system.transfer(buyer, state.bank, loan_amount, "loan_rollback", tick=state.time)
                             void_tx = state.bank.void_loan(loan_id)
                             if void_tx: state.transactions.append(void_tx)
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
                tax_result = seller.collect_tax(trade_value, "asset_sale", buyer, state.time)
                payment_success = tax_result["success"]
            else:
                # Standard Transfer
                payment_success = state.settlement_system.transfer(
                    buyer, seller, trade_value, f"purchase_unit_{unit.id}", tick=state.time
                )

            if not payment_success:
                 logger.error(f"HOUSING_PAYMENT_FAIL | Buyer {buyer.id} could not pay {trade_value} to Seller {seller.id}. Rolling back.")

                 # Rollback Loan
                 if loan_id:
                      # Reverse Disbursement
                      state.settlement_system.transfer(buyer, state.bank, loan_amount, "loan_rollback", tick=state.time)

                      # Void Loan
                      try:
                          void_tx = state.bank.void_loan(loan_id)
                          if void_tx: state.transactions.append(void_tx)
                      except Exception as e:
                          logger.warning(f"ROLLBACK_WARNING | void_loan failed during rollback: {e}")

                      unit.mortgage_id = None

                 return False

            # Success
            logger.info(
                f"REAL_ESTATE | Sold Unit {unit.id} to {buyer.id}. Price: {trade_value:.2f} Loan: {loan_amount}",
                extra={"tick": state.time, "tags": ["real_estate"]}
            )
            return True

        except Exception as e:
            logger.error(f"HOUSING_ERROR | {e}", extra={"error": str(e)})
            return False

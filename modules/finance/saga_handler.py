from typing import Any, Optional, cast, List, Tuple, Literal
import logging
from uuid import UUID

from modules.finance.sagas.housing_api import (
    IHousingTransactionSagaHandler,
    HousingTransactionSagaStateDTO,
    MortgageApprovalDTO,
    IPropertyRegistry,
    ILoanMarket,
    HousingSagaAgentContext
)
from modules.housing.api import IHousingService
from modules.finance.api import MortgageApplicationDTO, IFinancialAgent, IBank
from modules.simulation.api import ISimulationState, HouseholdSnapshotDTO
from simulation.finance.api import ISettlementSystem
from modules.finance.kernel.api import IMonetaryLedger

logger = logging.getLogger(__name__)

class HousingTransactionSagaHandler(IHousingTransactionSagaHandler):
    def __init__(self, simulation: ISimulationState):
        self.simulation = simulation
        self.settlement_system: ISettlementSystem = simulation.settlement_system
        # Note: housing_service must implement IHousingService
        self.housing_service: IHousingService = simulation.housing_service

        # Access Loan Market via markets dict
        market = simulation.markets.get("loan")
        # We need to ensure it supports ILoanMarket protocol methods used below.
        # Assuming the loan market implementation aligns with ILoanMarket protocol or similar.
        self.loan_market = market

        # TD-253: Monetary Ledger Injection
        self.monetary_ledger: Optional[IMonetaryLedger] = simulation.monetary_ledger

    def execute_step(self, saga: HousingTransactionSagaStateDTO) -> HousingTransactionSagaStateDTO:
        status = saga.status
        logger.debug(f"SAGA_EXECUTE | Saga {saga.saga_id} processing step: {status}")

        current_tick = self.simulation.time
        # Prevent double processing in same tick
        if saga.last_processed_tick == current_tick and status != "INITIATED":
             return saga

        try:
            if status == "INITIATED":
                return self._handle_initiated(saga)
            elif status == "CREDIT_CHECK":
                return self._handle_credit_check(saga)
            elif status == "APPROVED":
                return self._handle_approved(saga)
            elif status == "ESCROW_LOCKED":
                return self._handle_escrow_locked(saga)
            elif status == "TRANSFER_TITLE":
                return self._handle_transfer_title(saga)
            elif status in ["COMPLETED", "FAILED_ROLLED_BACK", "CANCELLED"]:
                return saga
            else:
                logger.error(f"SAGA_UNKNOWN_STATE | Saga {saga.saga_id} in unknown state {status}")
                return self.compensate_step(saga)

        except Exception as e:
            logger.exception(f"SAGA_CRITICAL_FAIL | Saga {saga.saga_id} failed at {status}. {e}")
            saga.error_message = str(e)
            return self.compensate_step(saga)
        finally:
            saga.last_processed_tick = current_tick

    def compensate_step(self, saga: HousingTransactionSagaStateDTO) -> HousingTransactionSagaStateDTO:
        status = saga.status
        logger.warning(f"SAGA_COMPENSATE | Rolling back saga {saga.saga_id} from {status}")

        try:
            # 1. Reverse Settlement if needed
            if status == "TRANSFER_TITLE":
                 # If failed at TITLE transfer, funds were moved in ESCROW_LOCKED.
                 self._reverse_settlement(saga)

            # 2. Cleanup Financials (Loan & Lien)
            if saga.mortgage_approval:
                 # Remove Lien
                 lien_id = saga.mortgage_approval.lien_id
                 self.housing_service.remove_lien(saga.property_id, lien_id)

                 # Void Loan
                 loan_id = saga.mortgage_approval.loan_id
                 # Use correct method to void/terminate existing loan
                 if isinstance(self.simulation.bank, IBank):
                    self.simulation.bank.terminate_loan(loan_id)
                 elif hasattr(self.loan_market, 'void_staged_application'):
                    # Fallback if approval but no bank method (unlikely)
                    self.loan_market.void_staged_application(loan_id)

            # 3. Cleanup Staged Loan (if no approval yet)
            elif saga.staged_loan_id:
                 if hasattr(self.loan_market, 'void_staged_application'):
                    self.loan_market.void_staged_application(saga.staged_loan_id)

            # 4. Release Property Lock
            self.housing_service.release_contract(saga.property_id, saga.saga_id)

            saga.status = "FAILED_ROLLED_BACK"

        except Exception as e:
            logger.critical(f"SAGA_ROLLBACK_FAIL | Failed to rollback saga {saga.saga_id}. {e}")
            saga.status = "FAILED_ROLLED_BACK"

        return saga

    def _get_buyer_id(self, saga: HousingTransactionSagaStateDTO) -> Optional[int]:
        """Helper to extract buyer ID from snapshot or dict."""
        ctx = saga.buyer_context
        if isinstance(ctx, HouseholdSnapshotDTO):
            return int(ctx.household_id)
        # Fallback removed as DTO enforces type
        return None

    def _handle_initiated(self, saga: HousingTransactionSagaStateDTO) -> HousingTransactionSagaStateDTO:
        # 1. Lock Property
        success = self.housing_service.set_under_contract(saga.property_id, saga.saga_id)

        if not success:
             saga.error_message = "Property already under contract"
             # Can't rollback lock if we didn't get it, but compensate handles cleanup
             return self.compensate_step(saga)

        # 2. Application Staging (Data already prepared by HousingSystem via Snapshot)
        app_dto = saga.loan_application

        if not app_dto:
             saga.error_message = "Missing loan application in saga state"
             return self.compensate_step(saga)

        # 3. Stage Mortgage
        staged_loan_id = self.loan_market.stage_mortgage_application(app_dto)
        if not staged_loan_id:
             saga.error_message = "Loan staging rejected"
             return self.compensate_step(saga)

        # stage_mortgage_application returns str (loan_id)
        saga.staged_loan_id = staged_loan_id

        saga.status = "CREDIT_CHECK"
        return saga

    def _handle_credit_check(self, saga: HousingTransactionSagaStateDTO) -> HousingTransactionSagaStateDTO:
        # Asynchronous check
        if not saga.staged_loan_id:
            saga.error_message = "Missing staged loan ID"
            return self.compensate_step(saga)

        status = self.loan_market.check_staged_application_status(saga.staged_loan_id)

        if status == "APPROVED":
            saga.status = "APPROVED"
        elif status == "REJECTED":
            saga.error_message = "Credit check rejected"
            return self.compensate_step(saga)
        else:
            # PENDING, wait next tick
            pass

        return saga

    def _handle_approved(self, saga: HousingTransactionSagaStateDTO) -> HousingTransactionSagaStateDTO:
        # Finalize Loan & Create Lien
        # 1. Convert/Retrieve Loan Info
        if not saga.staged_loan_id:
            saga.error_message = "Missing staged loan ID"
            return self.compensate_step(saga)

        loan_info = self.loan_market.convert_staged_to_loan(saga.staged_loan_id)
        if not loan_info:
             saga.error_message = "Failed to convert staged loan"
             return self.compensate_step(saga)

        loan_id = loan_info.loan_id
        principal = loan_info.approved_principal

        # 2. Add Lien via Registry
        # Need lienholder_id (Bank ID).
        # LoanInfo might not have it, but we know it's the Bank.
        bank_id = self.simulation.bank.id if self.simulation.bank else -1

        lien_id = self.housing_service.add_lien(saga.property_id, str(loan_id), bank_id, float(principal))
        if not lien_id:
             saga.error_message = "Failed to create lien"
             return self.compensate_step(saga)

        # 3. Store Approval
        saga.mortgage_approval = MortgageApprovalDTO(
            loan_id=loan_id,
            lien_id=lien_id,
            approved_principal=principal,
            monthly_payment=0.0 # Placeholder
        )

        saga.status = "ESCROW_LOCKED"
        return saga

    def _handle_escrow_locked(self, saga: HousingTransactionSagaStateDTO) -> HousingTransactionSagaStateDTO:
        # Execute Transfers (Settlement)
        # Bank -> Buyer (Principal)
        # Buyer -> Seller (Offer Price)

        bank = self.simulation.bank

        buyer_id = self._get_buyer_id(saga)

        seller_id = saga.seller_context.id if saga.seller_context else None

        # Determine seller agent
        seller = self.simulation.agents.get(seller_id)

        # Government/System Seller Logic
        if seller_id == -1:
             seller = self.simulation.government

        buyer = self.simulation.agents.get(buyer_id) if buyer_id is not None else None

        if not buyer or not seller:
             saga.error_message = "Agents missing for settlement"
             return self.compensate_step(saga)

        if not saga.mortgage_approval:
             saga.error_message = "Missing mortgage approval"
             return self.compensate_step(saga)

        principal = saga.mortgage_approval.approved_principal
        offer_price = saga.offer_price

        # MIGRATION: Convert Dollars to Pennies for Settlement
        principal_pennies = int(principal * 100)
        offer_price_pennies = int(offer_price * 100)

        transfers: List[Tuple[IFinancialAgent, IFinancialAgent, int]] = [
            (bank, buyer, principal_pennies),
            (buyer, seller, offer_price_pennies)
        ]

        success = self.settlement_system.execute_multiparty_settlement(transfers, self.simulation.time)

        if success:
             # TD-030: M2 Integrity - Record Authorized Expansion for Mortgage Disbursal
             if principal > 0 and self.monetary_ledger:
                 self.monetary_ledger.record_credit_expansion(
                     amount=principal,
                     saga_id=saga.saga_id,
                     loan_id=saga.mortgage_approval.loan_id,
                     reason="mortgage_disbursal"
                 )
             elif principal > 0:
                 # Fallback / Warning: Monetary Ledger missing
                 logger.warning(f"SAGA_M2_LEAK | MonetaryLedger missing. Credit expansion of {principal} not recorded for saga {saga.saga_id}.")

             saga.status = "TRANSFER_TITLE"
             return saga
        else:
             saga.error_message = "Settlement failed"
             return self.compensate_step(saga)

    def _handle_transfer_title(self, saga: HousingTransactionSagaStateDTO) -> HousingTransactionSagaStateDTO:
        # Finalize Ownership
        buyer_id = self._get_buyer_id(saga)

        success = self.housing_service.transfer_ownership(saga.property_id, buyer_id)

        if success:
             self._log_transaction(saga)
             self.housing_service.release_contract(saga.property_id, saga.saga_id)

             saga.status = "COMPLETED"
        else:
             saga.error_message = "Title transfer failed"
             return self.compensate_step(saga)

        return saga

    def _reverse_settlement(self, saga: HousingTransactionSagaStateDTO):
        # Reverse the transfers done in ESCROW_LOCKED
        # Seller -> Buyer (Offer Price)
        # Buyer -> Bank (Principal)

        bank = self.simulation.bank

        buyer_id = self._get_buyer_id(saga)
        seller_id = saga.seller_context.id if saga.seller_context else None

        buyer = self.simulation.agents.get(buyer_id) if buyer_id is not None else None
        seller = self.simulation.agents.get(seller_id)

        if seller_id == -1:
             seller = self.simulation.government

        if not buyer or not seller:
             logger.error("Cannot reverse settlement: agents missing")
             return

        if not saga.mortgage_approval:
             return

        principal = saga.mortgage_approval.approved_principal
        offer_price = saga.offer_price

        # MIGRATION: Convert Dollars to Pennies for Settlement
        principal_pennies = int(principal * 100)
        offer_price_pennies = int(offer_price * 100)

        transfers = [
            (seller, buyer, offer_price_pennies),
            (buyer, bank, principal_pennies)
        ]

        self.settlement_system.execute_multiparty_settlement(transfers, self.simulation.time)

        # TD-030: M2 Integrity - Record Destruction
        if principal > 0 and self.monetary_ledger:
             self.monetary_ledger.record_credit_destruction(
                 amount=principal,
                 saga_id=saga.saga_id,
                 loan_id=saga.mortgage_approval.loan_id,
                 reason="mortgage_rollback"
             )
        elif principal > 0:
             logger.warning(f"SAGA_M2_LEAK | MonetaryLedger missing. Credit destruction of {principal} not recorded for saga {saga.saga_id}.")

        logger.info(f"SAGA_ROLLBACK | Reversed settlement for saga {saga.saga_id}")

    def _log_transaction(self, saga: HousingTransactionSagaStateDTO):
        # Only for logging, avoiding manual transaction injection into world state to maintain protocol purity.
        # Ideally, SettlementSystem should log all financial transactions.
        # This explicit transaction logging was likely for non-financial record keeping (housing market volume).
        # We will skip manual injection into world_state.transactions to avoid violating ISimulationState protocol.
        pass

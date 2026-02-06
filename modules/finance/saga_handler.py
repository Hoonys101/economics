from typing import Any, Optional, cast, List, Tuple, Literal
import logging
from uuid import UUID

from modules.finance.sagas.housing_api import (
    IHousingTransactionSagaHandler,
    HousingTransactionSagaStateDTO,
    MortgageApprovalDTO,
    IPropertyRegistry,
    ILoanMarket
)
from modules.market.housing_planner_api import MortgageApplicationDTO
from modules.market.loan_api import (
    calculate_monthly_income,
    calculate_total_monthly_debt_payments
)
from modules.simulation.api import ISimulationState
from simulation.finance.api import ISettlementSystem, IFinancialEntity
from simulation.models import Transaction

logger = logging.getLogger(__name__)

class HousingTransactionSagaHandler(IHousingTransactionSagaHandler):
    def __init__(self, simulation: ISimulationState):
        self.simulation = simulation
        self.settlement_system: ISettlementSystem = simulation.settlement_system
        # Note: Registry in simulation must implement IPropertyRegistry methods
        self.housing_service = getattr(simulation, 'housing_service', None)
        self.loan_market = simulation.markets.get("loan")

    def execute_step(self, saga: HousingTransactionSagaStateDTO) -> HousingTransactionSagaStateDTO:
        status = saga['status']
        logger.debug(f"SAGA_EXECUTE | Saga {saga['saga_id']} processing step: {status}")

        current_tick = self.simulation.time
        # Prevent double processing in same tick
        if saga['last_processed_tick'] == current_tick and status != "INITIATED":
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
            elif status in ["COMPLETED", "FAILED_ROLLED_BACK"]:
                return saga
            else:
                logger.error(f"SAGA_UNKNOWN_STATE | Saga {saga['saga_id']} in unknown state {status}")
                return self.compensate_step(saga)

        except Exception as e:
            logger.exception(f"SAGA_CRITICAL_FAIL | Saga {saga['saga_id']} failed at {status}. {e}")
            saga['error_message'] = str(e)
            return self.compensate_step(saga)
        finally:
            saga['last_processed_tick'] = current_tick

    def compensate_step(self, saga: HousingTransactionSagaStateDTO) -> HousingTransactionSagaStateDTO:
        status = saga['status']
        logger.warning(f"SAGA_COMPENSATE | Rolling back saga {saga['saga_id']} from {status}")

        try:
            # 1. Reverse Settlement if needed
            if status == "TRANSFER_TITLE":
                 # If failed at TITLE transfer, funds were moved in ESCROW_LOCKED.
                 self._reverse_settlement(saga)

            # 2. Cleanup Financials (Loan & Lien)
            if saga.get('mortgage_approval'):
                 # Remove Lien
                 lien_id = saga['mortgage_approval']['lien_id']
                 if hasattr(self.housing_service, 'remove_lien'):
                    self.housing_service.remove_lien(saga['property_id'], lien_id)

                 # Void Loan
                 loan_id = saga['mortgage_approval']['loan_id']
                 if hasattr(self.loan_market, 'void_staged_application'):
                    self.loan_market.void_staged_application(loan_id)

            # 3. Cleanup Staged Loan (if no approval yet)
            elif saga.get('staged_loan_id'):
                 if hasattr(self.loan_market, 'void_staged_application'):
                    self.loan_market.void_staged_application(saga['staged_loan_id'])

            # 4. Release Property Lock
            if hasattr(self.housing_service, 'release_contract'):
                self.housing_service.release_contract(saga['property_id'], saga['saga_id'])

            saga['status'] = "FAILED_ROLLED_BACK"

        except Exception as e:
            logger.critical(f"SAGA_ROLLBACK_FAIL | Failed to rollback saga {saga['saga_id']}. {e}")
            saga['status'] = "FAILED_ROLLED_BACK"

        return saga

    def _handle_initiated(self, saga: HousingTransactionSagaStateDTO) -> HousingTransactionSagaStateDTO:
        # 1. Lock Property
        if hasattr(self.housing_service, 'set_under_contract'):
             success = self.housing_service.set_under_contract(saga['property_id'], saga['saga_id'])
             if not success:
                 saga['error_message'] = "Property already under contract"
                 # Can't rollback lock if we didn't get it, but compensate handles cleanup
                 return self.compensate_step(saga)

        # 2. Resolve Seller
        if saga['seller_id'] == -1:
             units = getattr(self.simulation, 'real_estate_units', [])
             unit = next((u for u in units if hasattr(u, 'id') and u.id == saga['property_id']), None)
             if unit:
                 saga['seller_id'] = unit.owner_id
             else:
                 saga['error_message'] = "Property not found"
                 return self.compensate_step(saga)

        # 3. Prepare Application
        principal = saga['offer_price'] - saga['down_payment_amount']
        buyer = self.simulation.agents.get(saga['buyer_id'])

        # Calculate Monthly Income
        ticks_per_year = getattr(self.simulation.config_module, 'TICKS_PER_YEAR', 360)
        monthly_income = 0.0
        if buyer and hasattr(buyer, 'current_wage'):
             monthly_income = calculate_monthly_income(buyer.current_wage, ticks_per_year)

        # Calculate Existing Monthly Debt Payments
        existing_monthly_payments = calculate_total_monthly_debt_payments(
            self.simulation.bank,
            saga['buyer_id'],
            ticks_per_year
        )

        app_dto: MortgageApplicationDTO = {
            "applicant_id": saga['buyer_id'],
            "requested_principal": principal,
            "purpose": "MORTGAGE",
            "property_id": saga['property_id'],
            "property_value": saga['offer_price'],
            "applicant_monthly_income": monthly_income,
            "existing_monthly_debt_payments": existing_monthly_payments,
            "loan_term": 360
        }
        saga['loan_application'] = app_dto # type: ignore

        # 4. Stage Mortgage
        staged_loan_id = self.loan_market.stage_mortgage_application(app_dto)
        if not staged_loan_id:
             saga['error_message'] = "Loan staging rejected"
             return self.compensate_step(saga)

        # stage_mortgage_application returns str (loan_id)
        saga['staged_loan_id'] = staged_loan_id

        saga['status'] = "CREDIT_CHECK"
        return saga

    def _handle_credit_check(self, saga: HousingTransactionSagaStateDTO) -> HousingTransactionSagaStateDTO:
        # Asynchronous check
        status = self.loan_market.check_staged_application_status(saga['staged_loan_id'])

        if status == "APPROVED":
            saga['status'] = "APPROVED"
        elif status == "REJECTED":
            saga['error_message'] = "Credit check rejected"
            return self.compensate_step(saga)
        else:
            # PENDING, wait next tick
            pass

        return saga

    def _handle_approved(self, saga: HousingTransactionSagaStateDTO) -> HousingTransactionSagaStateDTO:
        # Finalize Loan & Create Lien
        # 1. Convert/Retrieve Loan Info
        loan_info = self.loan_market.convert_staged_to_loan(saga['staged_loan_id'])
        if not loan_info:
             saga['error_message'] = "Failed to convert staged loan"
             return self.compensate_step(saga)

        loan_id = loan_info['loan_id']
        principal = loan_info['original_amount']

        # 2. Add Lien via Registry
        # Need lienholder_id (Bank ID).
        # LoanInfo might not have it, but we know it's the Bank.
        bank_id = self.simulation.bank.id if self.simulation.bank else -1

        lien_id = self.housing_service.add_lien(saga['property_id'], loan_id, bank_id, principal)
        if not lien_id:
             saga['error_message'] = "Failed to create lien"
             return self.compensate_step(saga)

        # 3. Store Approval
        saga['mortgage_approval'] = {
            "loan_id": loan_id,
            "lien_id": lien_id,
            "approved_principal": principal,
            "monthly_payment": 0.0 # Placeholder
        }

        saga['status'] = "ESCROW_LOCKED"
        return saga

    def _handle_escrow_locked(self, saga: HousingTransactionSagaStateDTO) -> HousingTransactionSagaStateDTO:
        # Execute Transfers (Settlement)
        # Bank -> Buyer (Principal)
        # Buyer -> Seller (Offer Price)

        bank = self.simulation.bank
        buyer = self.simulation.agents.get(saga['buyer_id'])
        seller = self.simulation.agents.get(saga['seller_id'])
        if saga['seller_id'] == -1 and hasattr(self.simulation, 'government'):
             seller = self.simulation.government

        if not buyer or not seller:
             saga['error_message'] = "Agents missing for settlement"
             return self.compensate_step(saga)

        principal = saga['mortgage_approval']['approved_principal']
        offer_price = saga['offer_price']

        transfers: List[Tuple[IFinancialEntity, IFinancialEntity, float]] = [
            (bank, buyer, principal),
            (buyer, seller, offer_price)
        ]

        success = self.settlement_system.execute_multiparty_settlement(transfers, self.simulation.time)

        if success:
             # TD-030: M2 Integrity - Record Authorized Expansion for Mortgage Disbursal
             # Moving Bank Reserves to Public Circulation (via Buyer) is an M2 Expansion.
             # We must track this to match the Authorized Delta (MonetaryLedger).
             if principal > 0:
                 tx_credit = Transaction(
                    buyer_id=bank.id,
                    seller_id=-1, # System Authorization
                    item_id=f"mortgage_disbursal_{saga['saga_id']}",
                    quantity=1.0,
                    price=principal,
                    market_id="monetary_policy",
                    transaction_type="credit_creation",
                    time=self.simulation.time,
                    metadata={"executed": True, "saga_id": str(saga['saga_id'])}
                 )
                 # Manually append to world_state transactions (like _log_transaction)
                 if hasattr(self.simulation, 'world_state'):
                      self.simulation.world_state.transactions.append(tx_credit)
                 elif hasattr(self.simulation, 'transactions'):
                      self.simulation.transactions.append(tx_credit)

             saga['status'] = "TRANSFER_TITLE"
             # Optionally process next step immediately?
             # Or wait next tick? State machine usually one step per tick unless we want fast track.
             # Draft says "If fund transfers are successful, transition to TRANSFER_TITLE."
             # It doesn't explicitly say "wait".
             # But returning ensures state is persisted.
             return saga
        else:
             saga['error_message'] = "Settlement failed"
             return self.compensate_step(saga)

    def _handle_transfer_title(self, saga: HousingTransactionSagaStateDTO) -> HousingTransactionSagaStateDTO:
        # Finalize Ownership
        success = self.housing_service.transfer_ownership(saga['property_id'], saga['buyer_id'])

        if success:
             self._log_transaction(saga)
             # Release lock is done implicitly by completion?
             # Or should we explicit release?
             # Draft: "Call PropertyRegistry.transfer_ownership... Transition to COMPLETED."
             # Usually ownership transfer overrides contract lock or lock is ignored for new owner.
             # But good hygiene: release lock.
             self.housing_service.release_contract(saga['property_id'], saga['saga_id'])

             saga['status'] = "COMPLETED"
        else:
             saga['error_message'] = "Title transfer failed"
             return self.compensate_step(saga)

        return saga

    def _reverse_settlement(self, saga: HousingTransactionSagaStateDTO):
        # Reverse the transfers done in ESCROW_LOCKED
        # Seller -> Buyer (Offer Price)
        # Buyer -> Bank (Principal)

        bank = self.simulation.bank
        buyer = self.simulation.agents.get(saga['buyer_id'])
        seller = self.simulation.agents.get(saga['seller_id'])
        if saga['seller_id'] == -1 and hasattr(self.simulation, 'government'):
             seller = self.simulation.government

        if not buyer or not seller:
             logger.error("Cannot reverse settlement: agents missing")
             return

        principal = saga['mortgage_approval']['approved_principal']
        offer_price = saga['offer_price']

        transfers = [
            (seller, buyer, offer_price),
            (buyer, bank, principal)
        ]

        self.settlement_system.execute_multiparty_settlement(transfers, self.simulation.time)

        # TD-030: M2 Integrity - Record Destruction
        if principal > 0:
             tx_destroy = Transaction(
                buyer_id=-1,
                seller_id=bank.id,
                item_id=f"mortgage_rollback_{saga['saga_id']}",
                quantity=1.0,
                price=principal,
                market_id="monetary_policy",
                transaction_type="credit_destruction",
                time=self.simulation.time,
                metadata={"executed": True, "saga_id": str(saga['saga_id'])}
             )
             if hasattr(self.simulation, 'world_state'):
                  self.simulation.world_state.transactions.append(tx_destroy)
             elif hasattr(self.simulation, 'transactions'):
                  self.simulation.transactions.append(tx_destroy)

        logger.info(f"SAGA_ROLLBACK | Reversed settlement for saga {saga['saga_id']}")

    def _log_transaction(self, saga: HousingTransactionSagaStateDTO):
        loan_id = saga['mortgage_approval']['loan_id'] if saga.get('mortgage_approval') else None

        tx_record = Transaction(
            buyer_id=saga['buyer_id'],
            seller_id=saga['seller_id'],
            item_id=f"unit_{saga['property_id']}",
            quantity=1.0,
            price=saga['offer_price'],
            market_id="housing",
            transaction_type="housing",
            time=self.simulation.time,
            metadata={"mortgage_id": loan_id}
        )

        # We don't need to call registry.update_ownership again because we called transfer_ownership.
        # But we need to log it for history.
        if hasattr(self.simulation, 'world_state'):
             self.simulation.world_state.transactions.append(tx_record)
        elif hasattr(self.simulation, 'transactions'):
             self.simulation.transactions.append(tx_record)

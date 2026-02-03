from typing import Any, Optional, cast
import logging
from uuid import UUID

from modules.housing.api import IHousingTransactionSagaHandler
from modules.housing.dtos import (
    HousingTransactionSagaStateDTO,
    MortgageApplicationDTO,
    MortgageApprovalDTO
)
from modules.simulation.api import ISimulationState
from simulation.finance.api import ISettlementSystem
from simulation.systems.api import IRegistry
from simulation.models import Transaction

logger = logging.getLogger(__name__)

class HousingTransactionSagaHandler(IHousingTransactionSagaHandler):
    def __init__(self, simulation: ISimulationState):
        self.simulation = simulation
        # Access systems via simulation
        self.settlement_system: ISettlementSystem = simulation.settlement_system
        self.registry: IRegistry = simulation.registry
        # We access loan market via simulation.markets
        self.loan_market = simulation.markets.get("loan")

    def execute_step(self, saga: HousingTransactionSagaStateDTO) -> HousingTransactionSagaStateDTO:
        status = saga['status']

        try:
            if status == "INITIATED":
                return self._handle_initiated(saga)
            elif status == "LOAN_APPROVED":
                return self._handle_loan_approved(saga)
            elif status == "DOWN_PAYMENT_COMPLETE":
                return self._handle_down_payment_complete(saga)
            elif status == "MORTGAGE_DISBURSEMENT_COMPLETE":
                return self._handle_disbursement_complete(saga)

        except Exception as e:
            logger.exception(f"SAGA_CRITICAL_FAIL | Saga {saga['saga_id']} failed at {status}. {e}")
            saga['status'] = "FAILED_ROLLED_BACK" # Or generic fail state, but we should try to rollback if possible in specific handlers.
            saga['error_message'] = str(e)

        return saga

    def _handle_initiated(self, saga: HousingTransactionSagaStateDTO) -> HousingTransactionSagaStateDTO:
        # Resolve Seller ID if not set
        if saga['seller_id'] == -1:
             prop_id = saga['property_id']
             # Access real_estate_units from simulation
             units = getattr(self.simulation, 'real_estate_units', [])
             if not units and hasattr(self.simulation, 'world_state'):
                 units = getattr(self.simulation.world_state, 'real_estate_units', [])

             unit = next((u for u in units if hasattr(u, 'id') and u.id == prop_id), None)
             if unit:
                 saga['seller_id'] = unit.owner_id
                 logger.debug(f"SAGA_INIT | Resolved seller {unit.owner_id} for property {prop_id}")
             else:
                 logger.error(f"SAGA_FAIL | Property {prop_id} not found in registry.")
                 saga['status'] = "FAILED_ROLLED_BACK"
                 saga['error_message'] = "Property not found"
                 return saga

        # Create and submit loan application
        # Principal = Offer Price - Down Payment
        principal = saga['offer_price'] - saga['down_payment_amount']

        application = MortgageApplicationDTO(
            applicant_id=saga['buyer_id'],
            principal=principal,
            property_id=saga['property_id'],
            property_value=saga['offer_price'],
            loan_term=360 # Default 30 years
        )
        saga['loan_application'] = application

        # Submit to Loan Market
        # Assuming LoanMarket has request_mortgage
        if self.loan_market and hasattr(self.loan_market, 'request_mortgage'):
             household = self.simulation.agents.get(saga['buyer_id'])
             current_tick = self.simulation.time

             approval = self.loan_market.request_mortgage(application, household_agent=household, current_tick=current_tick)
             if approval:
                 saga['mortgage_approval'] = approval
                 saga['status'] = "LOAN_APPROVED"
             else:
                 saga['status'] = "LOAN_REJECTED"
                 saga['error_message'] = "Loan rejected by bank"
        else:
             logger.error("LoanMarket missing or incompatible")
             saga['status'] = "FAILED_ROLLED_BACK"
             saga['error_message'] = "System Error: LoanMarket incompatible"

        return saga

    def _handle_loan_approved(self, saga: HousingTransactionSagaStateDTO) -> HousingTransactionSagaStateDTO:
        # Execute Down Payment
        buyer = self.simulation.agents.get(saga['buyer_id'])
        seller = self.simulation.agents.get(saga['seller_id'])

        if not buyer:
            saga['status'] = "FAILED_ROLLED_BACK"
            saga['error_message'] = "Buyer agent not found"
            self._rollback_loan(saga)
            return saga

        # Seller might be -1 (Govt/System) if undefined?
        if saga['seller_id'] == -1:
             if hasattr(self.simulation, 'government'):
                 seller = self.simulation.government

        if not seller:
             # Critical error, cannot transfer
             saga['status'] = "FAILED_ROLLED_BACK"
             saga['error_message'] = "Seller agent not found"
             self._rollback_loan(saga)
             return saga

        tx = self.settlement_system.transfer(
            debit_agent=buyer,
            credit_agent=seller,
            amount=saga['down_payment_amount'],
            memo=f"down_payment_saga_{saga['saga_id']}",
            tick=self.simulation.time
        )

        if tx:
            saga['status'] = "DOWN_PAYMENT_COMPLETE"
        else:
            # Down payment failed
            logger.warning(f"Saga {saga['saga_id']}: Down payment transfer failed. Rolling back loan.")
            self._rollback_loan(saga)
            saga['status'] = "FAILED_ROLLED_BACK"
            saga['error_message'] = "Down payment transfer failed"

        return saga

    def _handle_down_payment_complete(self, saga: HousingTransactionSagaStateDTO) -> HousingTransactionSagaStateDTO:
        # Execute Mortgage Disbursement
        # Bank.grant_loan puts money in Buyer's account (via deposit).
        # So Buyer pays Seller.

        buyer = self.simulation.agents.get(saga['buyer_id'])
        seller_id = saga['seller_id']
        seller = self.simulation.agents.get(seller_id)

        if seller_id == -1 and hasattr(self.simulation, 'government'):
            seller = self.simulation.government

        if not seller:
             saga['status'] = "FAILED_ROLLED_BACK"
             saga['error_message'] = "Seller agent not found during disbursement"
             self._rollback_down_payment(saga)
             self._rollback_loan(saga)
             return saga

        if not saga['mortgage_approval']:
             saga['status'] = "FAILED_ROLLED_BACK"
             saga['error_message'] = "Mortgage approval missing"
             self._rollback_down_payment(saga)
             return saga

        principal = saga['mortgage_approval']['approved_principal']

        tx = self.settlement_system.transfer(
            debit_agent=buyer, # Buyer pays Seller using the loan proceeds
            credit_agent=seller,
            amount=principal,
            memo=f"mortgage_disburse_saga_{saga['saga_id']}",
            tick=self.simulation.time
        )

        if tx:
            saga['status'] = "MORTGAGE_DISBURSEMENT_COMPLETE"
        else:
            # Failed. Rollback Down Payment
            self._rollback_down_payment(saga)
            # Rollback Loan (Reverse the deposit)
            self._rollback_loan(saga)
            saga['status'] = "FAILED_ROLLED_BACK"
            saga['error_message'] = "Mortgage disbursement failed"

        return saga

    def _handle_disbursement_complete(self, saga: HousingTransactionSagaStateDTO) -> HousingTransactionSagaStateDTO:
        # Finalize Ownership
        tx_record = Transaction(
            buyer_id=saga['buyer_id'],
            seller_id=saga['seller_id'],
            item_id=f"unit_{saga['property_id']}",
            quantity=1.0,
            price=saga['offer_price'],
            market_id="housing",
            transaction_type="housing",
            time=self.simulation.time,
            metadata={"mortgage_id": saga['mortgage_approval']['loan_id']}
        )

        buyer = self.simulation.agents.get(saga['buyer_id'])
        seller = self.simulation.agents.get(saga['seller_id'])
        if saga['seller_id'] == -1 and hasattr(self.simulation, 'government'):
             seller = self.simulation.government

        # Registry update
        self.registry.update_ownership(tx_record, buyer, seller, self.simulation.world_state if hasattr(self.simulation, 'world_state') else self.simulation)

        # Record Transaction
        if hasattr(self.simulation, 'world_state'):
             self.simulation.world_state.transactions.append(tx_record)

        saga['status'] = "COMPLETED"
        return saga

    def _rollback_down_payment(self, saga: HousingTransactionSagaStateDTO):
        buyer = self.simulation.agents.get(saga['buyer_id'])
        seller = self.simulation.agents.get(saga['seller_id'])
        if saga['seller_id'] == -1 and hasattr(self.simulation, 'government'):
             seller = self.simulation.government

        if buyer and seller:
            self.settlement_system.transfer(
                debit_agent=seller,
                credit_agent=buyer,
                amount=saga['down_payment_amount'],
                memo=f"rollback_down_payment_saga_{saga['saga_id']}",
                tick=self.simulation.time
            )
            logger.warning(f"SAGA_ROLLBACK | Down payment returned for saga {saga['saga_id']}")

    def _rollback_loan(self, saga: HousingTransactionSagaStateDTO):
         if saga['mortgage_approval']:
             loan_id = saga['mortgage_approval']['loan_id']
             if hasattr(self.simulation.bank, 'void_loan'):
                 self.simulation.bank.void_loan(loan_id)
                 logger.warning(f"SAGA_ROLLBACK | Loan {loan_id} voided for saga {saga['saga_id']}")
             else:
                 # Fallback
                 self.simulation.bank.terminate_loan(loan_id)
                 logger.warning(f"SAGA_ROLLBACK | Loan {loan_id} terminated (void not supported) for saga {saga['saga_id']}")

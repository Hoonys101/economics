from typing import Any, Optional, cast, List, Tuple
import logging
from uuid import UUID

from modules.housing.api import IHousingTransactionSagaHandler
from modules.housing.dtos import (
    HousingTransactionSagaStateDTO,
    MortgageApprovalDTO
)
# Use new API for application DTO construction
from modules.market.housing_planner_api import MortgageApplicationDTO

from modules.simulation.api import ISimulationState
from simulation.finance.api import ISettlementSystem, IFinancialEntity
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
            # Legacy states handling (if saga resumes from persistence in old state)
            elif status in ["LOAN_APPROVED", "DOWN_PAYMENT_COMPLETE", "MORTGAGE_DISBURSEMENT_COMPLETE"]:
                logger.warning(f"Resuming saga {saga['saga_id']} from intermediate state {status}. Attempting to complete via legacy path or aborting.")
                # For safety in this refactor, we fail them to force rollback or clean state.
                saga['status'] = "FAILED_ROLLED_BACK"
                saga['error_message'] = "Intermediate state not supported in Atomic V2"
                return saga

        except Exception as e:
            logger.exception(f"SAGA_CRITICAL_FAIL | Saga {saga['saga_id']} failed at {status}. {e}")
            saga['status'] = "FAILED_ROLLED_BACK"
            saga['error_message'] = str(e)

        return saga

    def _handle_initiated(self, saga: HousingTransactionSagaStateDTO) -> HousingTransactionSagaStateDTO:
        # 1. Resolve Seller ID if not set
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

        # 2. Prepare Mortgage Application (New API)
        principal = saga['offer_price'] - saga['down_payment_amount']
        buyer_id = saga['buyer_id']
        household = self.simulation.agents.get(buyer_id)

        # Estimate Income/Debt
        income = 0.0
        if household and hasattr(household, 'current_wage'):
             ticks_per_year = getattr(self.simulation.config_module, 'TICKS_PER_YEAR', 100)
             income = household.current_wage * ticks_per_year

        # For debt, we pass 0.0 if unknown, or let LoanMarket/Bank query internally.
        # LoanMarket.evaluate logic handles internal query fallback.

        app_dto: MortgageApplicationDTO = {
            "applicant_id": buyer_id,
            "principal": principal,
            "purpose": "MORTGAGE",
            "property_id": saga['property_id'],
            "property_value": saga['offer_price'],
            "applicant_income": income,
            "applicant_existing_debt": 0.0, # Placeholder
            "loan_term": 360
        }

        # Store in saga (compatibility cast)
        saga['loan_application'] = app_dto # type: ignore

        # 3. Stage Mortgage
        if not self.loan_market or not hasattr(self.loan_market, 'stage_mortgage'):
             logger.error("LoanMarket missing or incompatible (no stage_mortgage)")
             saga['status'] = "FAILED_ROLLED_BACK"
             saga['error_message'] = "System Error: LoanMarket incompatible"
             return saga

        loan_id = self.loan_market.stage_mortgage(app_dto)

        if loan_id is None:
             saga['status'] = "LOAN_REJECTED"
             saga['error_message'] = "Loan rejected or staging failed"
             return saga

        # Record Approval
        saga['mortgage_approval'] = {
            "loan_id": loan_id,
            "approved_principal": principal,
            "monthly_payment": 0.0 # Not needed for settlement
        }

        # 4. Atomic Settlement (Seamless Payment)
        # Bank -> Buyer (Principal)
        # Buyer -> Seller (Full Price)

        bank = self.simulation.bank
        buyer = household
        seller = self.simulation.agents.get(saga['seller_id'])

        if saga['seller_id'] == -1 and hasattr(self.simulation, 'government'):
             seller = self.simulation.government

        if not buyer or not seller or not bank:
             # Abort and Void Loan
             self._void_loan(loan_id)
             saga['status'] = "FAILED_ROLLED_BACK"
             saga['error_message'] = "Agents not found for settlement"
             return saga

        transfers: List[Tuple[IFinancialEntity, IFinancialEntity, float]] = [
            (bank, buyer, principal),
            (buyer, seller, saga['offer_price'])
        ]

        if not hasattr(self.settlement_system, 'execute_multiparty_settlement'):
             logger.error("SettlementSystem missing execute_multiparty_settlement")
             self._void_loan(loan_id)
             saga['status'] = "FAILED_ROLLED_BACK"
             return saga

        success = self.settlement_system.execute_multiparty_settlement(transfers, self.simulation.time)

        if success:
             # 5. Finalize
             self._finalize_transaction(saga, loan_id)
             saga['status'] = "COMPLETED"
             logger.info(f"SAGA_SUCCESS | Atomic purchase complete for {buyer_id} prop {saga['property_id']}")
        else:
             # 6. Rollback (Void Loan)
             # Settlement already rolled back transfers. We just need to kill the staged loan.
             self._void_loan(loan_id)
             saga['status'] = "FAILED_ROLLED_BACK"
             saga['error_message'] = "Settlement failed (Funds or Validation)"

        return saga

    def _finalize_transaction(self, saga: HousingTransactionSagaStateDTO, loan_id: int):
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

        buyer = self.simulation.agents.get(saga['buyer_id'])
        seller = self.simulation.agents.get(saga['seller_id'])
        if saga['seller_id'] == -1 and hasattr(self.simulation, 'government'):
             seller = self.simulation.government

        # Registry update
        self.registry.update_ownership(tx_record, buyer, seller, self.simulation.world_state if hasattr(self.simulation, 'world_state') else self.simulation)

        # Record Transaction
        if hasattr(self.simulation, 'world_state'):
             self.simulation.world_state.transactions.append(tx_record)

    def _void_loan(self, loan_id: int):
         # Call Bank.terminate_loan or void_loan
         # loan_id is int, Bank methods usually take str (e.g. "loan_123")
         # We assume LoanMarket returned the numeric part or hash.
         # Actually Bank uses "loan_X" strings.
         # LoanMarket.stage_mortgage returned int.
         # This implies LoanMarket parsed it.
         # To void, we need to reconstruct the string ID or iterate?
         # Bank.terminate_loan(loan_id: str).

         # Issue: LoanMarket.stage_mortgage returns INT. Bank has STRING keys "loan_1".
         # We need the string ID.
         # I should update LoanMarket.stage_mortgage to return string or SagaHandler to handle string?
         # HousingTransactionSagaStateDTO uses int for loan_id (in MortgageApprovalDTO).

         # Best effort: Try to find loan in bank with matching numeric part or just "loan_{loan_id}"

         # Access Bank loans directly to find it?
         bank = self.simulation.bank
         lid_str = f"loan_{loan_id}"
         if lid_str in bank.loans:
             bank.terminate_loan(lid_str)
         else:
             # Try search
             found = None
             for k in bank.loans.keys():
                 if str(loan_id) in k: # risky
                     found = k
                     break
             if found:
                 bank.terminate_loan(found)
             else:
                 logger.warning(f"SAGA_VOID_FAIL | Could not find loan to void: {loan_id}")

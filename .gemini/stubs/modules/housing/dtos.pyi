from dataclasses import dataclass as dataclass
from modules.household.dtos import HouseholdSnapshotDTO as HouseholdSnapshotDTO
from modules.market.housing_planner_api import MortgageApplicationDTO as MortgageApplicationDTO
from modules.system.api import HousingMarketSnapshotDTO as HousingMarketSnapshotDTO
from typing import Literal, TypedDict
from uuid import UUID

class MortgageApprovalDTO(TypedDict):
    """
    Response from the LoanMarket upon successful loan approval.
    """
    loan_id: int
    approved_principal: float
    monthly_payment: float

class HousingTransactionSagaStateDTO(TypedDict):
    """
    State object for the housing purchase Saga.
    Manages the entire lifecycle of the transaction.
    """
    saga_id: UUID
    status: Literal['INITIATED', 'LOAN_APPLICATION_PENDING', 'LOAN_REJECTED', 'LOAN_APPROVED', 'DOWN_PAYMENT_PENDING', 'DOWN_PAYMENT_COMPLETE', 'MORTGAGE_DISBURSEMENT_PENDING', 'MORTGAGE_DISBURSEMENT_COMPLETE', 'COMPLETED', 'FAILED_ROLLED_BACK']
    buyer_id: int
    seller_id: int
    property_id: int
    offer_price: float
    down_payment_amount: float
    loan_application: MortgageApplicationDTO | None
    mortgage_approval: MortgageApprovalDTO | None
    error_message: str | None

class HousingDecisionRequestDTO(TypedDict):
    """
    Input for the simplified HousingPlanner.
    """
    household_state: HouseholdSnapshotDTO
    housing_market_snapshot: HousingMarketSnapshotDTO
    outstanding_debt_payments: float

class HousingPurchaseDecisionDTO(TypedDict):
    """
    Output of the HousingPlanner, representing a desire to buy.
    This is the trigger for the transaction saga.
    """
    decision_type: Literal['INITIATE_PURCHASE']
    target_property_id: int
    offer_price: float
    down_payment_amount: float

class HousingRentalDecisionDTO(TypedDict):
    """
    Output of the HousingPlanner for renting.
    """
    decision_type: Literal['MAKE_RENTAL_OFFER']
    target_property_id: int

class HousingStayDecisionDTO(TypedDict):
    """
    Output of the HousingPlanner to do nothing.
    """
    decision_type: Literal['STAY']
HousingDecisionDTO = HousingPurchaseDecisionDTO | HousingRentalDecisionDTO | HousingStayDecisionDTO

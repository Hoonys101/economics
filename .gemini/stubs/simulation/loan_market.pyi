from _typeshed import Incomplete
from modules.finance.api import BorrowerProfileDTO as BorrowerProfileDTO, IBankService as IBankService, LoanDTO, MortgageApplicationDTO as MortgageApplicationDTO
from modules.housing.dtos import MortgageApprovalDTO
from modules.market.housing_planner_api import ILoanMarket
from simulation.bank import Bank as Bank
from simulation.core_markets import Market as Market
from simulation.models import Order as Order, Transaction as Transaction
from typing import Any, Literal, override

logger: Incomplete

class LoanMarket(Market, ILoanMarket):
    """
    Handles loan requests and repayments via the IBankService interface.
    Refactored to decouple from concrete Bank implementation.
    Implements ILoanMarket for housing pipeline (Phase 32).
    """
    id: Incomplete
    bank: Incomplete
    config_module: Incomplete
    loan_requests: list[Order]
    repayment_requests: list[Order]
    def __init__(self, market_id: str, bank: IBankService, config_module: Any) -> None: ...
    def evaluate_mortgage_application(self, application: MortgageApplicationDTO) -> bool:
        """
        Performs hard LTV/DTI checks. Returns True if approved, False if rejected.
        Implements ILoanMarket.evaluate_mortgage_application.
        Uses [TD-206] MortgageApplicationDTO for precise DTI calculation.
        """
    def apply_for_mortgage(self, application: MortgageApplicationDTO) -> LoanDTO | None:
        """
        Processes a mortgage application with regulatory checks.
        Returns LoanDTO if approved, None otherwise.
        """
    def stage_mortgage_application(self, application: MortgageApplicationDTO) -> str | None:
        """
        Submits an application for asynchronous credit check.
        Returns a unique `staged_loan_id` for tracking, or None if invalid.
        Implements ILoanMarket (Saga) interface.
        """
    def stage_mortgage(self, application: MortgageApplicationDTO) -> LoanDTO | None:
        """
        Legacy/Compat method.
        Stages a mortgage (creates loan record) without disbursing funds.
        Returns LoanDTO if successful, None otherwise.
        """
    def check_staged_application_status(self, staged_loan_id: str) -> Literal['PENDING', 'APPROVED', 'REJECTED']:
        """Checks the status of a pending mortgage application."""
    def convert_staged_to_loan(self, staged_loan_id: str) -> LoanDTO | None:
        """
        Finalizes an approved application.
        Returns LoanDTO object.
        """
    def void_staged_application(self, staged_loan_id: str) -> bool:
        """Cancels a pending or approved application."""
    def request_mortgage(self, application: MortgageApplicationDTO, household_agent: Any = None, current_tick: int = 0) -> MortgageApprovalDTO | None:
        """
        Legacy/Compat method.
        Calls evaluate, then Bank.grant_loan (Full execution).
        """
    def place_order(self, order: Order, current_tick: int) -> list[Transaction]:
        """Submits a loan request or repayment order to the bank service."""
    def get_total_demand(self) -> float: ...
    def get_total_supply(self) -> float: ...
    def match_orders(self, current_time: int) -> list[Transaction]: ...
    def get_daily_avg_price(self) -> float: ...
    def get_daily_volume(self) -> float: ...
    matched_transactions: Incomplete
    @override
    def clear_orders(self) -> None: ...

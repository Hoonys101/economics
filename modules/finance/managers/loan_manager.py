from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass
import config
from modules.finance.api import ILoanManager, LoanDTO, LoanApplicationDTO, LoanNotFoundError
from modules.finance.dtos import LoanStatus
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY

TICKS_PER_YEAR = config.TICKS_PER_YEAR

@dataclass
class _Loan:
    loan_id: str
    borrower_id: int
    principal: float
    remaining_balance: float
    annual_interest_rate: float
    term_ticks: int
    start_tick: int
    origination_tick: int
    status: LoanStatus = "ACTIVE"
    created_deposit_id: Optional[str] = None
    currency: CurrencyCode = DEFAULT_CURRENCY

    @property
    def tick_interest_rate(self) -> float:
        return self.annual_interest_rate / TICKS_PER_YEAR

class LoanManager(ILoanManager):
    """
    Manages the lifecycle of loans.
    """
    def __init__(self):
        self._loans: Dict[str, _Loan] = {}
        self._next_loan_id = 0

    def create_loan(self, borrower_id: int, amount: float, interest_rate: float,
                    start_tick: int, term_ticks: int, created_deposit_id: Optional[str] = None) -> str:
        """
        Creates a new loan and returns its ID.
        """
        loan_id = f"loan_{self._next_loan_id}"
        self._next_loan_id += 1

        loan = _Loan(
            loan_id=loan_id,
            borrower_id=borrower_id,
            principal=amount,
            remaining_balance=amount,
            annual_interest_rate=interest_rate,
            term_ticks=term_ticks,
            start_tick=start_tick,
            origination_tick=start_tick,
            created_deposit_id=created_deposit_id,
            status="ACTIVE"
        )
        self._loans[loan_id] = loan
        return loan_id

    def submit_loan_application(self, application: LoanApplicationDTO) -> str:
        # Assuming defaults for missing fields if used directly
        # This method is required by Protocol but Bank Facade might use create_loan
        return self.create_loan(
            borrower_id=application['applicant_id'],
            amount=application['amount'],
            interest_rate=0.05, # Default?
            start_tick=0,
            term_ticks=application['term_months']
        )

    def process_applications(self) -> None:
        pass

    def service_loans(self, current_tick: int, payment_callback: Callable[[int, float], bool]) -> List[Any]:
        """
        Iterates active loans, calculates interest, and attempts to collect via callback.
        Returns a list of event dicts:
        - {"type": "interest_payment", "loan_id": str, "borrower_id": int, "amount": float}
        - {"type": "default", "loan_id": str, "borrower_id": int, "amount_defaulted": float}
        """
        results = []

        # Iterate over a copy to allow modification if needed (though we just update status)
        for loan in list(self._loans.values()):
            if loan.status != "ACTIVE":
                continue

            if loan.remaining_balance <= 0:
                loan.status = "PAID"
                continue

            interest = loan.remaining_balance * loan.tick_interest_rate

            # Attempt to collect interest
            success = payment_callback(loan.borrower_id, interest)

            if success:
                results.append({
                    "type": "interest_payment",
                    "loan_id": loan.loan_id,
                    "borrower_id": loan.borrower_id,
                    "amount": interest
                })
            else:
                # Default Logic
                loan.status = "DEFAULTED"
                amount_defaulted = loan.remaining_balance
                loan.remaining_balance = 0.0 # Write off from active balance

                results.append({
                    "type": "default",
                    "loan_id": loan.loan_id,
                    "borrower_id": loan.borrower_id,
                    "amount_defaulted": amount_defaulted
                })

        return results

    def get_loan_by_id(self, loan_id: str) -> Optional[LoanDTO]:
        loan = self._loans.get(loan_id)
        if not loan:
            return None
        return self._map_to_dto(loan)

    def get_loans_for_agent(self, agent_id: int) -> List[LoanDTO]:
        return [self._map_to_dto(l) for l in self._loans.values() if l.borrower_id == agent_id]

    def _map_to_dto(self, loan: _Loan) -> LoanDTO:
        return LoanDTO(
            loan_id=loan.loan_id,
            borrower_id=loan.borrower_id,
            principal=loan.principal,
            interest_rate=loan.annual_interest_rate,
            term_months=loan.term_ticks,
            remaining_principal=loan.remaining_balance,
            status=loan.status,
            origination_tick=loan.origination_tick,
            due_tick=loan.start_tick + loan.term_ticks
        )

    # Internal / Helper methods for Bank Facade

    def repay_loan(self, loan_id: str, amount: float) -> bool:
        if loan_id not in self._loans:
            return False

        loan = self._loans[loan_id]
        actual_amount = min(amount, loan.remaining_balance)
        loan.remaining_balance -= actual_amount

        if loan.remaining_balance <= 0:
            loan.status = "PAID"

        return True

    def terminate_loan(self, loan_id: str) -> Optional[float]:
        """
        Terminates a loan and returns the remaining balance (for destruction calculation).
        Removes loan from manager.
        """
        if loan_id in self._loans:
            amount = self._loans[loan_id].remaining_balance
            del self._loans[loan_id]
            return amount
        return None

    def get_loan_internal(self, loan_id: str) -> Optional[_Loan]:
        return self._loans.get(loan_id)

    def delete_loan(self, loan_id: str):
        if loan_id in self._loans:
            del self._loans[loan_id]

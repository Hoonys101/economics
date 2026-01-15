from typing import Protocol, Dict, List
from dataclasses import dataclass

# Forward reference for type hinting
class Firm: pass

@dataclass
class BondDTO:
    """Data Transfer Object for government bonds."""
    id: str
    issuer: str
    face_value: float
    yield_rate: float
    maturity_date: int

@dataclass
class BailoutLoanDTO:
    """Data Transfer Object for corporate bailout loans."""
    firm_id: int
    amount: float
    interest_rate: float
    covenants: Dict[str, bool]

class IFinanceSystem(Protocol):
    """Interface for the sovereign debt and corporate bailout system."""

    def evaluate_solvency(self, firm: 'Firm', current_tick: int) -> bool:
        """Evaluates a firm's solvency to determine bailout eligibility."""
        ...

    def issue_treasury_bonds(self, amount: float, current_tick: int) -> List[BondDTO]:
        """Issues new treasury bonds to the market."""
        ...

    def grant_bailout_loan(self, firm: 'Firm', amount: float) -> BailoutLoanDTO:
        """Converts a bailout from a grant to an interest-bearing senior loan."""
        ...

    def service_debt(self, current_tick: int) -> None:
        """Manages the servicing of outstanding government debt."""
        ...

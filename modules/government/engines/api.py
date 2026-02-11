from typing import TypedDict, List, Dict, Optional, Protocol, runtime_checkable
from modules.system.api import CurrencyCode
from modules.finance.engines.api import MarketSnapshotDTO

class FiscalStateDTO(TypedDict):
    """Input state from Government agent."""
    tick: int
    assets: Dict[CurrencyCode, float]
    total_debt: float
    income_tax_rate: float
    corporate_tax_rate: float
    approval_rating: float
    welfare_budget_multiplier: float
    potential_gdp: float

class FirmFinancialsDTO(TypedDict):
    """A snapshot of a firm's health, NOT the live object."""
    assets: float
    profit: float
    is_solvent: bool

class FirmBailoutRequestDTO(TypedDict):
    firm_id: int
    requested_amount: float
    firm_financials: FirmFinancialsDTO

class FiscalRequestDTO(TypedDict): # Union of all possible requests
    bailout_request: Optional[FirmBailoutRequestDTO]
    # ... other request types in the future

class GrantedBailoutDTO(TypedDict):
    firm_id: int
    amount: float
    interest_rate: float
    term: int

class FiscalDecisionDTO(TypedDict):
    """Output decisions from the FiscalEngine."""
    new_income_tax_rate: Optional[float]
    new_corporate_tax_rate: Optional[float]
    new_welfare_budget_multiplier: Optional[float]
    bailouts_to_grant: List[GrantedBailoutDTO]

@runtime_checkable
class IFiscalEngine(Protocol):
    def decide(
        self,
        state: FiscalStateDTO,
        market: MarketSnapshotDTO,
        requests: List[FiscalRequestDTO]
    ) -> FiscalDecisionDTO:
        """
        Calculates the next set of fiscal actions based on current state.
        """
        ...

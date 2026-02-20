from typing import List, Dict, Optional, Protocol, runtime_checkable
from dataclasses import dataclass, field
from modules.system.api import CurrencyCode, MarketSnapshotDTO

@dataclass(frozen=True)
class FiscalStateDTO:
    """Input state from Government agent."""
    tick: int
    assets: Dict[CurrencyCode, float]
    total_debt: float
    income_tax_rate: float
    corporate_tax_rate: float
    approval_rating: float
    welfare_budget_multiplier: float
    potential_gdp: float

@dataclass(frozen=True)
class FirmFinancialsDTO:
    """A snapshot of a firm's health, NOT the live object."""
    assets: float
    profit: float
    is_solvent: bool

@dataclass(frozen=True)
class FirmBailoutRequestDTO:
    firm_id: int
    requested_amount: float
    firm_financials: FirmFinancialsDTO

@dataclass(frozen=True)
class FiscalRequestDTO: # Union of all possible requests
    bailout_request: Optional[FirmBailoutRequestDTO]
    # ... other request types in the future

@dataclass(frozen=True)
class GrantedBailoutDTO:
    firm_id: int
    amount: float
    interest_rate: float
    term: int

@dataclass(frozen=True)
class FiscalDecisionDTO:
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

from dataclasses import dataclass, field as field
from modules.system.api import CurrencyCode as CurrencyCode, MarketSnapshotDTO as MarketSnapshotDTO
from typing import Protocol

@dataclass(frozen=True)
class FiscalStateDTO:
    """Input state from Government agent."""
    tick: int
    assets: dict[CurrencyCode, int]
    total_debt: float
    income_tax_rate: float
    corporate_tax_rate: float
    approval_rating: float
    welfare_budget_multiplier: float
    potential_gdp: float

@dataclass(frozen=True)
class FirmFinancialsDTO:
    """A snapshot of a firm's health, NOT the live object."""
    assets: int
    profit: float
    is_solvent: bool

@dataclass(frozen=True)
class FirmBailoutRequestDTO:
    firm_id: int
    requested_amount: int
    firm_financials: FirmFinancialsDTO

@dataclass(frozen=True)
class FiscalRequestDTO:
    bailout_request: FirmBailoutRequestDTO | None

@dataclass(frozen=True)
class GrantedBailoutDTO:
    firm_id: int
    amount: int
    interest_rate: float
    term: int

@dataclass(frozen=True)
class FiscalDecisionDTO:
    """Output decisions from the FiscalEngine."""
    new_income_tax_rate: float | None
    new_corporate_tax_rate: float | None
    new_welfare_budget_multiplier: float | None
    bailouts_to_grant: list[GrantedBailoutDTO]

class IFiscalEngine(Protocol):
    def decide(self, state: FiscalStateDTO, market: MarketSnapshotDTO, requests: list[FiscalRequestDTO]) -> FiscalDecisionDTO:
        """
        Calculates the next set of fiscal actions based on current state.
        """

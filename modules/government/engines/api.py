from typing import List, Dict, Optional, Protocol, runtime_checkable
from dataclasses import dataclass, field
from modules.system.api import CurrencyCode, MarketSnapshotDTO

@dataclass(frozen=True)
class FiscalConfigDTO:
    """
    Configuration parameters for the Fiscal Engine.
    Enforces Type Safety and prevents magic number usage.
    """
    tax_rate_min: float
    tax_rate_max: float
    base_income_tax_rate: float
    base_corporate_tax_rate: float
    debt_ceiling_ratio: float
    austerity_trigger_ratio: float
    fiscal_sensitivity_alpha: float
    auto_counter_cyclical_enabled: bool

@dataclass(frozen=True)
class FiscalStateDTO:
    """Input state from Government agent."""
    tick: int
    assets: Dict[CurrencyCode, int] # Penny Standard
    total_debt: float # Keeping as float for ratio calcs, or should be int? Debt is usually tracked in pennies but ratios use float.
                      # Ideally debt is int (pennies) for ledger accuracy, but ratio calculation converts it.
                      # Let's keep total_debt as float for now as it often comes from a sum of bond face values (int) but might be used as float.
                      # Wait, debt is a liability. It should be int if it represents actual money owed.
                      # However, the original code had it as float. Let's stick to float for debt to minimize friction,
                      # but ASSETS must be int.
    income_tax_rate: float
    corporate_tax_rate: float
    approval_rating: float
    welfare_budget_multiplier: float
    potential_gdp: float

@dataclass(frozen=True)
class FirmFinancialsDTO:
    """A snapshot of a firm's health, NOT the live object."""
    assets: int # Penny Standard
    profit: float # Profit can be float? Usually accounting is int. But let's stick to assets/amounts being int.
    is_solvent: bool

@dataclass(frozen=True)
class FirmBailoutRequestDTO:
    firm_id: int
    requested_amount: int # Penny Standard
    firm_financials: FirmFinancialsDTO

@dataclass(frozen=True)
class FiscalRequestDTO: # Union of all possible requests
    bailout_request: Optional[FirmBailoutRequestDTO]
    # ... other request types in the future

@dataclass(frozen=True)
class GrantedBailoutDTO:
    firm_id: int
    amount: int # Penny Standard
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

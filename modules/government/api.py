from __future__ import annotations
from typing import Protocol, List, Any, Optional, Dict
from modules.government.dtos import (
    FiscalPolicyDTO,
    MonetaryPolicyDTO,
    GovernmentStateDTO,
    MacroEconomicSnapshotDTO,
    WelfareResultDTO,
    BailoutResultDTO,
    TaxCollectionResultDTO,
    IAgent
)
from modules.government.welfare.api import IWelfareRecipient
from simulation.dtos.api import MarketSnapshotDTO
from modules.finance.api import TaxCollectionResult
from modules.system.api import CurrencyCode

class IFiscalPolicyManager(Protocol):
    """Interface for managing the government's fiscal policy."""

    def determine_fiscal_stance(self, market_snapshot: "MarketSnapshotDTO") -> FiscalPolicyDTO:
        """Adjusts tax brackets based on economic conditions."""
        ...

    def calculate_tax_liability(self, policy: FiscalPolicyDTO, income: float) -> float:
        """Calculates the tax owed based on a progressive bracket system."""
        ...

class IMonetaryPolicyManager(Protocol):
    """Interface for managing the government's monetary policy (Central Bank)."""

    def determine_monetary_stance(self, market_snapshot: "MacroEconomicSnapshotDTO") -> MonetaryPolicyDTO:
        """Adjusts the target interest rate based on a Taylor-like rule."""
        ...

class ITaxService(Protocol):
    """
    A stateless service responsible for all tax calculations and for generating
    tax collection requests.
    """
    def determine_fiscal_stance(self, snapshot: MarketSnapshotDTO) -> FiscalPolicyDTO:
        """Determines the current fiscal policy based on market conditions."""
        ...

    def calculate_tax_liability(self, policy: FiscalPolicyDTO, income: float) -> float:
        """Calculates the tax amount for a given income and fiscal policy."""
        ...

    def calculate_corporate_tax(self, profit: float, rate: float) -> float:
        """Calculates corporate tax based on profit and a flat rate."""
        ...

    def calculate_wealth_tax(self, net_worth: float) -> float:
        """Calculates wealth tax amount (float) based on net worth."""
        ...

    def collect_wealth_tax(self, agents: List[IAgent]) -> TaxCollectionResultDTO:
        """
        Calculates wealth tax for all eligible agents and returns a DTO
        containing payment requests for the government to execute.
        """
        ...

    def record_revenue(self, result: TaxCollectionResult) -> None:
        """Updates internal ledgers based on a verified tax collection result."""
        ...

    def get_revenue_this_tick(self) -> Dict[CurrencyCode, float]:
        """Returns the total revenue collected in the current tick."""
        ...

    def get_revenue_breakdown_this_tick(self) -> Dict[str, float]:
        """Returns the breakdown of revenue by tax type for the current tick."""
        ...

    def get_total_collected_this_tick(self) -> float:
        """Returns the total amount collected this tick."""
        ...

    def get_tax_revenue(self) -> Dict[str, float]:
        """Returns the all-time tax revenue breakdown."""
        ...

    def get_total_collected_tax(self) -> Dict[CurrencyCode, float]:
        """Returns the all-time total collected tax by currency."""
        ...

    def reset_tick_flow(self) -> None:
        """Resets the per-tick revenue accumulators."""
        ...

class IWelfareManager(Protocol):
    """
    A stateless service responsible for all welfare and subsidy logic.
    It does not hold state or have access to agent wallets.
    """
    def run_welfare_check(self, agents: List[IAgent], market_data: MarketSnapshotDTO, current_tick: int, gdp_history: List[float], welfare_budget_multiplier: float = 1.0) -> WelfareResultDTO:
        """
        Identifies agents needing support and returns a DTO containing
        welfare payment requests for the government to execute.
        """
        ...

    def provide_firm_bailout(self, firm: IAgent, amount: float, current_tick: int, is_solvent: bool) -> Optional[BailoutResultDTO]:
        """
        Evaluates bailout eligibility and returns a DTO containing a loan request
        and a payment request. Returns None if not eligible.
        """
        ...

    def get_survival_cost(self, market_data: MarketSnapshotDTO) -> float:
        """Calculates current survival cost based on market prices."""
        ...

    def get_spending_this_tick(self) -> float:
        """Returns total welfare spending for the current tick."""
        ...

    def reset_tick_flow(self) -> None:
        """Resets the per-tick spending accumulator."""
        ...

class IGovernment(Protocol):
    """Facade for the government agent."""
    state: GovernmentStateDTO

    def make_policy_decision(self, market_snapshot: "MarketSnapshotDTO") -> None:
        ...

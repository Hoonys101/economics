from __future__ import annotations
from typing import Protocol, List, Any, Optional, Dict, TypedDict, runtime_checkable
from dataclasses import dataclass, field
from abc import abstractmethod
from modules.government.dtos import (
    FiscalPolicyDTO,
    MonetaryPolicyDTO,
    GovernmentStateDTO as LegacyGovernmentStateDTO,
    PolicyDecisionDTO,
    ExecutionResultDTO,
    MacroEconomicSnapshotDTO,
    WelfareResultDTO,
    BailoutResultDTO,
    TaxAssessmentResultDTO,
    FiscalContextDTO,
    BondIssueRequestDTO,
    BondIssuanceResultDTO,
    IAgent
)
from typing import TYPE_CHECKING
from modules.government.welfare.api import IWelfareRecipient
from modules.common.api import MarketSnapshotDTO

if TYPE_CHECKING:
    # Legacy import for compatibility if needed elsewhere, but GovBrain uses strict new one
    from simulation.dtos.api import MarketSnapshotDTO as LegacyMarketSnapshotDTO

from modules.finance.api import TaxCollectionResult, IFinancialEntity
from modules.system.api import CurrencyCode, AgentID

# --- Spec Definitions ---

@dataclass(frozen=True)
class GovernmentStateDTO:
    """
    Strict GovernmentStateDTO as per Wave 16 Spec.
    Represents the output state from the GovBrain.
    """
    treasury_balance: int # Pennies (changed from float to int as per review)
    current_tax_rates: Dict[str, float]
    active_welfare_programs: List[str]

@runtime_checkable
class IGovBrain(Protocol):
    def evaluate_policies(self, snapshot: MarketSnapshotDTO) -> GovernmentStateDTO: ...

# --- End Spec Definitions ---

@runtime_checkable
class ITaxableHousehold(IFinancialEntity, IAgent, Protocol):
    """
    Protocol for households subject to wealth tax.
    Requires financial entity capabilities and specific household attributes.
    """
    is_active: bool
    is_employed: bool
    needs: Any

class IFiscalPolicyManager(Protocol):
    """Interface for managing the government's fiscal policy."""

    def determine_fiscal_stance(self, market_snapshot: "LegacyMarketSnapshotDTO") -> GovernmentPolicyDTO:
        """Adjusts tax brackets based on economic conditions."""
        ...

    def calculate_tax_liability(self, policy: GovernmentPolicyDTO, income: int) -> int:
        """Calculates the tax owed based on a progressive bracket system (pennies)."""
        ...

class IMonetaryPolicyManager(Protocol):
    """Interface for managing the government's monetary policy (Central Bank)."""

    def determine_monetary_stance(self, market_snapshot: "MacroEconomicSnapshotDTO") -> GovernmentPolicyDTO:
        """Adjusts the target interest rate based on a Taylor-like rule."""
        ...

class ITaxService(Protocol):
    """
    A stateless service responsible for all tax calculations and for generating
    tax collection requests.
    """
    def determine_fiscal_stance(self, snapshot: "LegacyMarketSnapshotDTO") -> GovernmentPolicyDTO:
        """Determines the current fiscal policy based on market conditions."""
        ...

    def calculate_tax_liability(self, policy: GovernmentPolicyDTO, income: int) -> int:
        """Calculates the tax amount for a given income and fiscal policy (pennies)."""
        ...

    def calculate_corporate_tax(self, profit: int, rate: float) -> int:
        """Calculates corporate tax based on profit and a flat rate (pennies)."""
        ...

    def calculate_wealth_tax(self, net_worth: int) -> int:
        """Calculates wealth tax amount (pennies) based on net worth."""
        ...

    def collect_wealth_tax(self, agents: List[IAgent]) -> TaxAssessmentResultDTO:
        """
        Calculates wealth tax for all eligible agents and returns a DTO
        containing payment requests for the government to execute.
        """
        ...

    def record_revenue(self, result: TaxCollectionResult) -> None:
        """Updates internal ledgers based on a verified tax collection result."""
        ...

    def get_revenue_this_tick(self) -> Dict[CurrencyCode, int]:
        """Returns the total revenue collected in the current tick (pennies)."""
        ...

    def get_revenue_breakdown_this_tick(self) -> Dict[str, float]:
        """Returns the breakdown of revenue by tax type for the current tick."""
        ...

    def get_total_collected_this_tick(self) -> int:
        """Returns the total amount collected this tick (pennies)."""
        ...

    def get_tax_revenue(self) -> Dict[str, int]:
        """Returns the all-time tax revenue breakdown (pennies)."""
        ...

    def get_total_collected_tax(self) -> Dict[CurrencyCode, int]:
        """Returns the all-time total collected tax by currency (pennies)."""
        ...

    def reset_tick_flow(self) -> None:
        """Resets the per-tick revenue accumulators."""
        ...

class IWelfareService(Protocol):
    """
    A stateless service responsible for all welfare and subsidy logic.
    It does not hold state or have access to agent wallets.
    """
    def run_welfare_check(self, agents: List[IAgent], market_data: "LegacyMarketSnapshotDTO", current_tick: int, gdp_history: List[float], welfare_budget_multiplier: float = 1.0) -> WelfareResultDTO:
        """
        Identifies agents needing support and returns a DTO containing
        welfare payment requests for the government to execute.
        """
        ...

    def provide_firm_bailout(self, firm: IAgent, amount: int, current_tick: int, is_solvent: bool) -> Optional[BailoutResultDTO]:
        """
        Evaluates bailout eligibility and returns a DTO containing a loan request
        and a payment request. Returns None if not eligible.
        """
        ...

    def get_survival_cost(self, market_data: "LegacyMarketSnapshotDTO") -> int:
        """Calculates current survival cost based on market prices (pennies)."""
        ...

    def get_spending_this_tick(self) -> int:
        """Returns total welfare spending for the current tick (pennies)."""
        ...

    def reset_tick_flow(self) -> None:
        """Resets the per-tick spending accumulator."""
        ...

# Alias for backward compatibility
IWelfareManager = IWelfareService

class IFiscalBondService(Protocol):
    """
    A stateless service responsible for sovereign debt logic:
    calculating yields, determining buyers (QE), and preparing issuance.
    """
    def calculate_yield(self, context: FiscalContextDTO) -> float:
        """Calculates bond yield based on debt-to-GDP and other factors."""
        ...

    def issue_bonds(self, request: BondIssueRequestDTO, context: FiscalContextDTO, buyer_pool: Dict[str, Any]) -> BondIssuanceResultDTO:
        """
        Prepares a bond issuance transaction.
        Determines the buyer (e.g. Central Bank vs Commercial Bank) and creates the transaction request.
        """
        ...

@runtime_checkable
class IGovernment(Protocol):
    """
    Unified Facade for the Government Agent (Governor Pattern).
    All financial values MUST be in Integer Pennies.
    """
    id: AgentID
    is_active: bool
    name: str
    state: LegacyGovernmentStateDTO

    @property
    def expenditure_this_tick(self) -> Dict[CurrencyCode, int]:
        ...

    @property
    def revenue_this_tick(self) -> Dict[CurrencyCode, int]:
        ...

    @property
    def total_debt(self) -> int:
        ...

    @property
    def total_wealth(self) -> int:
        ...

    # Governance & Policy Fields
    corporate_tax_rate: float
    income_tax_rate: float
    fiscal_policy: FiscalPolicyDTO

    def make_policy_decision(self, market_snapshot: Any, current_tick: int, central_bank: Any) -> None:
        ...


@dataclass
class GovernmentExecutionContext:
    """Injectable dependencies for the ExecutionEngine."""
    settlement_system: Any # ISettlementSystem
    finance_system: Any # IFinanceSystem
    tax_service: ITaxService
    welfare_manager: IWelfareService
    fiscal_bond_service: IFiscalBondService
    infrastructure_manager: Any = None # Optional for now
    public_manager: Any = None # PublicManager (IAssetRecoverySystem)


class IGovernmentDecisionEngine(Protocol):
    """
    Interface for the stateless decision-making engine.
    Determines *what* policy action to take.
    """
    def decide(
        self,
        state: GovernmentStateDTO, # Corrected from LegacyGovernmentStateDTO to GovernmentStateDTO (New)
        market_snapshot: "LegacyMarketSnapshotDTO",
        central_bank: Any
    ) -> PolicyDecisionDTO:
        """
        Decides on a policy action based on current state and market data.
        """
        ...


class IPolicyExecutionEngine(Protocol):
    """
    Interface for the stateless policy execution engine.
    Determines *how* to implement a decided action.
    """
    def execute(
        self,
        decision: PolicyDecisionDTO,
        current_state: LegacyGovernmentStateDTO,
        agents: List[IAgent],
        market_data: Dict[str, Any],
        context: GovernmentExecutionContext
    ) -> ExecutionResultDTO:
        """
        Takes a high-level policy decision and translates it into concrete,
        executable results by orchestrating various services (Tax, Welfare, etc.).
        """
        ...


# --- Wave 4: Political System DTOs & Protocol ---

from modules.common.enums import IndustryDomain


@dataclass(frozen=True)
class VoteRecordDTO:
    """
    A single vote cast by an agent for a specific policy.
    """
    agent_id: int
    policy_type: str  # e.g., "INCOME_TAX_RATE", "CORPORATE_TAX", "WELFARE"
    preferred_rate: float  # The rate (0.0-1.0) the agent is voting for
    weight: float = 1.0  # Political weight (default 1.0, influenced by status)


@dataclass(frozen=True)
class LobbyingEffortDTO:
    """
    Represents a firm's investment to influence policy.
    Financial values in Integer Pennies (Penny Standard).
    """
    firm_id: int
    target_industry: IndustryDomain  # Sector to protect/subsidize
    investment_pennies: int  # Cost of lobbying (transferred to gov treasury)
    desired_policy_shift: float  # e.g., +0.01 or -0.01 shift in tax/subsidy


@runtime_checkable
class IPoliticalOrchestrator(Protocol):
    """
    Protocol for the Political System.
    Aggregates votes and lobbying efforts to determine Government Policy.
    """

    def register_vote(self, vote: VoteRecordDTO) -> None:
        """Ingests a vote from an agent."""
        ...

    def register_lobbying(self, effort: LobbyingEffortDTO) -> None:
        """Ingests a lobbying effort from a firm."""
        ...

    def calculate_policy_outcome(self) -> Dict[str, float]:
        """
        Aggregates all votes and lobbying to determine new policy rates.
        Returns a dict of {policy_type: new_rate}.
        """
        ...

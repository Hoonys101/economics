from dataclasses import dataclass
from modules.common.enums import IndustryDomain as IndustryDomain
from modules.finance.api import IFinancialEntity as IFinancialEntity, TaxCollectionResult as TaxCollectionResult
from modules.government.dtos import BailoutResultDTO as BailoutResultDTO, BondIssuanceResultDTO as BondIssuanceResultDTO, BondIssueRequestDTO as BondIssueRequestDTO, ExecutionResultDTO as ExecutionResultDTO, FiscalContextDTO as FiscalContextDTO, FiscalPolicyDTO as FiscalPolicyDTO, GovernmentStateDTO as GovernmentStateDTO, IAgent as IAgent, MacroEconomicSnapshotDTO as MacroEconomicSnapshotDTO, MonetaryPolicyDTO as MonetaryPolicyDTO, PolicyDecisionDTO as PolicyDecisionDTO, TaxAssessmentResultDTO as TaxAssessmentResultDTO, WelfareResultDTO as WelfareResultDTO
from modules.government.welfare.api import IWelfareRecipient as IWelfareRecipient
from modules.system.api import CurrencyCode as CurrencyCode
from simulation.dtos.api import MarketSnapshotDTO as MarketSnapshotDTO
from typing import Any, Protocol

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
    def determine_fiscal_stance(self, market_snapshot: MarketSnapshotDTO) -> GovernmentPolicyDTO:
        """Adjusts tax brackets based on economic conditions."""
    def calculate_tax_liability(self, policy: GovernmentPolicyDTO, income: int) -> int:
        """Calculates the tax owed based on a progressive bracket system (pennies)."""

class IMonetaryPolicyManager(Protocol):
    """Interface for managing the government's monetary policy (Central Bank)."""
    def determine_monetary_stance(self, market_snapshot: MacroEconomicSnapshotDTO) -> GovernmentPolicyDTO:
        """Adjusts the target interest rate based on a Taylor-like rule."""

class ITaxService(Protocol):
    """
    A stateless service responsible for all tax calculations and for generating
    tax collection requests.
    """
    def determine_fiscal_stance(self, snapshot: MarketSnapshotDTO) -> GovernmentPolicyDTO:
        """Determines the current fiscal policy based on market conditions."""
    def calculate_tax_liability(self, policy: GovernmentPolicyDTO, income: int) -> int:
        """Calculates the tax amount for a given income and fiscal policy (pennies)."""
    def calculate_corporate_tax(self, profit: int, rate: float) -> int:
        """Calculates corporate tax based on profit and a flat rate (pennies)."""
    def calculate_wealth_tax(self, net_worth: int) -> int:
        """Calculates wealth tax amount (pennies) based on net worth."""
    def collect_wealth_tax(self, agents: list[IAgent]) -> TaxAssessmentResultDTO:
        """
        Calculates wealth tax for all eligible agents and returns a DTO
        containing payment requests for the government to execute.
        """
    def record_revenue(self, result: TaxCollectionResult) -> None:
        """Updates internal ledgers based on a verified tax collection result."""
    def get_revenue_this_tick(self) -> dict[CurrencyCode, int]:
        """Returns the total revenue collected in the current tick (pennies)."""
    def get_revenue_breakdown_this_tick(self) -> dict[str, float]:
        """Returns the breakdown of revenue by tax type for the current tick."""
    def get_total_collected_this_tick(self) -> int:
        """Returns the total amount collected this tick (pennies)."""
    def get_tax_revenue(self) -> dict[str, int]:
        """Returns the all-time tax revenue breakdown (pennies)."""
    def get_total_collected_tax(self) -> dict[CurrencyCode, int]:
        """Returns the all-time total collected tax by currency (pennies)."""
    def reset_tick_flow(self) -> None:
        """Resets the per-tick revenue accumulators."""

class IWelfareService(Protocol):
    """
    A stateless service responsible for all welfare and subsidy logic.
    It does not hold state or have access to agent wallets.
    """
    def run_welfare_check(self, agents: list[IAgent], market_data: MarketSnapshotDTO, current_tick: int, gdp_history: list[float], welfare_budget_multiplier: float = 1.0) -> WelfareResultDTO:
        """
        Identifies agents needing support and returns a DTO containing
        welfare payment requests for the government to execute.
        """
    def provide_firm_bailout(self, firm: IAgent, amount: int, current_tick: int, is_solvent: bool) -> BailoutResultDTO | None:
        """
        Evaluates bailout eligibility and returns a DTO containing a loan request
        and a payment request. Returns None if not eligible.
        """
    def get_survival_cost(self, market_data: MarketSnapshotDTO) -> int:
        """Calculates current survival cost based on market prices (pennies)."""
    def get_spending_this_tick(self) -> int:
        """Returns total welfare spending for the current tick (pennies)."""
    def reset_tick_flow(self) -> None:
        """Resets the per-tick spending accumulator."""
IWelfareManager = IWelfareService

class IFiscalBondService(Protocol):
    """
    A stateless service responsible for sovereign debt logic:
    calculating yields, determining buyers (QE), and preparing issuance.
    """
    def calculate_yield(self, context: FiscalContextDTO) -> float:
        """Calculates bond yield based on debt-to-GDP and other factors."""
    def issue_bonds(self, request: BondIssueRequestDTO, context: FiscalContextDTO, buyer_pool: dict[str, Any]) -> BondIssuanceResultDTO:
        """
        Prepares a bond issuance transaction.
        Determines the buyer (e.g. Central Bank vs Commercial Bank) and creates the transaction request.
        """

class IGovernment(Protocol):
    """Facade for the government agent."""
    state: GovernmentStateDTO
    def make_policy_decision(self, market_snapshot: MarketSnapshotDTO) -> None: ...

@dataclass
class GovernmentExecutionContext:
    """Injectable dependencies for the ExecutionEngine."""
    settlement_system: Any
    finance_system: Any
    tax_service: ITaxService
    welfare_manager: IWelfareService
    fiscal_bond_service: IFiscalBondService
    infrastructure_manager: Any = ...
    public_manager: Any = ...

class IGovernmentDecisionEngine(Protocol):
    """
    Interface for the stateless decision-making engine.
    Determines *what* policy action to take.
    """
    def decide(self, state: GovernmentStateDTO, market_snapshot: MarketSnapshotDTO, central_bank: Any) -> PolicyDecisionDTO:
        """
        Decides on a policy action based on current state and market data.
        """

class IPolicyExecutionEngine(Protocol):
    """
    Interface for the stateless policy execution engine.
    Determines *how* to implement a decided action.
    """
    def execute(self, decision: PolicyDecisionDTO, current_state: GovernmentStateDTO, agents: list[IAgent], market_data: dict[str, Any], context: GovernmentExecutionContext) -> ExecutionResultDTO:
        """
        Takes a high-level policy decision and translates it into concrete,
        executable results by orchestrating various services (Tax, Welfare, etc.).
        """

@dataclass(frozen=True)
class VoteRecordDTO:
    """
    A single vote cast by an agent for a specific policy.
    """
    agent_id: int
    policy_type: str
    preferred_rate: float
    weight: float = ...

@dataclass(frozen=True)
class LobbyingEffortDTO:
    """
    Represents a firm's investment to influence policy.
    Financial values in Integer Pennies (Penny Standard).
    """
    firm_id: int
    target_industry: IndustryDomain
    investment_pennies: int
    desired_policy_shift: float

class IPoliticalOrchestrator(Protocol):
    """
    Protocol for the Political System.
    Aggregates votes and lobbying efforts to determine Government Policy.
    """
    def register_vote(self, vote: VoteRecordDTO) -> None:
        """Ingests a vote from an agent."""
    def register_lobbying(self, effort: LobbyingEffortDTO) -> None:
        """Ingests a lobbying effort from a firm."""
    def calculate_policy_outcome(self) -> dict[str, float]:
        """
        Aggregates all votes and lobbying to determine new policy rates.
        Returns a dict of {policy_type: new_rate}.
        """

from __future__ import annotations
from typing import Protocol, List, Any, Optional, Dict, TypedDict, runtime_checkable
from dataclasses import dataclass
from abc import abstractmethod
from modules.government.dtos import (
    FiscalPolicyDTO,
    MonetaryPolicyDTO,
    GovernmentStateDTO,
    PolicyDecisionDTO,
    ExecutionResultDTO,
    MacroEconomicSnapshotDTO,
    WelfareResultDTO,
    BailoutResultDTO,
    TaxCollectionResultDTO,
    FiscalContextDTO,
    BondIssueRequestDTO,
    BondIssuanceResultDTO,
    IAgent
)
from modules.government.welfare.api import IWelfareRecipient
from simulation.dtos.api import MarketSnapshotDTO
from modules.finance.api import TaxCollectionResult, IFinancialEntity
from modules.system.api import CurrencyCode

@runtime_checkable
class ITaxableHousehold(IFinancialEntity, IAgent, Protocol):
    """
    Protocol for households subject to wealth tax.
    Requires financial entity capabilities and specific household attributes.
    """
    is_active: bool
    is_employed: bool
    needs: Any

class BondRepaymentDetailsDTO(TypedDict):
    """
    A structured object carrying the details of a bond repayment.
    This DTO is expected to be present in the 'metadata' field of a 'bond_repayment' Transaction.

    Attributes:
        principal: The portion of the payment that constitutes principal repayment.
                   This amount is subject to monetary destruction if paid to the Central Bank.
        interest: The portion of the payment that constitutes an interest payment.
                  This is treated as a standard transfer and is not destroyed.
        bond_id: A unique identifier for the bond being serviced.
    """
    principal: float
    interest: float
    bond_id: str

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

class IWelfareService(Protocol):
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

class IGovernment(Protocol):
    """Facade for the government agent."""
    state: GovernmentStateDTO

    def make_policy_decision(self, market_snapshot: "MarketSnapshotDTO") -> None:
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
        state: GovernmentStateDTO,
        market_snapshot: MarketSnapshotDTO,
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
        current_state: GovernmentStateDTO,
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

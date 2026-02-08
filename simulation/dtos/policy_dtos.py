from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union, TYPE_CHECKING
from simulation.ai.enums import PolicyActionTag, PoliticalParty, EconomicSchool

if TYPE_CHECKING:
    from simulation.dtos import GovernmentStateDTO

@dataclass
class PolicyContextDTO:
    """
    Context for Government Policy Decisions.
    Pure DTO preventing direct access to Government agent.
    """
    agent_id: int
    tick: int
    sensory_data: Optional[GovernmentStateDTO]
    central_bank_base_rate: float
    locked_policies: List[PolicyActionTag]

    # Current State Snapshots (Immutable)
    current_welfare_budget_multiplier: float
    current_corporate_tax_rate: float
    current_income_tax_rate: float
    potential_gdp: float
    fiscal_stance: float

    ruling_party: Optional[PoliticalParty] = None

@dataclass
class ActionRequestDTO:
    """
    Request for a discrete action (e.g. fire advisor).
    """
    action_type: str # "FIRE_ADVISOR", etc.
    target: Optional[Union[EconomicSchool, Any]] = None
    params: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PolicyDecisionResultDTO:
    """
    Result of a policy decision.
    Contains updates to state and action requests.
    """
    policy_type: str
    status: str
    action_taken: str

    # State Updates (Optional - only if changed)
    updated_welfare_budget_multiplier: Optional[float] = None
    updated_corporate_tax_rate: Optional[float] = None
    updated_income_tax_rate: Optional[float] = None
    updated_potential_gdp: Optional[float] = None
    updated_fiscal_stance: Optional[float] = None

    # Discrete Action Request
    action_request: Optional[ActionRequestDTO] = None

    # Interest Rate Target (for Taylor Rule logging/return)
    interest_rate_target: Optional[float] = None
    utility: Optional[float] = None

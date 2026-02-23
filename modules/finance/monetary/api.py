from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Protocol, Dict, Any, Optional, runtime_checkable
from modules.system.api import CurrencyCode

# region: Enums

class MonetaryRuleType(Enum):
    """
    Defines the philosophical framework used by the Central Bank.
    """
    TAYLOR_RULE = auto()        # Interest Rate Targeting (Counter-cyclical)
    FRIEDMAN_K_PERCENT = auto() # Money Supply Targeting (Fixed Growth)
    MCCALLUM_RULE = auto()      # Monetary Base Targeting (NGDP Targeting)
    PEG_EXCHANGE_RATE = auto()  # Fixed Exchange Rate (Not implemented in V1)

class OMOActionType(Enum):
    """
    The type of Open Market Operation required to fulfill the policy.
    """
    NONE = auto()
    BUY_BONDS = auto()  # Quantitative Easing (Inject Cash)
    SELL_BONDS = auto() # Quantitative Tightening (Drain Cash)

# endregion

# region: DTOs

@dataclass(frozen=True)
class MacroEconomicSnapshotDTO:
    """
    Standardized view of the economy consumed by Monetary Strategies.
    SSoT: Provided by EconomyTracker / MarketSystem.
    """
    tick: int

    # Prices & Growth
    inflation_rate_annual: float # e.g., 0.02 for 2%
    nominal_gdp: int             # In pennies
    real_gdp_growth: float       # e.g., 0.03 for 3%

    # Employment
    unemployment_rate: float     # e.g., 0.05 for 5%

    # Monetary Aggregates
    current_m2_supply: int       # Total Money Supply (Cash + Deposits)
    current_monetary_base: int   # Cash in Circulation + Bank Reserves
    velocity_of_money: float     # V = GDP / M2

    # Derived
    output_gap: Optional[float] = None # (Current GDP - Potential GDP) / Potential GDP

@dataclass(frozen=True)
class MonetaryPolicyConfigDTO:
    """
    Configuration parameters for the active strategy.
    """
    rule_type: MonetaryRuleType

    # Targets
    inflation_target: float = 0.02
    unemployment_target: float = 0.05
    m2_growth_target: float = 0.03 # For Friedman Rule (k%)
    ngdp_target_growth: float = 0.04 # For McCallum Rule

    # Coefficients (Taylor Rule)
    taylor_alpha: float = 1.5 # Weight on Inflation
    taylor_beta: float = 0.5  # Weight on Output Gap
    neutral_rate: float = 0.02 # r*

    # Constraints
    min_interest_rate: float = 0.0 # Zero Lower Bound
    max_interest_rate: float = 0.20

@dataclass(frozen=True)
class MonetaryDecisionDTO:
    """
    The output of a Monetary Strategy.
    Instructs the Central Bank on what variables to target.
    """
    rule_type: MonetaryRuleType
    tick: int

    # Rate Target (Primary tool for Taylor Rule)
    target_interest_rate: float

    # Quantity Target (Primary tool for Friedman/McCallum)
    target_m2_supply: Optional[int] = None
    target_monetary_base: Optional[int] = None

    # Derived Action (For OMO Execution)
    omo_action: OMOActionType = OMOActionType.NONE
    omo_amount_pennies: int = 0

    reasoning: str = ""

# endregion

# region: Protocols

@runtime_checkable
class IMonetaryStrategy(Protocol):
    """
    Interface for implementing a Monetary Policy Rule.
    Decouples the logic (Thinker) from the Central Bank (Actor).
    """

    @property
    def rule_type(self) -> MonetaryRuleType:
        """Returns the type of rule implemented."""
        ...

    def calculate_decision(
        self,
        snapshot: MacroEconomicSnapshotDTO,
        current_rate: float,
        config: MonetaryPolicyConfigDTO
    ) -> MonetaryDecisionDTO:
        """
        Computes the target interest rate or money supply targets
        based on the provided economic snapshot.
        """
        ...

@runtime_checkable
class IMonetaryEngine(Protocol):
    """
    Context holder that manages the active strategy and executes it.
    """
    active_policy: IMonetaryStrategy

    def set_policy(self, policy: IMonetaryStrategy) -> None:
        ...

    def execute_tick(
        self,
        snapshot: MacroEconomicSnapshotDTO,
        current_rate: float
    ) -> MonetaryDecisionDTO:
        ...

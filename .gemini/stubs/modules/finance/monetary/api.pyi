from dataclasses import dataclass, field as field
from enum import Enum
from modules.system.api import CurrencyCode as CurrencyCode
from typing import Protocol

class MonetaryRuleType(Enum):
    """
    Defines the philosophical framework used by the Central Bank.
    """
    TAYLOR_RULE = ...
    FRIEDMAN_K_PERCENT = ...
    MCCALLUM_RULE = ...
    PEG_EXCHANGE_RATE = ...

class OMOActionType(Enum):
    """
    The type of Open Market Operation required to fulfill the policy.
    """
    NONE = ...
    BUY_BONDS = ...
    SELL_BONDS = ...

@dataclass(frozen=True)
class MacroEconomicSnapshotDTO:
    """
    Standardized view of the economy consumed by Monetary Strategies.
    SSoT: Provided by EconomyTracker / MarketSystem.
    """
    tick: int
    inflation_rate_annual: float
    nominal_gdp: int
    real_gdp_growth: float
    unemployment_rate: float
    current_m2_supply: int
    current_monetary_base: int
    velocity_of_money: float
    output_gap: float | None = ...

@dataclass(frozen=True)
class MonetaryPolicyConfigDTO:
    """
    Configuration parameters for the active strategy.
    """
    rule_type: MonetaryRuleType
    inflation_target: float = ...
    unemployment_target: float = ...
    m2_growth_target: float = ...
    ngdp_target_growth: float = ...
    taylor_alpha: float = ...
    taylor_beta: float = ...
    neutral_rate: float = ...
    min_interest_rate: float = ...
    max_interest_rate: float = ...

@dataclass(frozen=True)
class MonetaryDecisionDTO:
    """
    The output of a Monetary Strategy.
    Instructs the Central Bank on what variables to target.
    """
    rule_type: MonetaryRuleType
    tick: int
    target_interest_rate: float
    target_m2_supply: int | None = ...
    target_monetary_base: int | None = ...
    omo_action: OMOActionType = ...
    omo_amount_pennies: int = ...
    reasoning: str = ...

class IMonetaryStrategy(Protocol):
    """
    Interface for implementing a Monetary Policy Rule.
    Decouples the logic (Thinker) from the Central Bank (Actor).
    """
    @property
    def rule_type(self) -> MonetaryRuleType:
        """Returns the type of rule implemented."""
    def calculate_decision(self, snapshot: MacroEconomicSnapshotDTO, current_rate: float, config: MonetaryPolicyConfigDTO) -> MonetaryDecisionDTO:
        """
        Computes the target interest rate or money supply targets
        based on the provided economic snapshot.
        """

class IMonetaryEngine(Protocol):
    """
    Context holder that manages the active strategy and executes it.
    """
    active_policy: IMonetaryStrategy
    def set_policy(self, policy: IMonetaryStrategy) -> None: ...
    def execute_tick(self, snapshot: MacroEconomicSnapshotDTO, current_rate: float) -> MonetaryDecisionDTO: ...

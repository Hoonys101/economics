import logging
from dataclasses import dataclass
from modules.demographics.api import IDemographicManager as IDemographicManager
from modules.finance.api import IFinancialEntity as IFinancialEntity
from simulation.dtos.api import SimulationState as SimulationState
from simulation.models import Transaction as Transaction
from typing import Any, Protocol

@dataclass(frozen=True)
class LifecycleConfigDTO:
    """
    Strictly typed configuration DTO for the Lifecycle and Aging systems.
    Replaces loose config_module getattr calls and enforces the Penny Standard.
    """
    assets_closure_threshold_pennies: int
    firm_closure_turns_threshold: int
    liquidity_need_increase_rate: float
    distress_grace_period: int
    survival_need_death_threshold: float
    default_fallback_price_pennies: int
    @classmethod
    def from_config_module(cls, config_module: Any) -> LifecycleConfigDTO:
        """
        Factory method to safely construct the DTO from a dynamic config module.
        Centralizes the float-to-penny conversions and default fallbacks.
        """

@dataclass(frozen=True)
class BirthConfigDTO:
    """Configuration DTO for the BirthSystem."""
    initial_household_assets_pennies: int
    reproduction_rate: float
    immigration_rate: float
    max_population_cap: int
    reproduction_age_start: int
    reproduction_age_end: int
    @classmethod
    def from_config_module(cls, config_module: Any) -> BirthConfigDTO: ...

@dataclass(frozen=True)
class DeathConfigDTO:
    """Configuration DTO for the DeathSystem."""
    death_tax_rate: float
    min_inheritance_pennies: int
    liquidation_fee_pennies: int
    default_fallback_price_pennies: int
    @classmethod
    def from_config_module(cls, config_module: Any) -> DeathConfigDTO: ...

class ILifecycleSubsystem(Protocol):
    """
    Protocol for discrete lifecycle systems (Birth, Aging, Death).
    Adheres to SEO Pattern: Stateless execution on State DTO.
    """
    def execute(self, state: SimulationState) -> list[Transaction]:
        """
        Executes the lifecycle logic for the current tick.
        Returns a list of transactions (e.g., inheritance, fees) to be processed.
        """

class IAgingSystem(ILifecycleSubsystem, Protocol):
    """
    Responsible for incrementing age, updating biological needs,
    and performing health/distress checks for all agents.
    """
    def __init__(self, config: LifecycleConfigDTO, demographic_manager: IDemographicManager, logger: logging.Logger) -> None: ...

class IBirthSystem(ILifecycleSubsystem, Protocol):
    """
    Responsible for creating new agents (Households) via reproduction
    and handling immigration entry.
    """
class IDeathSystem(ILifecycleSubsystem, Protocol):
    """
    Responsible for handling agent death, liquidation of assets,
    and inheritance processing.
    """

class IFinanceEngine(Protocol):
    def check_bankruptcy(self, finance_state: Any, config: Any) -> None: ...

class IAgingFirm(Protocol):
    id: Any
    is_active: bool
    age: int
    needs: dict[str, float]
    wallet: IFinancialEntity
    finance_state: Any
    config: Any
    finance_engine: IFinanceEngine
    def get_all_items(self) -> dict[str, Any]: ...

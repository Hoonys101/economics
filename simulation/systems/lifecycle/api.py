from __future__ import annotations
from typing import Protocol, List, Any, Dict, runtime_checkable, TYPE_CHECKING, Union, Optional
from dataclasses import dataclass
import logging
from simulation.models import Transaction
from modules.finance.api import IFinancialEntity
from modules.demographics.api import IDemographicManager

if TYPE_CHECKING:
    from simulation.dtos.api import SimulationState
    from modules.simulation.api import AgentID

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
    def from_config_module(cls, config_module: Any) -> "LifecycleConfigDTO":
        """
        Factory method to safely construct the DTO from a dynamic config module.
        Centralizes the float-to-penny conversions and default fallbacks.
        """
        return cls(
            assets_closure_threshold_pennies=int(getattr(config_module, "ASSETS_CLOSURE_THRESHOLD", 0.0) * 100),
            firm_closure_turns_threshold=int(getattr(config_module, "FIRM_CLOSURE_TURNS_THRESHOLD", 5)),
            liquidity_need_increase_rate=float(getattr(config_module, "LIQUIDITY_NEED_INCREASE_RATE", 1.0)),
            distress_grace_period=int(getattr(config_module, "DISTRESS_GRACE_PERIOD", 5)),
            survival_need_death_threshold=float(getattr(config_module, "SURVIVAL_NEED_DEATH_THRESHOLD", 100.0)),
            default_fallback_price_pennies=int(getattr(config_module, "DEFAULT_FALLBACK_PRICE", 1000))
        )

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
    def from_config_module(cls, config_module: Any) -> "BirthConfigDTO":
        return cls(
            initial_household_assets_pennies=int(getattr(config_module, "INITIAL_HOUSEHOLD_ASSETS", 100000) * 100),
            reproduction_rate=float(getattr(config_module, "REPRODUCTION_RATE", 0.01)),
            immigration_rate=float(getattr(config_module, "IMMIGRATION_RATE", 0.005)),
            max_population_cap=int(getattr(config_module, "MAX_POPULATION_CAP", 5000)),
            reproduction_age_start=int(getattr(config_module, "REPRODUCTION_AGE_START", 20)),
            reproduction_age_end=int(getattr(config_module, "REPRODUCTION_AGE_END", 45))
        )

@dataclass(frozen=True)
class DeathConfigDTO:
    """Configuration DTO for the DeathSystem."""
    death_tax_rate: float
    min_inheritance_pennies: int
    liquidation_fee_pennies: int
    default_fallback_price_pennies: int

    @classmethod
    def from_config_module(cls, config_module: Any) -> "DeathConfigDTO":
        default_price_float = getattr(config_module, "GOODS_INITIAL_PRICE", {}).get("default", 10.0)
        return cls(
            death_tax_rate=float(getattr(config_module, "DEATH_TAX_RATE", 0.1)),
            min_inheritance_pennies=int(getattr(config_module, "MIN_INHERITANCE", 1000) * 100),
            liquidation_fee_pennies=int(getattr(config_module, "LIQUIDATION_FEE", 500) * 100),
            default_fallback_price_pennies=int(default_price_float * 100)
        )

@runtime_checkable
class IDeathContext(Protocol):
    """
    Scoped context for Lifecycle systems to prevent God DTO coupling.
    """
    time: int
    households: List[Any]
    firms: List[Any]
    agents: Dict[Any, Any]
    markets: Dict[str, Any]
    primary_government: Optional[Any]
    inactive_agents: Optional[Dict[Any, Any]]
    currency_registry_handler: Optional[Any]
    currency_holders: Optional[List[Any]]

@runtime_checkable
class ILifecycleSubsystem(Protocol):
    """
    Protocol for discrete lifecycle systems (Birth, Aging, Death).
    Adheres to SEO Pattern: Stateless execution on Scoped Context.
    """
    def execute(self, state: Union[SimulationState, IDeathContext]) -> List[Transaction]:
        """
        Executes the lifecycle logic for the current tick.
        Returns a list of transactions (e.g., inheritance, fees) to be processed.
        """
        ...

@runtime_checkable
class IAgingSystem(ILifecycleSubsystem, Protocol):
    """
    Responsible for incrementing age, updating biological needs,
    and performing health/distress checks for all agents.
    """
    def __init__(self, config: LifecycleConfigDTO, demographic_manager: IDemographicManager, logger: logging.Logger) -> None:
        ...

@runtime_checkable
class IBirthSystem(ILifecycleSubsystem, Protocol):
    """
    Responsible for creating new agents (Households) via reproduction
    and handling immigration entry.
    """
    ...

@runtime_checkable
class IDeathSystem(ILifecycleSubsystem, Protocol):
    """
    Responsible for handling agent death, liquidation of assets,
    and inheritance processing.
    """
    ...

@runtime_checkable
class IFinanceEngine(Protocol):
    def check_bankruptcy(self, finance_state: Any, config: Any) -> None: ...

@runtime_checkable
class IAgingFirm(Protocol):
    id: Any
    is_active: bool
    age: int
    needs: Dict[str, float]
    wallet: IFinancialEntity
    finance_state: Any
    config: Any
    finance_engine: IFinanceEngine

    def get_all_items(self) -> Dict[str, Any]: ...

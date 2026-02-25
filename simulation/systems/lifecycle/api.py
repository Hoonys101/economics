from __future__ import annotations
from typing import Protocol, List, Any, Dict, runtime_checkable, TYPE_CHECKING
from dataclasses import dataclass
import logging
from simulation.dtos.api import SimulationState
from simulation.models import Transaction
from modules.finance.api import IFinancialEntity
from modules.demographics.api import IDemographicManager

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

@runtime_checkable
class ILifecycleSubsystem(Protocol):
    """
    Protocol for discrete lifecycle systems (Birth, Aging, Death).
    Adheres to SEO Pattern: Stateless execution on State DTO.
    """
    def execute(self, state: SimulationState) -> List[Transaction]:
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

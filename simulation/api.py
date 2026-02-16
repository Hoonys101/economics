"""
This module serves as the public API for the simulation package.
It re-exports core classes and functions from various sub-modules,
providing a centralized and clear interface for external interaction.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union, TYPE_CHECKING

from simulation.ai.enums import Personality
from simulation.models import Share, Order as OrderDTO

if TYPE_CHECKING:
    from simulation.dtos.scenario import StressScenarioConfig

from .core_markets import Market
from .engine import Simulation, EconomicIndicatorTracker
from .core_agents import Household, Talent, Skill
from .firms import Firm
from .decisions.action_proposal import ActionProposalEngine
from .decisions import BaseDecisionEngine, FirmDecisionEngine, HouseholdDecisionEngine
from .ai.ai_training_manager import AITrainingManager
from .ai_model import AIDecisionEngine, AIEngineRegistry
from .ai.state_builder import StateBuilder
from .ai.model_wrapper import ModelWrapper
from .ai.reward_calculator import RewardCalculator

# --- Configuration DTOs ---

from .dtos.config_dtos import HouseholdConfigDTO, FirmConfigDTO

# --- Core Data DTOs ---

@dataclass(frozen=True)
class GoodsDTO:
    """
    Represents a specific quantity of a good in an agent's inventory.
    """
    name: str
    quantity: float

@dataclass(frozen=True)
class GoodsInfoDTO:
    """
    Represents static information about a good type (Catalog).
    """
    id: str
    name: str
    category: str
    is_durable: bool
    is_essential: bool
    initial_price: float
    base_need_satisfaction: float
    quality_modifier: float
    type: str
    satiety: float
    decay_rate: float

@dataclass(frozen=True)
class MarketHistoryDTO:
    """
    Represents historical market data.
    """
    avg_price: float
    trade_volume: float
    best_ask: float
    best_bid: float
    avg_ask: float
    avg_bid: float
    worst_ask: float
    worst_bid: float

# MarketSnapshotDTO is now imported from modules.system.api
from modules.system.api import MarketSnapshotDTO

@dataclass(frozen=True)
class GovernmentPolicyDTO:
    """
    A pure-data snapshot of current government policies affecting agent decisions.
    """
    income_tax_rate: float
    sales_tax_rate: float
    corporate_tax_rate: float
    base_interest_rate: float

# --- State DTOs ---

from modules.household.dtos import HouseholdStateDTO
from modules.simulation.dtos.api import FirmStateDTO

# --- Context DTO ---

@dataclass(frozen=True)
class DecisionContext:
    """
    A pure data container for decision-making.
    """
    goods_data: List[GoodsInfoDTO]
    market_data: Dict[str, MarketHistoryDTO]
    current_time: int

    # State DTO representing the agent's current condition
    state: Union[HouseholdStateDTO, FirmStateDTO]

    # Static configuration values relevant to the agent type
    config: Union[HouseholdConfigDTO, FirmConfigDTO]

    # Environment Snapshots
    market_snapshot: Optional[MarketSnapshotDTO] = None
    government_policy: Optional[GovernmentPolicyDTO] = None

    stress_scenario_config: Optional['StressScenarioConfig'] = None

__all__ = [
    "Market",
    "Simulation",
    "EconomicIndicatorTracker",
    "Household",
    "Talent",
    "Skill",
    "Firm",
    "ActionProposalEngine",
    "BaseDecisionEngine",
    "FirmDecisionEngine",
    "HouseholdDecisionEngine",
    "AITrainingManager",
    "AIDecisionEngine",
    "AIEngineRegistry",
    "StateBuilder",
    "ModelWrapper",
    "RewardCalculator",
    # New DTOs
    "HouseholdConfigDTO",
    "FirmConfigDTO",
    "GoodsDTO",
    "GoodsInfoDTO",
    "MarketHistoryDTO",
    "OrderDTO",
    "MarketSnapshotDTO",
    "GovernmentPolicyDTO",
    "HouseholdStateDTO",
    "FirmStateDTO",
    "DecisionContext",
]

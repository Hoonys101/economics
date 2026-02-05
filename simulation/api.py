"""
This module serves as the public API for the simulation package.
It re-exports core classes and functions from various sub-modules,
providing a centralized and clear interface for external interaction.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union, TYPE_CHECKING

from simulation.ai.enums import Personality
from simulation.models import Share

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

@dataclass
class GoodsDTO:
    """
    Represents a specific quantity of a good in an agent's inventory.
    """
    name: str
    quantity: float

@dataclass
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

@dataclass
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

@dataclass
class OrderDTO:
    """
    Represents an order in the market.
    """
    agent_id: int
    item_id: str
    quantity: float
    price: float

@dataclass
class MarketSnapshotDTO:
    """
    A pure-data snapshot of the state of all markets at a point in time.
    """
    prices: Dict[str, float]
    volumes: Dict[str, float]
    asks: Dict[str, List[OrderDTO]]
    best_asks: Dict[str, float]

@dataclass
class GovernmentPolicyDTO:
    """
    A pure-data snapshot of current government policies affecting agent decisions.
    """
    income_tax_rate: float
    sales_tax_rate: float
    corporate_tax_rate: float
    base_interest_rate: float

# --- State DTOs ---

@dataclass
class HouseholdStateDTO:
    """
    A read-only DTO containing the complete state of a Household agent.
    """
    id: int
    assets: float
    inventory: List[GoodsDTO]
    needs: Dict[str, float]
    preference_asset: float
    preference_social: float
    preference_growth: float
    personality: Personality
    durable_assets: List[Dict[str, Any]]
    expected_inflation: Dict[str, float]
    is_employed: bool
    current_wage: float
    wage_modifier: float
    is_homeless: bool
    residing_property_id: Optional[int]
    owned_properties: List[int]
    portfolio_holdings: Dict[int, Share]
    risk_aversion: float
    agent_data: Dict[str, Any]
    perceived_prices: Dict[str, float] = field(default_factory=dict)
    conformity: float = 0.5
    social_rank: float = 0.5
    approval_rating: int = 1
    optimism: float = 0.5
    ambition: float = 0.5
    perceived_fair_price: Dict[str, float] = field(default_factory=dict)
    sentiment_index: float = 0.5

@dataclass
class FirmStateDTO:
    """
    A read-only DTO containing the complete state of a Firm agent.
    """
    id: int
    assets: float
    is_active: bool
    inventory: List[GoodsDTO]
    inventory_quality: Dict[str, float]
    input_inventory: Dict[str, float]

    # Production & Tech
    current_production: float
    productivity_factor: float
    production_target: float
    capital_stock: float
    base_quality: float
    automation_level: float
    specialization: str

    # Finance & Market
    total_shares: float
    treasury_shares: float
    dividend_rate: float
    is_publicly_traded: bool
    valuation: float
    revenue_this_turn: Dict[str, float]
    expenses_this_tick: Dict[str, float]
    consecutive_loss_turns: int
    altman_z_score: float
    price_history: Dict[str, float]
    profit_history: List[float]

    # Brand & Sales
    brand_awareness: float
    perceived_quality: float
    marketing_budget: float

    # HR
    employees: List[int]
    employees_data: Dict[int, Dict[str, Any]]

    # AI/Agent Data
    agent_data: Dict[str, Any]
    system2_guidance: Dict[str, Any]

    # Parity Fields
    sentiment_index: float = 0.5

# --- Context DTO ---

@dataclass
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

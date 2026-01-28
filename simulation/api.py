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

@dataclass
class HouseholdConfigDTO:
    """Static configuration values relevant to household decisions."""
    survival_need_consumption_threshold: float
    target_food_buffer_quantity: float
    food_purchase_max_per_tick: float
    assets_threshold_for_other_actions: float
    wage_decay_rate: float
    reservation_wage_floor: float
    survival_critical_turns: float
    labor_market_min_wage: float
    # New from Household.make_decision refactoring
    household_low_asset_threshold: float
    household_low_asset_wage: float
    household_default_wage: float

    # AI Engine requirements
    market_price_fallback: float
    need_factor_base: float
    need_factor_scale: float
    valuation_modifier_base: float
    valuation_modifier_range: float
    household_max_purchase_quantity: float
    bulk_buy_need_threshold: float
    bulk_buy_agg_threshold: float
    bulk_buy_moderate_ratio: float
    panic_buying_threshold: float
    hoarding_factor: float
    deflation_wait_threshold: float
    delay_factor: float
    dsr_critical_threshold: float
    budget_limit_normal_ratio: float
    budget_limit_urgent_need: float
    budget_limit_urgent_ratio: float
    min_purchase_quantity: float
    job_quit_threshold_base: float
    job_quit_prob_base: float
    job_quit_prob_scale: float
    stock_market_enabled: bool
    household_min_assets_for_investment: float
    stock_investment_equity_delta_threshold: float
    stock_investment_diversification_count: int
    expected_startup_roi: float
    startup_cost: float
    debt_repayment_ratio: float
    debt_repayment_cap: float
    debt_liquidity_ratio: float
    # Added for parity
    initial_rent_price: float
    # Added for AI Engine Purity
    default_mortgage_rate: float
    # Housing Manager
    enable_vanity_system: bool
    mimicry_factor: float
    maintenance_rate_per_tick: float

@dataclass
class FirmConfigDTO:
    """Static configuration values relevant to firm decisions."""
    firm_min_production_target: float
    firm_max_production_target: float
    startup_cost: float
    seo_trigger_ratio: float
    seo_max_sell_ratio: float
    automation_cost_per_pct: float
    firm_safety_margin: float
    automation_tax_rate: float
    altman_z_score_threshold: float
    dividend_suspension_loss_ticks: int
    dividend_rate_min: float
    dividend_rate_max: float
    labor_alpha: float
    automation_labor_reduction: float
    severance_pay_weeks: float
    labor_market_min_wage: float
    overstock_threshold: float
    understock_threshold: float
    production_adjustment_factor: float
    max_sell_quantity: float
    invisible_hand_sensitivity: float
    capital_to_output_ratio: float

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
    revenue_this_turn: float
    expenses_this_tick: float
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

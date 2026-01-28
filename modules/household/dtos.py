from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from collections import deque, defaultdict
import copy

from simulation.ai.api import Personality
from simulation.models import Share, Skill, Talent, Order
from simulation.portfolio import Portfolio

if TYPE_CHECKING:
    from simulation.core_markets import Market
    from simulation.interfaces.market_interface import IMarket
    from simulation.dtos import LeisureType

@dataclass
class HouseholdStateDTO:
    """
    A read-only DTO containing the state of a Household agent.
    Used by the DecisionEngine to make decisions without direct dependency on the Household class.
    """
    id: int
    assets: float
    inventory: Dict[str, float]
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

    # Additional fields needed by DecisionEngine
    conformity: float = 0.5
    social_rank: float = 0.5
    approval_rating: int = 1
    optimism: float = 0.5
    ambition: float = 0.5

    # WO-108: Parity Fields
    perceived_fair_price: Dict[str, float] = field(default_factory=dict)
    sentiment_index: float = 0.5

@dataclass
class BioStateDTO:
    """Internal state for BioComponent."""
    id: int # Agent ID
    age: float
    gender: str
    generation: int
    is_active: bool
    needs: Dict[str, float]
    parent_id: Optional[int] = None
    spouse_id: Optional[int] = None
    children_ids: List[int] = field(default_factory=list)

    def copy(self) -> "BioStateDTO":
        new_state = copy.copy(self)
        new_state.needs = self.needs.copy()
        new_state.children_ids = list(self.children_ids)
        return new_state

@dataclass
class EconStateDTO:
    """Internal state for EconComponent."""
    # Assets & Inventory
    assets: float
    inventory: Dict[str, float]
    inventory_quality: Dict[str, float]
    durable_assets: List[Dict[str, Any]]
    portfolio: Portfolio # Treated as mutable component state, but we should copy it if needed

    # Labor
    is_employed: bool
    employer_id: Optional[int]
    current_wage: float
    wage_modifier: float
    labor_skill: float
    education_xp: float
    education_level: int
    expected_wage: float
    talent: Talent # Assuming immutable or shared reference ok
    skills: Dict[str, Skill]
    aptitude: float

    # Housing
    owned_properties: List[int]
    residing_property_id: Optional[int]
    is_homeless: bool
    home_quality_score: float
    housing_target_mode: str

    # History & Memory
    housing_price_history: deque
    market_wage_history: deque
    shadow_reservation_wage: float
    last_labor_offer_tick: int
    last_fired_tick: int
    job_search_patience: int

    # Consumption & Inflation
    current_consumption: float
    current_food_consumption: float
    expected_inflation: Dict[str, float]
    perceived_avg_prices: Dict[str, float]
    price_history: defaultdict[str, deque]
    price_memory_length: int
    adaptation_rate: float

    # Income Tracking (Transient per tick)
    labor_income_this_tick: float
    capital_income_this_tick: float

    # Legacy / Compatibility
    credit_frozen_until_tick: int = 0
    initial_assets_record: float = 0.0

    def copy(self) -> "EconStateDTO":
        new_state = copy.copy(self)
        new_state.inventory = self.inventory.copy()
        new_state.inventory_quality = self.inventory_quality.copy()
        # Deep copy durable assets as they are dicts
        new_state.durable_assets = [d.copy() for d in self.durable_assets]

        # Portfolio copy
        new_portfolio = Portfolio(self.portfolio.owner_id)
        # Manually copy holdings.
        for k, v in self.portfolio.holdings.items():
            new_portfolio.holdings[k] = copy.copy(v)
        new_state.portfolio = new_portfolio

        new_state.owned_properties = list(self.owned_properties)
        new_state.skills = {k: copy.copy(v) for k, v in self.skills.items()}
        new_state.housing_price_history = copy.copy(self.housing_price_history) # deque copy
        new_state.market_wage_history = copy.copy(self.market_wage_history)
        new_state.expected_inflation = self.expected_inflation.copy()
        new_state.perceived_avg_prices = self.perceived_avg_prices.copy()

        # Helper for defaultdict(deque)
        maxlen = self.price_memory_length
        new_state.price_history = defaultdict(lambda: deque(maxlen=maxlen))
        for k, v in self.price_history.items():
            new_state.price_history[k] = copy.copy(v)

        return new_state

@dataclass
class SocialStateDTO:
    """Internal state for SocialComponent."""
    personality: Personality
    social_status: float
    discontent: float
    approval_rating: int

    conformity: float
    social_rank: float
    quality_preference: float

    brand_loyalty: Dict[int, float]
    last_purchase_memory: Dict[str, int]

    patience: float
    optimism: float
    ambition: float

    last_leisure_type: str # LeisureType is str alias usually

    # Psychology Component State
    survival_need_high_turns: int = 0
    desire_weights: Dict[str, float] = field(default_factory=dict)

    def copy(self) -> "SocialStateDTO":
        new_state = copy.copy(self)
        new_state.brand_loyalty = self.brand_loyalty.copy()
        new_state.last_purchase_memory = self.last_purchase_memory.copy()
        new_state.desire_weights = self.desire_weights.copy()
        return new_state

@dataclass
class CloningRequestDTO:
    """Data required to clone a household."""
    new_id: int
    initial_assets_from_parent: float
    current_tick: int

@dataclass
class EconContextDTO:
    """Context for economic operations."""
    markets: Dict[str, "IMarket"]
    market_data: Dict[str, Any]
    current_time: int

@dataclass
class SocialContextDTO:
    """Context for social operations."""
    current_time: int
    market_data: Optional[Dict[str, Any]] = None

@dataclass
class LifecycleDTO:
    """State data required for lifecycle updates."""
    is_employed: bool

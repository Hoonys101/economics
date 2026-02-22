from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from collections import deque, defaultdict
import copy

from simulation.ai.api import Personality
from simulation.models import Share, Skill, Talent, Order
from simulation.portfolio import Portfolio
from modules.system.api import CurrencyCode # Added for Phase 33
from modules.finance.wallet.api import IWallet
from modules.common.enums import IndustryDomain

if TYPE_CHECKING:
    from simulation.core_markets import Market
    from simulation.interfaces.market_interface import IMarket
    from simulation.dtos import LeisureType

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

    # --- Wave 4: Health & Marriage Extensions ---
    # Biological Sex (Reproduction Logic, distinct from social 'gender')
    sex: str = "F"  # "M" or "F"
    # Health Dynamics
    health_status: float = 1.0  # 0.0 (Dead) to 1.0 (Perfect)
    has_disease: bool = False  # Condition triggering medical utility demand
    # --------------------------------------------

    # Moved from SocialStateDTO for better alignment with NeedsEngine
    survival_need_high_turns: int = 0

    def copy(self) -> "BioStateDTO":
        new_state = copy.copy(self)
        new_state.needs = self.needs.copy()
        new_state.children_ids = list(self.children_ids)
        return new_state

@dataclass
class EconStateDTO:
    """
    Internal state for EconComponent.
    MIGRATION: Monetary values are integers (pennies).
    """
    # Assets & Inventory
    wallet: IWallet # Changed for WO-4.2A Wallet Abstraction
    # assets: Dict[CurrencyCode, float] # DEPRECATED, access via wallet
    inventory: Dict[str, float]
    inventory_quality: Dict[str, float]
    durable_assets: List[Dict[str, Any]]
    portfolio: Portfolio # Treated as mutable component state, but we should copy it if needed

    # Labor
    is_employed: bool
    employer_id: Optional[int]
    current_wage_pennies: int
    wage_modifier: float
    labor_skill: float
    education_xp: float
    education_level: int

    # Housing
    owned_properties: List[int]
    residing_property_id: Optional[int]
    is_homeless: bool
    home_quality_score: float
    housing_target_mode: str

    # History & Memory
    housing_price_history: deque
    market_wage_history: deque
    shadow_reservation_wage_pennies: int
    last_labor_offer_tick: int
    last_fired_tick: int
    job_search_patience: int
    employment_start_tick: int

    # Consumption & Inflation
    current_consumption: float
    current_food_consumption: float
    expected_inflation: Dict[str, float]
    perceived_avg_prices: Dict[str, float]
    price_history: defaultdict[str, deque]
    price_memory_length: int
    adaptation_rate: float

    # Income Tracking (Transient per tick)
    labor_income_this_tick_pennies: int
    capital_income_this_tick_pennies: int

    # Expenditure Tracking (Transient per tick)
    consumption_expenditure_this_tick_pennies: int
    food_expenditure_this_tick_pennies: int

    # Phase 4.1: Dynamic Cognitive Filter & Talent & Major
    market_insight: float = 0.5
    expected_wage_pennies: int = 1000
    talent: Talent = field(default_factory=lambda: Talent(1.0, 1.0, 1.0))
    skills: Dict[str, Skill] = field(default_factory=dict)
    aptitude: float = 1.0
    
    # --- Wave 3: Heterogeneous Labor State ---
    
    # Public Signal (The "Degree")
    major: Optional[IndustryDomain] = None 
    
    # Private Truth (The "Veil")
    # Hidden innate talent per domain (0.0 - 1.0).
    hidden_talent: Dict[IndustryDomain, float] = field(default_factory=dict)
    
    # Experience (Public)
    # Cumulative years worked per domain.
    experience: Dict[IndustryDomain, float] = field(default_factory=dict)
    
    # Sunk Cost (Psychological)
    # Tracks total money spent on education.
    sunk_cost_pennies: int = 0

    # Legacy / Compatibility
    credit_frozen_until_tick: int = 0
    initial_assets_record_pennies: int = 0

    @property
    def assets(self) -> Dict[CurrencyCode, int]:
        """Legacy compatibility accessor."""
        return self.wallet.get_all_balances()

    def copy(self) -> "EconStateDTO":
        new_state = copy.copy(self)

        # Deep copy wallet to ensure snapshot isolation
        from modules.finance.wallet.wallet import Wallet
        new_wallet = Wallet(self.wallet.owner_id, self.wallet.get_all_balances())
        new_state.wallet = new_wallet

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
    # survival_need_high_turns: int = 0 # Moved to BioStateDTO
    desire_weights: Dict[str, float] = field(default_factory=dict)

    # WO-157: Demand Elasticity
    demand_elasticity: float = 1.0

    # WO-4.3: Political Component State
    economic_vision: float = 0.5
    trust_score: float = 0.5

    def copy(self) -> "SocialStateDTO":
        new_state = copy.copy(self)
        new_state.brand_loyalty = self.brand_loyalty.copy()
        new_state.last_purchase_memory = self.last_purchase_memory.copy()
        new_state.desire_weights = self.desire_weights.copy()
        return new_state

@dataclass
class HouseholdSnapshotDTO:
    """
    [TD-194] A structured, read-only snapshot of a Household agent's complete state,
    composed of the states of its underlying components.
    Serves as the primary data contract for decision-making systems.
    Replaces HouseholdStateDTO.
    """
    id: int
    bio_state: BioStateDTO
    econ_state: EconStateDTO
    social_state: SocialStateDTO
    market_insight: float = 0.5 # Phase 4.1: Mirrored from EconState for Decision Logic
    monthly_income_pennies: int = 0 # Added for precision in financial decisions (TD-206)
    monthly_debt_payments_pennies: int = 0 # Added for precision in financial decisions (TD-206)
    major: Optional[IndustryDomain] = None # Mirrored from EconState

@dataclass
class HouseholdStateDTO:
    """
    [DEPRECATED] Use HouseholdSnapshotDTO instead.
    A read-only DTO containing the state of a Household agent.
    Used by the DecisionEngine to make decisions without direct dependency on the Household class.
    MIGRATION: Monetary values are integers (pennies).
    """
    id: int
    assets: Dict[CurrencyCode, int] # Changed for Phase 33
    inventory: Dict[str, float]
    needs: Dict[str, float]
    preference_asset: float
    preference_social: float
    preference_growth: float
    personality: Personality
    durable_assets: List[Dict[str, Any]]
    expected_inflation: Dict[str, float]
    is_employed: bool
    current_wage_pennies: int
    wage_modifier: float
    is_homeless: bool
    residing_property_id: Optional[int]
    owned_properties: List[int]
    portfolio_holdings: Dict[int, Share]
    risk_aversion: float
    agent_data: Dict[str, Any]
    market_insight: float = 0.5 # Phase 4.1: Dynamic Cognitive Filter
    major: Optional[IndustryDomain] = None
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

    # WO-157: Demand Elasticity
    demand_elasticity: float = 1.0

    # TD-206: Financial Precision (Parity with Snapshot)
    monthly_income_pennies: int = 0
    monthly_debt_payments_pennies: int = 0

@dataclass
class CloningRequestDTO:
    """Data required to clone a household."""
    new_id: int
    initial_assets_from_parent: Dict[CurrencyCode, int] # Changed for Phase 33
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

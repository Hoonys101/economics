from _typeshed import Incomplete
from collections import defaultdict, deque
from dataclasses import dataclass, field
from modules.common.enums import IndustryDomain as IndustryDomain
from modules.finance.wallet.api import IWallet as IWallet
from modules.system.api import CurrencyCode as CurrencyCode
from simulation.ai.api import Personality as Personality
from simulation.core_markets import Market as Market
from simulation.dtos import LeisureType as LeisureType
from simulation.interfaces.market_interface import IMarket as IMarket
from simulation.models import Order as Order, Share as Share, Skill as Skill, Talent
from simulation.portfolio import Portfolio
from typing import Any

@dataclass
class DurableAssetDTO:
    """Represents a durable asset owned by the household."""
    item_id: str
    quality: float
    remaining_life: int
    def copy(self) -> DurableAssetDTO: ...

@dataclass
class BioStateDTO:
    """Internal state for BioComponent."""
    id: int
    age: float
    gender: str
    generation: int
    is_active: bool
    needs: dict[str, float]
    parent_id: int | None = ...
    spouse_id: int | None = ...
    children_ids: list[int] = field(default_factory=list)
    sex: str = ...
    health_status: float = ...
    has_disease: bool = ...
    survival_need_high_turns: int = ...
    def copy(self) -> BioStateDTO: ...

@dataclass
class EconStateDTO:
    """
    Internal state for EconComponent.
    MIGRATION: Monetary values are integers (pennies).
    """
    wallet: IWallet
    inventory: dict[str, float]
    inventory_quality: dict[str, float]
    durable_assets: list[DurableAssetDTO]
    portfolio: Portfolio
    is_employed: bool
    employer_id: int | None
    current_wage_pennies: int
    wage_modifier: float
    labor_skill: float
    education_xp: float
    education_level: int
    owned_properties: list[int]
    residing_property_id: int | None
    is_homeless: bool
    home_quality_score: float
    housing_target_mode: str
    housing_price_history: deque
    market_wage_history: deque
    shadow_reservation_wage_pennies: int
    last_labor_offer_tick: int
    last_fired_tick: int
    job_search_patience: int
    employment_start_tick: int
    current_consumption: float
    current_food_consumption: float
    expected_inflation: dict[str, float]
    perceived_avg_prices: dict[str, float]
    price_history: defaultdict[str, deque]
    price_memory_length: int
    adaptation_rate: float
    labor_income_this_tick_pennies: int
    capital_income_this_tick_pennies: int
    consumption_expenditure_this_tick_pennies: int
    food_expenditure_this_tick_pennies: int
    market_insight: float = ...
    expected_wage_pennies: int = ...
    talent: Talent = field(default_factory=Incomplete)
    skills: dict[str, Skill] = field(default_factory=dict)
    aptitude: float = ...
    major: IndustryDomain | None = ...
    hidden_talent: dict[IndustryDomain, float] = field(default_factory=dict)
    experience: dict[IndustryDomain, float] = field(default_factory=dict)
    sunk_cost_pennies: int = ...
    credit_frozen_until_tick: int = ...
    initial_assets_record_pennies: int = ...
    @property
    def assets(self) -> dict[CurrencyCode, int]:
        """Legacy compatibility accessor."""
    def copy(self) -> EconStateDTO: ...

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
    brand_loyalty: dict[int, float]
    last_purchase_memory: dict[str, int]
    patience: float
    optimism: float
    ambition: float
    last_leisure_type: str
    desire_weights: dict[str, float] = field(default_factory=dict)
    demand_elasticity: float = ...
    economic_vision: float = ...
    trust_score: float = ...
    def copy(self) -> SocialStateDTO: ...

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
    market_insight: float = ...
    monthly_income_pennies: int = ...
    monthly_debt_payments_pennies: int = ...
    major: IndustryDomain | None = ...

@dataclass
class HouseholdStateDTO:
    """
    [DEPRECATED] Use HouseholdSnapshotDTO instead.
    A read-only DTO containing the state of a Household agent.
    Used by the DecisionEngine to make decisions without direct dependency on the Household class.
    MIGRATION: Monetary values are integers (pennies).
    """
    id: int
    assets: dict[CurrencyCode, int]
    inventory: dict[str, float]
    needs: dict[str, float]
    preference_asset: float
    preference_social: float
    preference_growth: float
    personality: Personality
    durable_assets: list[dict[str, Any]]
    expected_inflation: dict[str, float]
    is_employed: bool
    current_wage_pennies: int
    wage_modifier: float
    is_homeless: bool
    residing_property_id: int | None
    owned_properties: list[int]
    portfolio_holdings: dict[int, Share]
    risk_aversion: float
    agent_data: dict[str, Any]
    market_insight: float = ...
    major: IndustryDomain | None = ...
    perceived_prices: dict[str, float] = field(default_factory=dict)
    conformity: float = ...
    social_rank: float = ...
    approval_rating: int = ...
    optimism: float = ...
    ambition: float = ...
    perceived_fair_price: dict[str, float] = field(default_factory=dict)
    sentiment_index: float = ...
    demand_elasticity: float = ...
    monthly_income_pennies: int = ...
    monthly_debt_payments_pennies: int = ...

@dataclass
class CloningRequestDTO:
    """Data required to clone a household."""
    new_id: int
    initial_assets_from_parent: dict[CurrencyCode, int]
    current_tick: int

@dataclass
class EconContextDTO:
    """Context for economic operations."""
    markets: dict[str, 'IMarket']
    market_data: dict[str, Any]
    current_time: int

@dataclass
class SocialContextDTO:
    """Context for social operations."""
    current_time: int
    market_data: dict[str, Any] | None = ...

@dataclass
class LifecycleDTO:
    """State data required for lifecycle updates."""
    is_employed: bool

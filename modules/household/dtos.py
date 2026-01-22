from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, TYPE_CHECKING

from simulation.ai.api import Personality
from simulation.models import Share

if TYPE_CHECKING:
    from simulation.core_markets import Market

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

    # WO-108: Parity Fields
    perceived_fair_price: Dict[str, float] = field(default_factory=dict)
    sentiment_index: float = 0.5

@dataclass
class CloningRequestDTO:
    """Data required to clone a household."""
    new_id: int
    initial_assets_from_parent: float
    current_tick: int

@dataclass
class EconContextDTO:
    """Context for economic operations."""
    markets: Dict[str, "Market"]
    market_data: Dict[str, Any]
    current_time: int

@dataclass
class SocialContextDTO:
    """Context for social operations."""
    current_time: int
    market_data: Optional[Dict[str, Any]] = None

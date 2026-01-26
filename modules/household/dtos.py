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
    optimism: float = 0.5
    ambition: float = 0.5

    # WO-108: Parity Fields
    perceived_fair_price: Dict[str, float] = field(default_factory=dict)
    sentiment_index: float = 0.5

    @classmethod
    def from_household(cls, household: Any) -> "HouseholdStateDTO":
        """
        Creates a HouseholdStateDTO from a Household-like object (Household instance or Mock).
        """
        # Safely extract attributes with defaults

        # Helper for portfolio
        portfolio_holdings = {}
        if hasattr(household, 'portfolio'):
             # If portfolio is an object, access holdings. If dict, use it.
             # Assuming Portfolio object with .holdings (dict of id -> Share)
             if hasattr(household.portfolio, 'holdings'):
                 portfolio_holdings = household.portfolio.holdings
             elif isinstance(household.portfolio, dict):
                 portfolio_holdings = household.portfolio # Legacy/Mock support

        # Helper for perceived_prices
        perceived_prices = {}
        if hasattr(household, 'perceived_avg_prices'):
             perceived_prices = household.perceived_avg_prices.copy()

        # Helper for properties
        owned_properties = getattr(household, 'owned_properties', [])

        # Helper for agent_data
        agent_data = {}
        if hasattr(household, 'get_agent_data'):
             agent_data = household.get_agent_data()

        # DTO Construction
        return cls(
            id=household.id,
            assets=household.assets,
            inventory=household.inventory.copy(),
            needs=household.needs.copy(),
            preference_asset=getattr(household, 'preference_asset', 0.5),
            preference_social=getattr(household, 'preference_social', 0.5),
            preference_growth=getattr(household, 'preference_growth', 0.5),
            personality=household.personality,
            durable_assets=getattr(household, 'durable_assets', []).copy() if hasattr(household, 'durable_assets') else [],
            expected_inflation=getattr(household, 'expected_inflation', {}).copy(),
            is_employed=household.is_employed,
            current_wage=household.current_wage,
            wage_modifier=getattr(household, 'wage_modifier', 1.0),
            is_homeless=getattr(household, 'is_homeless', False),
            residing_property_id=getattr(household, 'residing_property_id', None),
            owned_properties=owned_properties,
            portfolio_holdings=portfolio_holdings,
            risk_aversion=getattr(household, 'risk_aversion', 1.0),
            agent_data=agent_data,
            perceived_prices=perceived_prices,
            conformity=getattr(household, 'conformity', 0.5),
            social_rank=getattr(household, 'social_rank', 0.5),
            approval_rating=getattr(household, 'approval_rating', 1),
            optimism=getattr(household, 'optimism', 0.5),
            ambition=getattr(household, 'ambition', 0.5),
            perceived_fair_price=getattr(household, 'perceived_fair_price', {}).copy(),
            sentiment_index=getattr(household, 'sentiment_index', 0.5)
        )

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

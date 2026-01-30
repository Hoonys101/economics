
from typing import Dict, Any, Optional
from simulation.ai.enums import Personality
from modules.household.dtos import HouseholdStateDTO
from simulation.dtos.firm_state_dto import FirmStateDTO

def create_household_dto(
    id: int = 1,
    assets: float = 1000.0,
    inventory: Optional[Dict[str, float]] = None,
    needs: Optional[Dict[str, float]] = None,
    is_employed: bool = False,
    current_wage: float = 0.0,
    wage_modifier: float = 1.0,
    durable_assets: Optional[list] = None,
    perceived_prices: Optional[Dict[str, float]] = None,
    agent_data: Optional[Dict[str, Any]] = None,
    personality: Personality = Personality.BALANCED,
    **kwargs
) -> HouseholdStateDTO:
    """Factory for HouseholdStateDTO with sensible defaults."""
    return HouseholdStateDTO(
        id=id,
        assets=assets,
        inventory=inventory or {},
        needs=needs or {"survival": 0.5, "leisure": 0.5},
        preference_asset=kwargs.get("preference_asset", 1.0),
        preference_social=kwargs.get("preference_social", 1.0),
        preference_growth=kwargs.get("preference_growth", 1.0),
        personality=personality,
        durable_assets=durable_assets or [],
        expected_inflation=kwargs.get("expected_inflation", {}),
        is_employed=is_employed,
        current_wage=current_wage,
        wage_modifier=wage_modifier,
        is_homeless=kwargs.get("is_homeless", False),
        residing_property_id=kwargs.get("residing_property_id"),
        owned_properties=kwargs.get("owned_properties", []),
        portfolio_holdings=kwargs.get("portfolio_holdings", {}),
        risk_aversion=kwargs.get("risk_aversion", 1.0),
        agent_data=agent_data or {},
        perceived_prices=perceived_prices or {},
        conformity=kwargs.get("conformity", 0.5),
        social_rank=kwargs.get("social_rank", 0.5),
        approval_rating=kwargs.get("approval_rating", 1)
    )

def create_firm_dto(
    id: int = 100,
    assets: float = 10000.0,
    is_active: bool = True,
    inventory: Optional[Dict[str, float]] = None,
    current_production: float = 0.0,
    productivity_factor: float = 1.0,
    production_target: float = 100.0,
    capital_stock: float = 100.0,
    employees: Optional[list] = None,
    price_history: Optional[Dict[str, float]] = None,
    **kwargs
) -> FirmStateDTO:
    """Factory for FirmStateDTO with sensible defaults."""
    return FirmStateDTO(
        id=id,
        assets=assets,
        is_active=is_active,
        inventory=inventory or {},
        inventory_quality=kwargs.get("inventory_quality", {}),
        input_inventory=kwargs.get("input_inventory", {}),
        current_production=current_production,
        productivity_factor=productivity_factor,
        production_target=production_target,
        capital_stock=capital_stock,
        base_quality=kwargs.get("base_quality", 1.0),
        automation_level=kwargs.get("automation_level", 0.0),
        specialization=kwargs.get("specialization", "food"),
        total_shares=kwargs.get("total_shares", 100.0),
        treasury_shares=kwargs.get("treasury_shares", 0.0),
        dividend_rate=kwargs.get("dividend_rate", 0.1),
        is_publicly_traded=kwargs.get("is_publicly_traded", True),
        valuation=kwargs.get("valuation", 1000.0),
        revenue_this_turn=kwargs.get("revenue_this_turn", 0.0),
        expenses_this_tick=kwargs.get("expenses_this_tick", 0.0),
        consecutive_loss_turns=kwargs.get("consecutive_loss_turns", 0),
        altman_z_score=kwargs.get("altman_z_score", 3.0),
        price_history=price_history or {},
        profit_history=kwargs.get("profit_history", []),
        brand_awareness=kwargs.get("brand_awareness", 0.0),
        perceived_quality=kwargs.get("perceived_quality", 1.0),
        marketing_budget=kwargs.get("marketing_budget", 0.0),
        employees=employees or [],
        employees_data=kwargs.get("employees_data", {}),
        agent_data=kwargs.get("agent_data", {}),
        system2_guidance=kwargs.get("system2_guidance", {})
    )

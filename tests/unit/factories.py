from typing import Dict, Any, Optional
from simulation.ai.enums import Personality
from modules.household.dtos import HouseholdStateDTO
from simulation.dtos.firm_state_dto import FirmStateDTO
from tests.unit.mocks.mock_factory import MockFactory

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
    return MockFactory.create_household_state_dto(
        id=id,
        assets=assets,
        inventory=inventory,
        needs=needs,
        is_employed=is_employed,
        current_wage=current_wage,
        wage_modifier=wage_modifier,
        durable_assets=durable_assets,
        perceived_prices=perceived_prices,
        agent_data=agent_data,
        personality=personality,
        **kwargs
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
    return MockFactory.create_firm_state_dto(
        id=id,
        is_active=is_active,
        balance=assets, # Map 'assets' (flat) to 'balance' (finance dto)
        inventory=inventory,
        current_production=current_production,
        productivity_factor=productivity_factor,
        production_target=production_target,
        capital_stock=capital_stock,
        employees=employees,
        price_history=price_history,
        **kwargs
    )

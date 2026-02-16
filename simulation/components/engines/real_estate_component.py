from typing import List, Dict, Any, Optional, Tuple
from modules.simulation.dtos.api import FirmConfigDTO

class RealEstateUtilizationComponent:
    """
    TD-271: Converts firm-owned real estate into a production bonus.
    Applies production cost reduction based on owned space and market conditions.
    """
    def apply(self, owned_properties: List[int], config: FirmConfigDTO, firm_id: int, current_tick: int, market_data: Optional[Dict[str, Any]] = None) -> Tuple[Optional[Dict[str, Any]], int]:
        # 1. Calculate Owned Space
        # Assuming 1 property = 1 unit of space for now (or configurable)
        owned_space = len(owned_properties)
        if owned_space <= 0:
            return None, 0

        # space_utility_factor: How much cost reduction per unit of space?
        # Ideally from config. Assuming default 100.0 if not in config.
        space_utility_factor = getattr(config, "space_utility_factor", 100.0)

        # regional_rent_index: From market data or default 1.0
        regional_rent_index = 1.0
        # Placeholder for market data integration

        # 3. Calculate Cost Reduction (Bonus)
        # Formula: owned_space * space_utility_factor * regional_rent_index
        cost_reduction = owned_space * space_utility_factor * regional_rent_index

        # 4. Apply Bonus
        # Effectively reduces net cost by increasing revenue/profit internally
        if cost_reduction > 0:
             # Assuming pre-scaled or handled elsewhere. For now just int cast.
             amount_pennies = int(cost_reduction)

             effect = {
                 "type": "PRODUCTION_COST_REDUCTION",
                 "agent_id": firm_id,
                 "amount": amount_pennies,
                 "tick": current_tick,
                 "details": {
                     "owned_space": owned_space,
                     "utility_factor": space_utility_factor
                 }
             }
             return effect, amount_pennies
        return None, 0

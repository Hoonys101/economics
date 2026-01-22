from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from simulation.ai.enums import Personality

@dataclass
class FirmStateDTO:
    """
    A read-only DTO containing the state of a Firm agent.
    Used by DecisionEngines to prevent direct access to the Firm instance.
    """
    id: int
    assets: float
    is_active: bool
    specialization: str
    inventory: Dict[str, float]
    needs: Dict[str, float]
    current_production: float
    production_target: float
    productivity_factor: float
    employee_count: int
    employees: List[int]
    employee_wages: Dict[int, float]
    profit_history: List[float]
    last_prices: Dict[str, float]
    inventory_quality: Dict[str, float]
    input_inventory: Dict[str, float]

    # Financials
    last_revenue: float
    last_sales_volume: float
    revenue_this_turn: float
    expenses_this_tick: float
    consecutive_loss_turns: int
    total_shares: float
    treasury_shares: float
    dividend_rate: float
    capital_stock: float
    total_debt: float
    personality: Personality

    # Brand
    base_quality: float
    brand_awareness: float = 0.0
    perceived_quality: float = 0.0

    # Automation
    automation_level: float = 0.0

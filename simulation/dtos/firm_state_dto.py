from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

@dataclass
class FirmStateDTO:
    """
    A read-only DTO containing the state of a Firm agent.
    Used by DecisionEngines to make decisions without direct dependency on the Firm class.
    """
    id: int
    assets: float
    is_active: bool
    inventory: Dict[str, float]
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
    price_history: Dict[str, float] # last_prices
    profit_history: List[float]

    # Brand & Sales
    brand_awareness: float
    perceived_quality: float
    marketing_budget: float

    # HR
    employees: List[int] # List of employee IDs
    employees_data: Dict[int, Dict[str, Any]] # Detailed employee info

    # AI/Agent Data
    agent_data: Dict[str, Any]
    system2_guidance: Dict[str, Any]

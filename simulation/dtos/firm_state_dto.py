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

    @staticmethod
    def from_firm(firm: Any) -> "FirmStateDTO":
        """
        Creates a FirmStateDTO from a Firm-like object (Firm instance or Mock).
        Used to unify DTO creation logic across the simulation and test loaders.
        """
        # Handle FinanceDepartment delegation/structure
        finance = getattr(firm, "finance", None)
        hr = getattr(firm, "hr", None)
        brand_manager = getattr(firm, "brand_manager", None)

        # Helper to safely get nested attributes or defaults
        def safe_get(obj, attr, default):
            return getattr(obj, attr, default)

        # Handle profit history: might be deque or list
        profit_history = list(safe_get(finance, "profit_history", [])) if finance else []

        # Handle employees: might be list of Household objects (Firm) or already IDs (Mock/JSON)
        # Note: Firm.hr.employees is List[Household]. DTO expects List[int].
        # If input is from JSON (GoldenLoader), it might be missing or different.
        employees = []
        if hr:
             raw_employees = safe_get(hr, "employees", [])
             # Check if it's a list of objects with 'id' or just IDs
             if raw_employees and hasattr(raw_employees[0], "id"):
                 employees = [e.id for e in raw_employees]
             else:
                 employees = [] # Fallback or already empty

        # Agent Data
        agent_data = {}
        if hasattr(firm, "get_agent_data"):
            agent_data = firm.get_agent_data()

        return FirmStateDTO(
            id=safe_get(firm, "id", 0),
            assets=safe_get(firm, "assets", 0.0),
            is_active=safe_get(firm, "is_active", True),
            inventory=safe_get(firm, "inventory", {}).copy(),
            inventory_quality=safe_get(firm, "inventory_quality", {}).copy(),
            input_inventory=safe_get(firm, "input_inventory", {}).copy(),
            current_production=safe_get(firm, "current_production", 0.0),
            productivity_factor=safe_get(firm, "productivity_factor", 1.0),
            production_target=safe_get(firm, "production_target", 0.0),
            capital_stock=safe_get(firm, "capital_stock", 0.0),
            base_quality=safe_get(firm, "base_quality", 1.0),
            automation_level=safe_get(firm, "automation_level", 0.0),
            specialization=safe_get(firm, "specialization", "food"),
            total_shares=safe_get(firm, "total_shares", 1000.0),
            treasury_shares=safe_get(firm, "treasury_shares", 0.0),
            dividend_rate=safe_get(firm, "dividend_rate", 0.0),
            is_publicly_traded=safe_get(firm, "is_publicly_traded", True),
            valuation=safe_get(firm, "valuation", 0.0),
            revenue_this_turn=safe_get(firm, "revenue_this_turn", 0.0),
            expenses_this_tick=safe_get(firm, "expenses_this_tick", 0.0),
            consecutive_loss_turns=safe_get(finance, "consecutive_loss_turns", 0) if finance else 0,
            altman_z_score=finance.calculate_altman_z_score() if finance and hasattr(finance, "calculate_altman_z_score") else 0.0,
            price_history=safe_get(firm, "last_prices", {}).copy(),
            profit_history=profit_history,
            brand_awareness=safe_get(brand_manager, "brand_awareness", 0.0) if brand_manager else 0.0,
            perceived_quality=safe_get(brand_manager, "perceived_quality", 0.0) if brand_manager else 0.0,
            marketing_budget=safe_get(firm, "marketing_budget", 0.0),
            employees=employees,
            employees_data={},
            agent_data=agent_data,
            system2_guidance={}
        )

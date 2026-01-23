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

    # WO-108: Parity Fields
    sentiment_index: float = 0.5

    @classmethod
    def from_firm(cls, firm: Any) -> "FirmStateDTO":
        """
        Creates a FirmStateDTO from a Firm-like object (Firm instance or Mock).
        """
        # Extract employee IDs safely
        employee_ids = []
        employees_data = {}
        if hasattr(firm, 'hr') and hasattr(firm.hr, 'employees'):
            employee_ids = [e.id for e in firm.hr.employees]

            # Populate employees_data for CorporateManager
            wages_map = getattr(firm.hr, 'employee_wages', {})
            for e in firm.hr.employees:
                employees_data[e.id] = {
                    "id": e.id,
                    "wage": wages_map.get(e.id, 0.0),
                    "skill": getattr(e, 'labor_skill', 1.0),
                    "age": getattr(e, 'age', 0),
                    "education_level": getattr(e, 'education_level', 0)
                }

        # Extract financial data safely (using properties or direct access)
        finance = getattr(firm, 'finance', None)
        revenue = firm.revenue_this_turn if finance else 0.0
        expenses = firm.expenses_this_tick if finance else 0.0

        profit_history = []
        if finance and hasattr(finance, 'profit_history'):
             profit_history = list(finance.profit_history)

        consecutive_loss_turns = firm.consecutive_loss_turns if hasattr(firm, 'consecutive_loss_turns') else 0
        if finance and hasattr(finance, 'consecutive_loss_turns'):
             consecutive_loss_turns = finance.consecutive_loss_turns

        altman_z = 0.0
        if finance and hasattr(finance, 'get_altman_z_score'):
            altman_z = finance.get_altman_z_score()
        elif hasattr(firm, 'altman_z_score'):
            altman_z = firm.altman_z_score

        # Determine sentiment_index
        # Logic: 1.0 if profitable/active, 0.0 if failing.
        # Refined: (1.0 / (1 + consecutive_loss_turns))
        sentiment = 1.0 / (1.0 + consecutive_loss_turns)

        return cls(
            id=firm.id,
            assets=firm.assets,
            is_active=firm.is_active,
            inventory=firm.inventory.copy(),
            inventory_quality=firm.inventory_quality.copy(),
            input_inventory=firm.input_inventory.copy() if hasattr(firm, 'input_inventory') else {},
            current_production=firm.current_production,
            productivity_factor=firm.productivity_factor,
            production_target=firm.production_target,
            capital_stock=firm.capital_stock,
            base_quality=firm.base_quality,
            automation_level=firm.automation_level,
            specialization=firm.specialization,
            total_shares=firm.total_shares,
            treasury_shares=firm.treasury_shares,
            dividend_rate=firm.dividend_rate,
            is_publicly_traded=firm.is_publicly_traded,
            valuation=firm.valuation,
            revenue_this_turn=revenue,
            expenses_this_tick=expenses,
            consecutive_loss_turns=consecutive_loss_turns,
            altman_z_score=altman_z,
            price_history=firm.last_prices.copy(),
            profit_history=profit_history,
            brand_awareness=firm.brand_manager.brand_awareness,
            perceived_quality=firm.brand_manager.perceived_quality,
            marketing_budget=firm.marketing_budget,
            employees=employee_ids,
            employees_data=employees_data,
            agent_data=firm.get_agent_data(),
            system2_guidance={}, # Placeholder
            sentiment_index=sentiment
        )

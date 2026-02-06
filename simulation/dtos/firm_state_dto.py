from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from .department_dtos import FinanceStateDTO, ProductionStateDTO, SalesStateDTO, HRStateDTO

@dataclass
class FirmStateDTO:
    """
    A read-only DTO containing the state of a Firm agent.
    Used by DecisionEngines to make decisions without direct dependency on the Firm class.
    Refactored to Composite State (TD-073).
    """
    id: int
    is_active: bool

    # Department Composite States
    finance: FinanceStateDTO
    production: ProductionStateDTO
    sales: SalesStateDTO
    hr: HRStateDTO

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
        # --- HR State ---
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

        hr_dto = HRStateDTO(
            employees=employee_ids,
            employees_data=employees_data
        )

        # --- Finance State ---
        finance = getattr(firm, 'finance', None)
        # Handle access via old properties if they exist (during refactor transition) or direct finance access
        # Since we are removing properties, we should look at finance component directly if possible.
        # However, for mocks or tests that might not have finance fully setup, we need care.
        # But 'firm' here is likely the actual Firm object which has 'finance'.

        balance = 0.0
        if finance and hasattr(finance, 'balance'):
            balance = finance.balance
        elif hasattr(firm, 'assets'): # Fallback (e.g. BaseAgent or Mock)
             balance = firm.assets

        revenue = 0.0
        if finance and hasattr(finance, 'revenue_this_turn'):
            revenue = finance.revenue_this_turn
        elif hasattr(firm, 'revenue_this_turn'):
            revenue = firm.revenue_this_turn

        expenses = 0.0
        if finance and hasattr(finance, 'expenses_this_tick'):
            expenses = finance.expenses_this_tick
        elif hasattr(firm, 'expenses_this_tick'):
            expenses = firm.expenses_this_tick

        profit_history = []
        if finance and hasattr(finance, 'profit_history'):
             profit_history = list(finance.profit_history)
        elif hasattr(firm, 'profit_history'): # Fallback
             profit_history = firm.profit_history

        consecutive_loss_turns = 0
        if finance and hasattr(finance, 'consecutive_loss_turns'):
             consecutive_loss_turns = finance.consecutive_loss_turns
        elif hasattr(firm, 'consecutive_loss_turns'):
             consecutive_loss_turns = firm.consecutive_loss_turns

        altman_z = 0.0
        if finance and hasattr(finance, 'get_altman_z_score'):
            altman_z = finance.get_altman_z_score()
        elif hasattr(firm, 'altman_z_score'):
            altman_z = firm.altman_z_score

        finance_dto = FinanceStateDTO(
            balance=balance,
            revenue_this_turn=revenue,
            expenses_this_tick=expenses,
            consecutive_loss_turns=consecutive_loss_turns,
            profit_history=profit_history,
            altman_z_score=altman_z,
            valuation=getattr(firm, 'valuation', 0.0),
            total_shares=getattr(firm, 'total_shares', 0.0),
            treasury_shares=getattr(firm, 'treasury_shares', 0.0),
            dividend_rate=getattr(firm, 'dividend_rate', 0.0),
            is_publicly_traded=getattr(firm, 'is_publicly_traded', True)
        )

        # --- Production State ---
        # Robust inventory retrieval
        inventory = {}
        if hasattr(firm, 'get_all_items'):
             inventory = firm.get_all_items()
        elif hasattr(firm, '_inventory'):
             inventory = firm._inventory.copy()
        else:
             inventory = getattr(firm, 'inventory', {}).copy()

        production_dto = ProductionStateDTO(
            current_production=getattr(firm, 'current_production', 0.0),
            productivity_factor=getattr(firm, 'productivity_factor', 1.0),
            production_target=getattr(firm, 'production_target', 0.0),
            capital_stock=getattr(firm, 'capital_stock', 0.0),
            base_quality=getattr(firm, 'base_quality', 1.0),
            automation_level=getattr(firm, 'automation_level', 0.0),
            specialization=getattr(firm, 'specialization', "GENERIC"),
            inventory=inventory,
            input_inventory=getattr(firm, 'input_inventory', {}).copy(),
            inventory_quality=getattr(firm, 'inventory_quality', {}).copy()
        )

        # --- Sales State ---
        brand_awareness = 0.0
        perceived_quality = 0.0
        if hasattr(firm, 'brand_manager'):
            brand_awareness = firm.brand_manager.brand_awareness
            perceived_quality = firm.brand_manager.perceived_quality

        sales_dto = SalesStateDTO(
            inventory_last_sale_tick=getattr(firm, 'inventory_last_sale_tick', {}).copy(),
            price_history=getattr(firm, 'last_prices', {}).copy(),
            brand_awareness=brand_awareness,
            perceived_quality=perceived_quality,
            marketing_budget=getattr(firm, 'marketing_budget', 0.0)
        )

        # Determine sentiment_index
        # Logic: 1.0 if profitable/active, 0.0 if failing.
        # Refined: (1.0 / (1 + consecutive_loss_turns))
        sentiment = 1.0 / (1.0 + consecutive_loss_turns)

        return cls(
            id=firm.id,
            is_active=firm.is_active,
            finance=finance_dto,
            production=production_dto,
            sales=sales_dto,
            hr=hr_dto,
            agent_data=firm.get_agent_data(),
            system2_guidance={}, # Placeholder
            sentiment_index=sentiment
        )

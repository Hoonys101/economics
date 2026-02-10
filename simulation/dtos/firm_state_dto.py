from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Protocol, runtime_checkable
from .department_dtos import FinanceStateDTO, ProductionStateDTO, SalesStateDTO, HRStateDTO
from modules.system.api import DEFAULT_CURRENCY

@runtime_checkable
class IFirmStateProvider(Protocol):
    """Protocol for entities that can provide their state as a FirmStateDTO."""
    def get_state_dto(self) -> "FirmStateDTO":
        ...

@dataclass(frozen=True)
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
        # Use Protocol if available (Preferred)
        if isinstance(firm, IFirmStateProvider):
            # To avoid infinite recursion if the provider calls from_firm (which it shouldn't anymore),
            # we assume the provider constructs the DTO directly.
            # However, if the provider is the Firm class itself using the OLD implementation:
            # def get_state_dto(self): return FirmStateDTO.from_firm(self)
            # then we have a loop.
            # But we are updating Firm class in the next step to NOT call from_firm.
            # So this is safe IF we update Firm class correctly.
            return firm.get_state_dto()

        # Fallback for Mocks/Legacy Objects
        # --- HR State ---
        employee_ids = []
        employees_data = {}

        # Check for new architecture (hr_state) first, then fallback to property (hr)
        hr_source = getattr(firm, 'hr_state', None)
        if hr_source is None:
            hr_source = getattr(firm, 'hr', None)

        if hr_source and hasattr(hr_source, 'employees'):
            employee_ids = [e.id for e in hr_source.employees]

            # Populate employees_data for CorporateManager
            wages_map = getattr(hr_source, 'employee_wages', {})
            for e in hr_source.employees:
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
        finance_source = getattr(firm, 'finance_state', None)
        if finance_source is None:
             finance_source = getattr(firm, 'finance', None)

        # Determine Balance (Wallet or Dict)
        balance = 0.0 # Default primary currency balance
        if hasattr(firm, 'wallet') and hasattr(firm.wallet, 'get_balance'):
             balance = firm.wallet.get_balance(DEFAULT_CURRENCY)
        elif finance_source and hasattr(finance_source, 'balance'):
             # If balance is dict
             b = finance_source.balance
             if isinstance(b, dict):
                 balance = b.get(DEFAULT_CURRENCY, 0.0)
             else:
                 balance = b
        elif hasattr(firm, 'assets'):
             balance = firm.assets

        revenue = 0.0
        # revenue_this_turn is Dict in new state, maybe float in old/mock?
        if finance_source and hasattr(finance_source, 'revenue_this_turn'):
            rev = finance_source.revenue_this_turn
            if isinstance(rev, dict):
                revenue = rev.get(DEFAULT_CURRENCY, 0.0)
            else:
                revenue = rev
        elif hasattr(firm, 'revenue_this_turn'):
             revenue = firm.revenue_this_turn

        expenses = 0.0
        if finance_source and hasattr(finance_source, 'expenses_this_tick'):
            exp = finance_source.expenses_this_tick
            if isinstance(exp, dict):
                expenses = exp.get(DEFAULT_CURRENCY, 0.0)
            else:
                expenses = exp
        elif hasattr(firm, 'expenses_this_tick'):
             expenses = firm.expenses_this_tick

        profit_history = []
        if finance_source and hasattr(finance_source, 'profit_history'):
             profit_history = list(finance_source.profit_history)
        elif hasattr(firm, 'profit_history'):
             profit_history = firm.profit_history

        consecutive_loss_turns = 0
        if finance_source and hasattr(finance_source, 'consecutive_loss_turns'):
             consecutive_loss_turns = finance_source.consecutive_loss_turns
        elif hasattr(firm, 'consecutive_loss_turns'):
             consecutive_loss_turns = firm.consecutive_loss_turns

        altman_z = 0.0
        # Check engine for calculation if available, or property
        if hasattr(firm, 'finance_engine') and hasattr(firm.finance_engine, 'calculate_altman_z_score'):
             # We skip complex calc in DTO creation to avoid side effects/dependencies
             pass
        elif hasattr(finance_source, 'get_altman_z_score'):
            altman_z = finance_source.get_altman_z_score()
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
        prod_source = getattr(firm, 'production_state', None)
        if prod_source is None:
             prod_source = getattr(firm, 'production', None)
             if prod_source is None: prod_source = firm # Fallback to firm if properties are on firm

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
        sales_source = getattr(firm, 'sales_state', None)
        if sales_source is None:
             sales_source = getattr(firm, 'sales', None)
             if sales_source is None: sales_source = firm

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

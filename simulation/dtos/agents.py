from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class AgentBasicDTO(BaseModel):
    id: int
    type: str  # "household" | "firm"
    wealth: int
    income: int
    expense: int

class AgentDetailDTO(AgentBasicDTO):
    # Common
    is_active: bool

    # Household specific
    age: Optional[float] = None
    needs: Optional[Dict[str, float]] = None
    inventory: Optional[Dict[str, float]] = None
    employer_id: Optional[int] = None
    current_wage: Optional[int] = None

    # Firm specific
    sector: Optional[str] = None
    employees_count: Optional[int] = None
    production: Optional[float] = None
    revenue_this_turn: Optional[Dict[str, int]] = None
    expenses_this_tick: Optional[Dict[str, int]] = None

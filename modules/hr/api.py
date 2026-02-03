from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from modules.common.dtos import Claim
    from simulation.firms import Firm

class IHRService(ABC):
    @abstractmethod
    def calculate_liquidation_employee_claims(self, firm: Firm, current_tick: int) -> List[Claim]:
        """Calculates all employee-related claims (wages, severance) for a firm in liquidation."""
        ...

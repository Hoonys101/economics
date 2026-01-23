from typing import Any
from modules.finance.api import IFiscalMonitor

class FiscalMonitor(IFiscalMonitor):
    """
    Component for analyzing government fiscal health.
    """
    def get_debt_to_gdp_ratio(self, government_dto: Any, world_dto: Any) -> float:
        """
        Calculates the debt-to-GDP ratio.

        Args:
            government_dto: Object containing debt information (expected 'total_debt').
            world_dto: Object containing GDP information (expected 'current_gdp' or 'total_production').

        Returns:
            float: The debt-to-GDP ratio. Returns 0.0 if GDP is invalid.
        """
        debt = getattr(government_dto, 'total_debt', 0.0)

        # GDP might be in various DTOs depending on context
        gdp = getattr(world_dto, 'current_gdp', 0.0)
        if gdp == 0.0:
            gdp = getattr(world_dto, 'total_production', 0.0)

        if gdp <= 0:
            return 0.0

        return debt / gdp

from modules.finance.api import IFiscalMonitor
from modules.simulation.api import EconomicIndicatorsDTO
from modules.government.api import IGovernment

class FiscalMonitor(IFiscalMonitor):
    """
    Component for analyzing government fiscal health.
    """
    def get_debt_to_gdp_ratio(self, government: IGovernment, indicators: EconomicIndicatorsDTO) -> float:
        """
        Calculates the debt-to-GDP ratio.

        Args:
            government: Object containing debt information (expected 'total_debt').
            indicators: Object containing GDP information.

        Returns:
            float: The debt-to-GDP ratio. Returns 0.0 if GDP is invalid.
        """
        # Convert debt (pennies) to dollars for ratio calculation against GDP (dollars)
        debt = government.total_debt / 100.0

        # GDP is strictly in EconomicIndicatorsDTO
        gdp = indicators.gdp

        if gdp <= 0:
            return 0.0

        return debt / gdp

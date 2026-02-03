from modules.finance.api import IFiscalMonitor
from modules.simulation.api import IGovernment, EconomicIndicatorsDTO

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
        debt = government.total_debt

        # GDP is strictly in EconomicIndicatorsDTO
        gdp = indicators.gdp

        if gdp <= 0:
            return 0.0

        return debt / gdp

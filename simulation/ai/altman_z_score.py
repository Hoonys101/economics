from simulation.dtos.financial_dtos import FinancialStatementDTO

class AltmanZScoreCalculator:
    """Calculates the Altman Z-Score based on a standardized financial snapshot."""

    def calculate(self, statement: FinancialStatementDTO) -> float:
        """
        Calculates the Z-Score using a modified formula for service companies.
        Z = 1.2*X1 + 1.4*X2 + 3.3*X3

        Where:
            X1 (Working Capital / Total Assets): Measures liquid assets in relation
               to the size of the company. A firm with significant working capital
               is less likely to face immediate financial distress.
            X2 (Retained Earnings / Total Assets): Measures cumulative profitability.
               A higher value indicates a history of reinvesting profits.
            X3 (Average Profit / Total Assets): Measures recent operational efficiency.
               Uses a moving average of profit to gauge how effectively the firm
               is generating earnings from its assets.

        Returns:
            The calculated Z-Score. A score below 1.81 typically indicates a firm
            is heading for bankruptcy, while a score above 3.0 suggests a healthy
            financial position.
        """
        if statement["total_assets"] == 0:
            return 0.0

        # X1: Working Capital / Total Assets
        x1 = statement["working_capital"] / statement["total_assets"]

        # X2: Retained Earnings / Total Assets
        x2 = statement["retained_earnings"] / statement["total_assets"]

        # X3: Average Profit / Total Assets
        x3 = statement["average_profit"] / statement["total_assets"]

        z_score = 1.2 * x1 + 1.4 * x2 + 3.3 * x3
        return z_score

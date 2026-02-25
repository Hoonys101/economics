from dataclasses import dataclass as dataclass

class AltmanZScoreCalculator:
    """
    Calculates the Altman Z-Score for a firm to assess its solvency and bankruptcy risk.

    This implementation uses a modified Z-Score formula often used for non-manufacturing
    or private companies, focusing on liquidity, cumulative profitability, and operational efficiency.
    """
    @staticmethod
    def calculate(total_assets: float, working_capital: float, retained_earnings: float, average_profit: float) -> float:
        """
        Calculates the Altman Z-Score.

        Formula:
            Z = 1.2 * X1 + 1.4 * X2 + 3.3 * X3

        Where:
            X1 = Working Capital / Total Assets
                 (Measures liquidity relative to size)
            X2 = Retained Earnings / Total Assets
                 (Measures cumulative profitability and leverage)
            X3 = Average Profit (EBIT) / Total Assets
                 (Measures operational efficiency)

        Args:
            total_assets (float): The sum of all assets (Cash + Capital + Inventory).
            working_capital (float): Current Assets - Current Liabilities.
            retained_earnings (float): The total earnings retained by the firm.
            average_profit (float): The average profit (EBIT) over a recent period.

        Returns:
            float: The calculated Z-Score.
                   Generally, Z > 3.0 is safe, 1.8 < Z < 3.0 is grey zone, Z < 1.8 is distress.
        """

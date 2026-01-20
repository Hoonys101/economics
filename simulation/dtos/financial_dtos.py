from typing import TypedDict

class FinancialStatementDTO(TypedDict):
    """
    Standardized data contract for financial analytics.
    Serves as the Single Source of Truth (SSOT) for solvency and valuation logic.
    """
    total_assets: float
    working_capital: float
    retained_earnings: float
    average_profit: float
    total_debt: float

from typing import TypedDict

class FinancialStatementDTO(TypedDict):
    """
    Standardized Data Transfer Object for passing financial state.
    Used for solvency calculations and financial reporting.
    """
    total_assets: float
    working_capital: float
    retained_earnings: float
    average_profit: float
    total_debt: float

from _typeshed import Incomplete
from modules.market.api import OrderDTO as OrderDTO
from simulation.ai.api import Personality as Personality
from simulation.decisions.household.api import AssetManagementContext as AssetManagementContext
from simulation.decisions.household.stock_trader import StockTrader as StockTrader
from simulation.decisions.portfolio_manager import PortfolioManager as PortfolioManager
from simulation.models import Order as Order
from typing import Any

class AssetManager:
    """
    Manages Financial Assets (Portfolio, Stock, Liquidity, Debt).
    Refactored from AIDrivenHouseholdDecisionEngine.
    """
    stock_trader: Incomplete
    def __init__(self) -> None: ...
    def decide_investments(self, context: AssetManagementContext) -> list[Order]: ...
    def get_savings_roi(self, household: Any, market_data: dict[str, Any], config: Any | None = None) -> float:
        """가계의 저축 ROI(미래 효용)를 계산합니다."""
    def get_debt_penalty(self, household: Any, market_data: dict[str, Any], config: Any) -> float: ...

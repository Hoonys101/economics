from _typeshed import Incomplete
from modules.firm.api import AssetManagementInputDTO as AssetManagementInputDTO, AssetManagementResultDTO as AssetManagementResultDTO, RDInputDTO as RDInputDTO, RDResultDTO as RDResultDTO
from modules.system.api import CurrencyCode as CurrencyCode, DEFAULT_CURRENCY as DEFAULT_CURRENCY, MarketContextDTO as MarketContextDTO
from simulation.agents.government import Government as Government
from simulation.components.engines.asset_management_engine import AssetManagementEngine as AssetManagementEngine
from simulation.components.engines.rd_engine import RDEngine as RDEngine
from simulation.dtos import FiscalContext as FiscalContext
from simulation.firms import Firm as Firm
from simulation.models import Order as Order

logger: Incomplete

class FirmActionExecutor:
    """
    Executes internal orders for a Firm.
    Delegates to stateless engines and updates firm state.
    """
    def execute(self, firm: Firm, orders: list[Order], fiscal_context: FiscalContext, current_time: int, market_context: MarketContextDTO | None = None) -> None:
        """
        Orchestrates internal orders by delegating to specialized engines.
        Moved from Firm.execute_internal_orders.
        """

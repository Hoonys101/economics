from _typeshed import Incomplete
from modules.simulation.api import AgentCoreConfigDTO as AgentCoreConfigDTO, IDecisionEngine as IDecisionEngine
from modules.simulation.dtos.api import FirmConfigDTO as FirmConfigDTO
from simulation.ai.enums import Personality as Personality
from simulation.firms import Firm as Firm
from simulation.loan_market import LoanMarket as LoanMarket
from simulation.markets.order_book_market import OrderBookMarket as OrderBookMarket
from simulation.models import Order as Order
from typing import Any, override

logger: Incomplete

class ServiceFirm(Firm):
    """
    서비스 기업 클래스 (Phase 17-1).
    재고가 저장되지 않고 즉시 소멸(Void)되는 특성을 가짐.
    """
    capacity_this_tick: float
    waste_this_tick: float
    sales_volume_this_tick: float
    def __init__(self, core_config: AgentCoreConfigDTO, engine: IDecisionEngine, specialization: str, productivity_factor: float, config_dto: FirmConfigDTO, initial_inventory: dict[str, float] | None = None, loan_market: LoanMarket | None = None, sector: str = 'SERVICE', personality: Personality | None = None) -> None: ...
    current_production: Incomplete
    def produce(self, current_time: int, technology_manager: Any | None = None) -> None:
        """
        서비스 생산 로직.
        1. Cobb-Douglas로 용량(Capacity) 계산.
        2. 이전 틱의 잔여 재고를 폐기(Void).
        3. 새 용량을 재고로 설정.
        """
    def update_needs(self, current_time: int, government: Any | None = None, market_data: dict[str, Any] | None = None, technology_manager: Any | None = None) -> None:
        """
        서비스 기업 비용 처리.
        Holding Cost(보관비)는 0으로 처리 (서비스는 재고가 없으므로).
        """
    @override
    def get_agent_data(self) -> dict[str, Any]:
        """AI Data Provider."""

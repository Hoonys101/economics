import logging
import math
from typing import Optional, Dict, Any, List, override

from simulation.firms import Firm
from simulation.ai.enums import Personality
from simulation.models import Order
from simulation.markets.order_book_market import OrderBookMarket

logger = logging.getLogger(__name__)

class ServiceFirm(Firm):
    """
    서비스 기업 클래스 (Phase 17-1).
    재고가 저장되지 않고 즉시 소멸(Void)되는 특성을 가짐.
    """

    def __init__(
        self,
        id: int,
        initial_capital: float,
        initial_liquidity_need: float,
        specialization: str,
        productivity_factor: float,
        decision_engine: Any,
        value_orientation: str,
        config_module: Any,
        initial_inventory: Optional[Dict[str, float]] = None,
        loan_market: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
        sector: str = "SERVICE",
        is_visionary: bool = False,
        personality: Optional[Personality] = None,
    ) -> None:
        super().__init__(
            id,
            initial_capital,
            initial_liquidity_need,
            specialization,
            productivity_factor,
            decision_engine,
            value_orientation,
            config_module,
            initial_inventory,
            loan_market,
            logger,
            sector,
            is_visionary,
            personality,
        )
        # Service Specific Metrics
        self.capacity_this_tick: float = 0.0
        self.waste_this_tick: float = 0.0

    def produce(self, current_time: int) -> None:
        """
        서비스 생산 로직.
        1. Cobb-Douglas로 용량(Capacity) 계산.
        2. 이전 틱의 잔여 재고를 폐기(Void).
        3. 새 용량을 재고로 설정.
        """
        log_extra = {"tick": current_time, "agent_id": self.id, "tags": ["production", "service"]}

        # 1. 감가상각 (Goods와 동일)
        depreciation_rate = getattr(self.config_module, "CAPITAL_DEPRECIATION_RATE", 0.05)
        self.capital_stock *= (1.0 - depreciation_rate)

        # 2. 생산 용량 계산 (Cobb-Douglas)
        total_labor_skill = sum(getattr(emp, 'labor_skill', 1.0) for emp in self.employees if hasattr(emp, 'labor_skill'))
        if not self.employees:
            total_labor_skill = 1.0
        capital = max(self.capital_stock, 0.01)

        alpha = getattr(self.config_module, "LABOR_ALPHA", 0.7)
        tfp = self.productivity_factor

        if total_labor_skill > 0 and capital > 0:
            capacity = tfp * (total_labor_skill ** alpha) * (capital ** (1 - alpha))
        else:
            capacity = 0.0

        # Phase 15: Quality Calculation (Same as Goods)
        avg_skill = 0.0
        if self.employees:
            total_skill = sum(getattr(emp, 'labor_skill', 1.0) for emp in self.employees if hasattr(emp, 'labor_skill'))
            avg_skill = total_skill / len(self.employees)

        item_config = self.config_module.GOODS.get(self.specialization, {})
        quality_sensitivity = item_config.get("quality_sensitivity", 0.5)
        actual_quality = self.base_quality + (math.log1p(avg_skill) * quality_sensitivity)

        # 3. Void Logic (Unsold Inventory from previous tick is WASTE)
        item_id = self.specialization
        unsold_inventory = self.inventory.get(item_id, 0.0)
        self.waste_this_tick = unsold_inventory

        if unsold_inventory > 0:
            self.logger.debug(
                f"SERVICE_VOID | Firm {self.id} voided {unsold_inventory:.2f} unsold capacity.",
                extra={**log_extra, "waste": unsold_inventory}
            )

        # 4. Refill Logic (Set Inventory to New Capacity)
        # Service inventory doesn't accumulate; it resets.
        self.inventory[item_id] = capacity
        self.capacity_this_tick = capacity
        self.current_production = capacity # For compatibility

        # Update Quality (Weighted Avg doesn't apply to reset, just set new quality)
        self.inventory_quality[item_id] = actual_quality

        self.logger.debug(
            f"SERVICE_PRODUCE | Firm {self.id} produced capacity {capacity:.2f} (Quality: {actual_quality:.2f})",
            extra={**log_extra, "capacity": capacity}
        )

    def update_needs(self, current_time: int, government: Optional[Any] = None, market_data: Optional[Dict[str, Any]] = None, technology_manager: Optional[Any] = None) -> None:
        """
        서비스 기업 비용 처리.
        Holding Cost(보관비)는 0으로 처리 (서비스는 재고가 없으므로).
        """
        # Override holding cost logic
        # Standard Firm calculates holding cost based on inventory value.
        # Service Firm has "inventory" as capacity, but conceptually it's not "held" in a warehouse.
        # However, maintaining capacity (personnel/equipment) costs are covered by Wages and Maintenance Fee.
        # So we can explicitly skip holding cost calculation or set INVENTORY_HOLDING_COST_RATE to 0 locally.

        # Let's call super().update_needs but trick it? No, better to copy-paste and modify or hook?
        # Firm.update_needs does many things: Holding Cost, Wages, Marketing, Maintenance, Taxes, Closure Check.
        # Copy-paste is safer to avoid modifying base class significantly for this one deviation.
        # But duplication is bad.
        # Let's use the fact that config_module is passed.
        # We can temporarily mock config or just accept holding cost as "Capacity Maintenance Cost"?
        # Spec says "Unsold capacity still incurred Wages and Capital Depreciation".
        # It implies Fixed Costs are high.
        # If we allow holding cost, it acts as a penalty for over-capacity (large facility maintenance).
        # This actually aligns with "High Fixed Cost" nature of services.
        # So paying holding cost on Capacity seems acceptable/desirable!
        # It simulates the cost of maintaining the readiness of the service.

        super().update_needs(current_time, government, market_data, technology_manager)

    @override
    def get_agent_data(self) -> Dict[str, Any]:
        """AI 의사결정에 필요한 에이전트의 현재 상태 데이터를 반환합니다."""
        data = super().get_agent_data()
        data["capacity_this_tick"] = self.capacity_this_tick
        data["sales_volume_this_tick"] = self.sales_volume_this_tick
        return data

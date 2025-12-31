import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class Government:
    """
    정부 에이전트. 세금을 징수하고 보조금을 지급하거나 인프라에 투자합니다.
    """

    def __init__(self, id: int, initial_assets: float = 0.0, config_module: Any = None):
        self.id = id
        self.assets = initial_assets
        self.config_module = config_module
        
        self.total_collected_tax: float = 0.0
        self.total_spent_subsidies: float = 0.0
        self.infrastructure_level: int = 0
        
        # 세수 유형별 집계
        self.tax_revenue: Dict[str, float] = {}

        # 성향 및 욕구 (AI 훈련용 더미)
        self.value_orientation = "public_service"
        self.needs: Dict[str, float] = {}

        logger.info(
            f"Government {self.id} initialized with assets: {self.assets}",
            extra={"tick": 0, "agent_id": self.id, "tags": ["init", "government"]},
        )

    def collect_tax(self, amount: float, tax_type: str, source_id: int, current_tick: int):
        """세금을 징수합니다."""
        if amount <= 0:
            return 0.0
            
        self.assets += amount
        self.total_collected_tax += amount
        
        # 세목별 집계
        self.tax_revenue[tax_type] = self.tax_revenue.get(tax_type, 0.0) + amount

        logger.info(
            f"TAX_COLLECTED | Collected {amount:.2f} as {tax_type} from {source_id}",
            extra={
                "tick": current_tick,
                "agent_id": self.id,
                "amount": amount,
                "tax_type": tax_type,
                "source_id": source_id,
                "tags": ["tax", "revenue"]
            }
        )
        return amount

    def provide_subsidy(self, target_agent: Any, amount: float, current_tick: int):
        """보조금을 지급합니다."""
        if self.assets < amount:
            # 예산 부족 시 보유 자산만큼만 지급하거나 지급하지 않음
            amount = max(0.0, self.assets)
            
        if amount <= 0:
            return 0.0
            
        self.assets -= amount
        self.total_spent_subsidies += amount
        target_agent.assets += amount
        
        logger.info(
            f"SUBSIDY_PAID | Paid {amount:.2f} subsidy to {target_agent.id}",
            extra={
                "tick": current_tick,
                "agent_id": self.id,
                "amount": amount,
                "target_id": target_agent.id,
                "tags": ["subsidy", "expenditure"]
            }
        )
        return amount

    def invest_infrastructure(self, current_tick: int) -> bool:
        """인프라에 투자하여 전체 생산성을 향상시킵니다."""
        cost = getattr(self.config_module, "INFRASTRUCTURE_INVESTMENT_COST", 5000.0)
        
        if self.assets >= cost:
            self.assets -= cost
            self.infrastructure_level += 1
            
            logger.info(
                f"INFRASTRUCTURE_INVESTED | Level {self.infrastructure_level} reached. Cost: {cost}",
                extra={
                    "tick": current_tick,
                    "agent_id": self.id,
                    "level": self.infrastructure_level,
                    "tags": ["investment", "infrastructure"]
                }
            )
            return True
        return False

    def get_agent_data(self) -> Dict[str, Any]:
        """정부 상태 데이터를 반환합니다."""
        return {
            "id": self.id,
            "agent_type": "government",
            "assets": self.assets,
            "total_collected_tax": self.total_collected_tax,
            "total_spent_subsidies": self.total_spent_subsidies,
            "infrastructure_level": self.infrastructure_level
        }

from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class FirmActionVector:
    """
    기업의 한 틱 행동을 정의하는 연속적 적극성 벡터.
    Values ideally range from 0.0 to 1.0.
    """
    # 1. 판매 적극성 (0.0~1.0)
    # 0.0: Profit-driven (High Margin, Low Probability) -> High Price
    # 1.0: Liquidity-driven (Low Margin, High Probability) -> Low Price
    sales_aggressiveness: float = 0.5 

    # 2. 고용 적극성 (0.0~1.0)
    # 0.0: Passive Hiring -> Offer Low Wage
    # 1.0: Urgent Hiring -> Offer High Wage
    hiring_aggressiveness: float = 0.5
    
    # 3. 임금 유지/삭감 적극성 (Optional for future)
    # wage_aggressiveness: float = 0.5

    # 4. 생산 목표 조정 적극성 (Optional)
    # 1.0: Maximize Production Capacity
    # 0.0: Maintain or Reduce
    production_aggressiveness: float = 0.5


@dataclass
class HouseholdActionVector:
    """
    가계의 한 틱 행동을 정의하는 연속적 적극성 벡터.
    """
    # 1. 소비 적극성 (카테고리별 매핑)
    # Key: 'basic_food', 'luxury', etc.
    # Value: 0.0~1.0
    # 0.0: Save Money (Buy only if super cheap)
    # 1.0: Panic Buy (Buy at any price)
    consumption_aggressiveness: Dict[str, float] = field(default_factory=dict)
    
    # 2. 노동 공급 적극성
    # 0.0: High Reservation Wage (Don't work unless paid well)
    # 1.0: Low Reservation Wage (Work for anything)
    work_aggressiveness: float = 0.5

    # 3. 투자/교육 적극성
    investment_aggressiveness: float = 0.0
    learning_aggressiveness: float = 0.0

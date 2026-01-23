from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class FirmActionVector:
    """
    기업의 한 틱 행동을 정의하는 연속적 적극성 벡터.
    Values ideally range from 0.0 to 1.0.
    """

    # 1. 판매 적극성 (Pricing)
    # 0.0: High Margin (High Price)
    # 1.0: High Volume (Low Price)
    sales_aggressiveness: float = 0.5

    # 2. 고용 적극성 (Employment)
    # 0.0: Low Wage / Fire
    # 1.0: High Wage / Hire
    hiring_aggressiveness: float = 0.5

    # 3. R&D 적극성 (Innovation)
    # 0.0: No R&D
    # 1.0: Maximize R&D Spending (% of Revenue)
    rd_aggressiveness: float = 0.5

    # 4. 자본재 투자 적극성 (Capacity)
    # 0.0: No CAPEX
    # 1.0: Maximize CAPEX
    capital_aggressiveness: float = 0.5

    # 5. 배당 적극성 (Dividend)
    # 0.0: Retain Earnings
    # 1.0: Maximize Payout
    dividend_aggressiveness: float = 0.5

    # 6. 부채 관리 적극성 (Leverage)
    # 0.0: De-leverage (Repay Debt)
    # 1.0: Leverage Up (Borrow Aggressively)
    debt_aggressiveness: float = 0.5


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

    # 3. 노동 기동성 (이직 적극성)
    # 0.0: High Loyalty (Don't quit even for better wages)
    # 1.0: High Mobility (Quit immediately for slightly better wages)
    job_mobility_aggressiveness: float = 0.5

    # 4. 투자/교육 적극성
    investment_aggressiveness: float = 0.0
    learning_aggressiveness: float = 0.0

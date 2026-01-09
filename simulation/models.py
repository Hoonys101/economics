from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import uuid


@dataclass
class Order:
    """시장에 제출되는 개별 주문을 나타내는 데이터 클래스"""

    agent_id: int
    order_type: str
    item_id: str
    quantity: float
    price: float
    market_id: str
    target_agent_id: Optional[int] = None  # Phase 6: Targeted Orders (Brand Loyalty)
    brand_info: Optional[Dict[str, Any]] = None # Phase 6: Brand Metadata (awareness, quality)
    id: str = field(default_factory=lambda: str(uuid.uuid4()), init=False)


@dataclass
class Transaction:
    """체결된 거래를 나타내는 데이터 클래스"""

    buyer_id: int
    seller_id: int
    item_id: str
    quantity: float
    price: float
    market_id: str  # Added market_id
    transaction_type: str  # 'goods', 'labor', 'dividend', 'stock' 등 거래 유형
    time: int  # 거래가 발생한 시뮬레이션 틱
    quality: float = 1.0  # Phase 15: Durables Quality


@dataclass
class StockOrder:
    """주식 시장에 제출되는 주문을 나타내는 데이터 클래스"""

    agent_id: int          # 주문 제출자 ID
    order_type: str        # "BUY" or "SELL"
    firm_id: int           # 대상 기업 ID
    quantity: float        # 주문 수량
    price: float           # 호가 (주당 가격)
    id: str = field(default_factory=lambda: str(uuid.uuid4()), init=False)


@dataclass
class Share:
    """주식 보유 정보를 담는 데이터 클래스"""
    
    firm_id: int               # 발행 기업 ID
    holder_id: int             # 보유자 ID (가계 또는 기업)
    quantity: float            # 보유 수량
    acquisition_price: float   # 평균 매입 가격


@dataclass
class RealEstateUnit:
    """부동산 자산 단위 (Phase 17-3A)"""
    id: int
    owner_id: Optional[int] = None  # None = Government
    occupant_id: Optional[int] = None  # Tenant
    condition: float = 1.0
    estimated_value: float = 10000.0
    rent_price: float = 100.0
    mortgage_id: Optional[str] = None # Updated to str to match loan_id type


@dataclass
class Loan:
    borrower_id: int
    principal: float       # 원금
    remaining_balance: float # 잔액
    annual_interest_rate: float # 연이율
    term_ticks: int        # 만기 (틱)
    start_tick: int        # 대출 실행 틱
    collateral_id: Optional[int] = None # Link to RealEstateUnit.id

    @property
    def tick_interest_rate(self) -> float:
        TICKS_PER_YEAR = 100 # Default fallback, better if passed or configured
        return self.annual_interest_rate / TICKS_PER_YEAR


@dataclass
class Deposit:
    depositor_id: int
    amount: float          # 예치금
    annual_interest_rate: float # 연이율

    @property
    def tick_interest_rate(self) -> float:
        TICKS_PER_YEAR = 100
        return self.annual_interest_rate / TICKS_PER_YEAR

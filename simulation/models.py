from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, TYPE_CHECKING
import uuid
from modules.market.api import OrderDTO
from modules.finance.api import LienDTO
from modules.system.api import DEFAULT_CURRENCY

# Alias for backward compatibility and migration
Order = OrderDTO

@dataclass
class Transaction:
    """체결된 거래를 나타내는 데이터 클래스"""

    buyer_id: int | str
    seller_id: int | str
    item_id: str
    quantity: float
    price: float
    market_id: str  # Added market_id
    transaction_type: str  # 'goods', 'labor', 'dividend', 'stock' 등 거래 유형
    time: int  # 거래가 발생한 시뮬레이션 틱
    currency: str = DEFAULT_CURRENCY # TD-213: Multi-currency support
    quality: float = 1.0  # Phase 15: Durables Quality
    metadata: Optional[Dict[str, Any]] = None  # WO-109: Metadata for side-effects


@dataclass
class StockOrder:
    """주식 시장에 제출되는 주문을 나타내는 데이터 클래스"""

    agent_id: int          # 주문 제출자 ID
    order_type: str        # "BUY" or "SELL"
    firm_id: int           # 대상 기업 ID
    quantity: float        # 주문 수량
    price: float           # 호가 (주당 가격)
    market_id: str = "stock_market"
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
    """부동산 자산 단위 (Phase 17-3A, Updated for Lien System)"""
    id: int
    owner_id: Optional[int] = None  # None = Government
    occupant_id: Optional[int] = None  # Tenant
    condition: float = 1.0
    estimated_value: float = 10000.0
    rent_price: float = 100.0

    # New field for tracking all liens against the property
    liens: List[LienDTO] = field(default_factory=list)

    @property
    def mortgage_id(self) -> Optional[str]:
        """
        Backward compatibility for existing logic. Returns the loan_id of the
        first mortgage found in the liens list. Returns None if no mortgage exists.
        New logic should iterate over the `liens` list directly.
        """
        for lien in self.liens:
            if lien['lien_type'] == 'MORTGAGE':
                return str(lien['loan_id'])
        return None

@dataclass
class Talent:
    """가계의 선천적 재능을 나타내는 클래스입니다."""
    base_learning_rate: float
    max_potential: Dict[str, float]
    related_domains: Dict[str, List[str]] = field(default_factory=dict)

@dataclass
class Skill:
    """가계의 후천적 역량을 나타내는 클래스입니다."""
    domain: str
    value: float = 0.0
    observability: float = 0.5

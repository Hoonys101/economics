from dataclasses import dataclass, field
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

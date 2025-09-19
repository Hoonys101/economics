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
    market_id: str # Added market_id
    transaction_type: str # 'goods', 'labor', 'dividend' 등 거래 유형
    time: int # 거래가 발생한 시뮬레이션 틱

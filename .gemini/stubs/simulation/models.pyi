from dataclasses import dataclass, field
from modules.finance.api import LienDTO as LienDTO
from modules.market.api import CanonicalOrderDTO
from typing import Any

Order = CanonicalOrderDTO

@dataclass
class Transaction:
    """체결된 거래를 나타내는 데이터 클래스"""
    buyer_id: int | str
    seller_id: int | str
    item_id: str
    quantity: float
    price: float
    market_id: str
    transaction_type: str
    time: int
    total_pennies: int = ...
    currency: str = ...
    quality: float = ...
    metadata: dict[str, Any] | None = ...
    def __post_init__(self) -> None: ...
    @property
    def sender_id(self) -> int | str:
        """Alias for buyer_id in payment context."""
    @property
    def receiver_id(self) -> int | str:
        """Alias for seller_id in payment context."""
    @property
    def amount_pennies(self) -> int:
        """Alias for total_pennies."""
    @property
    def tick(self) -> int:
        """Alias for time."""
    @property
    def memo(self) -> str | None:
        """Accessor for memo within metadata."""

@dataclass
class Share:
    """주식 보유 정보를 담는 데이터 클래스"""
    firm_id: int
    holder_id: int
    quantity: float
    acquisition_price: int

@dataclass
class RealEstateUnit:
    """부동산 자산 단위 (Phase 17-3A, Updated for Lien System)"""
    id: int
    owner_id: int | None = ...
    occupant_id: int | None = ...
    condition: float = ...
    estimated_value: int = ...
    rent_price: int = ...
    liens: list[LienDTO] = field(default_factory=list)
    @property
    def mortgage_id(self) -> str | None:
        """
        Backward compatibility for existing logic. Returns the loan_id of the
        first mortgage found in the liens list. Returns None if no mortgage exists.
        New logic should iterate over the `liens` list directly.
        TODO: DEPRECATE_LEGACY_DICT - Remove dictionary support in Wave 2.
        """

@dataclass
class Talent:
    """가계의 선천적 재능을 나타내는 클래스입니다."""
    base_learning_rate: float
    max_potential: dict[str, float]
    related_domains: dict[str, list[str]] = field(default_factory=dict)

@dataclass
class Skill:
    """가계의 후천적 역량을 나타내는 클래스입니다."""
    domain: str
    value: float = ...
    observability: float = ...

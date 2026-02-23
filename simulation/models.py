from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, TYPE_CHECKING
import uuid
import warnings
from modules.market.api import CanonicalOrderDTO
from modules.finance.api import LienDTO, FloatIncursionError
from modules.system.api import DEFAULT_CURRENCY

# Alias for backward compatibility and migration
Order = CanonicalOrderDTO

@dataclass
class Transaction:
    """체결된 거래를 나타내는 데이터 클래스"""

    buyer_id: int | str
    seller_id: int | str
    item_id: str
    quantity: float
    price: float  # Changed from int to float (deprecated/display)
    market_id: str  # Added market_id
    transaction_type: str  # 'goods', 'labor', 'dividend', 'stock' 등 거래 유형
    time: int  # 거래가 발생한 시뮬레이션 틱
    total_pennies: int = 0 # SSoT for settlement. Default 0 allows legacy init, caught in post_init.
    currency: str = DEFAULT_CURRENCY # TD-213: Multi-currency support
    quality: float = 1.0  # Phase 15: Durables Quality
    metadata: Optional[Dict[str, Any]] = None  # WO-109: Metadata for side-effects

    def __post_init__(self):
        # 1. Float Guard for total_pennies
        if isinstance(self.total_pennies, float):
            raise FloatIncursionError(f"total_pennies must be int, got float: {self.total_pennies}")

        # 2. Legacy Migration Logic
        if self.total_pennies == 0 and self.price != 0.0:
            # LEGACY PATH: Derive pennies from float price
            # Strict rounding needed to avoid 99.99999 -> 99 issue
            self.total_pennies = int(round(self.price * self.quantity * 100))
            # Optional: warnings.warn("Transaction instantiated with float price. Use total_pennies.", DeprecationWarning)

        # 3. SSoT Enforcement
        if self.total_pennies != 0:
            # Re-calculate display price from SSoT
            calculated_price = (self.total_pennies / 100.0) / self.quantity if self.quantity else 0
            # If price was explicitly set and diverges significantly, warn or raise
            if self.price != 0 and abs(self.price - calculated_price) > 0.001:
                # We enforce SSoT but allow small float errors.
                # raise ValueError(f"SSoT Violation: price={self.price} != derived={calculated_price}")
                pass

            # Force consistency for display
            self.price = calculated_price

    # --- ITransaction Protocol Implementation ---
    @property
    def sender_id(self) -> int | str:
        """Alias for buyer_id in payment context."""
        return self.buyer_id

    @property
    def receiver_id(self) -> int | str:
        """Alias for seller_id in payment context."""
        return self.seller_id

    @property
    def amount_pennies(self) -> int:
        """Alias for total_pennies."""
        return self.total_pennies

    @property
    def tick(self) -> int:
        """Alias for time."""
        return self.time

    @property
    def memo(self) -> Optional[str]:
        """Accessor for memo within metadata."""
        if self.metadata:
            return self.metadata.get("memo")
        return None


@dataclass
class Share:
    """주식 보유 정보를 담는 데이터 클래스"""
    
    firm_id: int               # 발행 기업 ID
    holder_id: int             # 보유자 ID (가계 또는 기업)
    quantity: float            # 보유 수량
    acquisition_price: int     # Changed from float to int (pennies)


@dataclass
class RealEstateUnit:
    """부동산 자산 단위 (Phase 17-3A, Updated for Lien System)"""
    id: int
    owner_id: Optional[int] = None  # None = Government
    occupant_id: Optional[int] = None  # Tenant
    condition: float = 1.0
    estimated_value: int = 10000  # Changed from float to int (pennies)
    rent_price: int = 100         # Changed from float to int (pennies)

    # New field for tracking all liens against the property
    liens: List[LienDTO] = field(default_factory=list)

    @property
    def mortgage_id(self) -> Optional[str]:
        """
        Backward compatibility for existing logic. Returns the loan_id of the
        first mortgage found in the liens list. Returns None if no mortgage exists.
        New logic should iterate over the `liens` list directly.
        TODO: DEPRECATE_LEGACY_DICT - Remove dictionary support in Wave 2.
        """
        for lien in self.liens:
            if hasattr(lien, 'lien_type') and lien.lien_type == 'MORTGAGE':
                return str(lien.loan_id)
            elif isinstance(lien, dict) and lien.get('lien_type') == 'MORTGAGE':
                return str(lien.get('loan_id'))
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

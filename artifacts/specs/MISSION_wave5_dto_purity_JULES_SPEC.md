modules/market/api.py
```python
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, TypedDict, Protocol, List, runtime_checkable, Union
from enum import Enum
import uuid
from pydantic import BaseModel, Field, field_validator

# Phase 33 Imports
from modules.finance.dtos import MoneyDTO
from modules.system.api import DEFAULT_CURRENCY, CurrencyCode
from modules.common.interfaces import IPropertyOwner
from modules.finance.api import IFinancialAgent

# --- Enums ---

class MarketSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

# --- Core Engine DTOs (Frozen Dataclasses for Performance) ---

@dataclass(frozen=True)
class CanonicalOrderDTO:
    """
    Standardized Market Order Data Transfer Object (Engine Layer).
    Immutable to prevent side-effects during processing.
    
    Adheres to [SEO_PATTERN.md] - Pure Data.
    """
    agent_id: Union[int, str]
    side: str  # "BUY" or "SELL" (Validated by MarketSide in logic)
    item_id: str
    quantity: float
    price_pennies: int # Integer pennies (The SSoT)
    market_id: str

    # Legacy/Display fields (Deprecated but kept for transition)
    price_limit: float = 0.0 # DEPRECATED: Use price_pennies

    # Phase 6/7 Extensions
    target_agent_id: Optional[int] = None
    brand_info: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    # TD-213: Multi-Currency Support
    monetary_amount: Optional[MoneyDTO] = None
    currency: CurrencyCode = DEFAULT_CURRENCY

    # Auto-generated ID
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    @property
    def price(self) -> float:
        """Alias for legacy compatibility. Returns float dollars."""
        return self.price_pennies / 100.0

    @property
    def order_type(self) -> str:
        """Alias for legacy compatibility."""
        return self.side

# --- Boundary DTOs (Pydantic Models for UI/Telemetry) ---

class OrderTelemetrySchema(BaseModel):
    """
    Pydantic model for strictly typed UI/Websocket serialization.
    Satisfies [TD-UI-DTO-PURITY].
    """
    id: str
    agent_id: Union[int, str]
    side: MarketSide
    item_id: str
    quantity: float
    price_pennies: int
    price_display: float = Field(..., description="Human readable float price")
    market_id: str
    currency: str = DEFAULT_CURRENCY
    timestamp: int = 0

    @field_validator('side', mode='before')
    def normalize_side(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v

    @classmethod
    def from_canonical(cls, dto: CanonicalOrderDTO, timestamp: int = 0) -> 'OrderTelemetrySchema':
        """Adapter: CanonicalOrderDTO -> OrderTelemetrySchema"""
        return cls(
            id=dto.id,
            agent_id=dto.agent_id,
            side=dto.side,  # type: ignore
            item_id=dto.item_id,
            quantity=dto.quantity,
            price_pennies=dto.price_pennies,
            price_display=dto.price,
            market_id=dto.market_id,
            currency=dto.currency,
            timestamp=timestamp
        )

# --- Interfaces ---

@runtime_checkable
class IMarket(Protocol):
    """
    Standard interface for all market types.
    Enforces strictly typed CanonicalOrderDTOs.
    """
    id: str

    @property
    def buy_orders(self) -> Dict[str, List[CanonicalOrderDTO]]:
        """Returns active buy orders as immutable DTOs."""
        ...

    @property
    def sell_orders(self) -> Dict[str, List[CanonicalOrderDTO]]:
        """Returns active sell orders as immutable DTOs."""
        ...

    def place_order(self, order_dto: CanonicalOrderDTO, current_time: int) -> None:
        """Submits a new order to the market."""
        ...

    def cancel_orders(self, agent_id: str) -> None:
        """Cancels all orders for the specified agent."""
        ...

    def get_telemetry_snapshot(self) -> List[OrderTelemetrySchema]:
        """Returns Pydantic schemas for UI consumption."""
        ...

# --- Helpers ---

class StockIDHelper:
    """Helper for Stock ID formatting and parsing."""
    PREFIX = "stock"
    SEPARATOR = "_"

    @staticmethod
    def is_valid_stock_id(item_id: str) -> bool:
        if not item_id or not isinstance(item_id, str):
            return False
        parts = item_id.split(StockIDHelper.SEPARATOR)
        return len(parts) == 2 and parts[0] == StockIDHelper.PREFIX and parts[1].isdigit()

    @staticmethod
    def parse_firm_id(item_id: str) -> int:
        if not StockIDHelper.is_valid_stock_id(item_id):
            raise ValueError(f"Invalid Stock ID: {item_id}")
        return int(item_id.split(StockIDHelper.SEPARATOR)[1])

    @staticmethod
    def format_stock_id(firm_id: Union[int, str]) -> str:
        return f"{StockIDHelper.PREFIX}{StockIDHelper.SEPARATOR}{firm_id}"

# --- Deprecated Aliases (For phased migration) ---
# Warn: Use CanonicalOrderDTO directly.
OrderDTO = CanonicalOrderDTO
```

design/3_work_artifacts/specs/wave5_dto_purity_spec.md
```markdown
# MISSION SPEC: Wave 5 DTO Purity & Market Standardization

## 1. Introduction
This specification addresses critical technical debt in the Data Transfer Object (DTO) layer, specifically focusing on the Market and UI subsystems. It aims to eliminate legacy, loosely-typed structures (`StockOrder`, raw dicts) and enforce strict, type-safe contracts (`CanonicalOrderDTO`, Pydantic Schemas).

### 1.1 Goals
-   **Resolve TD-DEPR-STOCK-DTO**: Fully deprecate `StockOrder` and legacy `OrderDTO` aliases in favor of `CanonicalOrderDTO`.
-   **Resolve TD-UI-DTO-PURITY**: Implement Pydantic models for the Dashboard/Telemetry interface to prevent serialization errors.
-   **Enhance Type Safety**: Eliminate `float` ambiguity in price fields by strictly enforcing `price_pennies`.

---

## 2. Architecture & Design

### 2.1 The "Two-Tier DTO" Strategy
To balance high-frequency engine performance with robust UI validation, we adopt a two-tier strategy:

1.  **Core Engine Layer (`CanonicalOrderDTO`)**:
    -   **Type**: Frozen Dataclass.
    -   **Reason**: Low overhead, immutable, optimized for high-volume matching engines.
    -   **Standard**: Must be used for all internal `Market`, `MatchingEngine`, and `Agent` logic.

2.  **Boundary Layer (`OrderTelemetrySchema`)**:
    -   **Type**: Pydantic BaseModel.
    -   **Reason**: Runtime validation, JSON schema generation, safe serialization for Websockets/REST.
    -   **Standard**: Must be used for all `TelemetryService` and `Dashboard` communication.

### 2.2 Namespace De-confliction
A critical naming collision exists between `simulation.dtos.api.OrderDTO` (which points to `simulation.models.Order`) and `modules.market.api.OrderDTO` (which points to `CanonicalOrderDTO`).

-   **Action**: Rename `simulation.dtos.api.OrderDTO` to `LegacySimulationOrder` (or remove the alias if unused).
-   **Action**: Update all imports in `simulation/` to use explicit namespaces.

---

## 3. Implementation Steps

### 3.1 Step 1: Market API Hardening (`modules/market/api.py`)
-   Define `OrderTelemetrySchema` (Pydantic).
-   Implement `from_canonical()` factory method.
-   Deprecate `convert_legacy_order_to_canonical` heuristics; enforce strict construction.

### 3.2 Step 2: Dashboard Service Refactor (`modules/dashboard/services/telemetry_service.py`)
-   Locate the websocket broadcast loop.
-   **Before**:
    ```python
    # BAD: Manual dict construction
    payload = {"id": order.id, "price": order.price_limit, ...}
    ```
-   **After**:
    ```python
    # GOOD: Pydantic serialization
    schema = OrderTelemetrySchema.from_canonical(order, timestamp=tick)
    payload = schema.model_dump()
    ```

### 3.3 Step 3: Agent Logic Migration
-   Search for all usages of `StockOrder`.
-   Replace with `CanonicalOrderDTO`.
-   **Crucial**: Ensure `price` (float) access is replaced with `price_pennies` (int) or careful usage of the `.price` property.

### 3.4 Step 4: Strict Namespace Enforcement
-   Modify `simulation/dtos/api.py`:
    ```python
    # Change this:
    # OrderDTO = Order
    # To this:
    LegacySimulationOrder = Order
    # And deprecate OrderDTO alias entirely to force explicit usage.
    ```

---

## 4. Testing & Verification Strategy

### 4.1 New Test Cases (`tests/market/test_dto_purity.py`)
-   **Serialization Test**: Create a `CanonicalOrderDTO`, convert to `OrderTelemetrySchema`, and assert JSON output matches expectations.
-   **Validation Test**: Try to create `OrderTelemetrySchema` with invalid side (e.g., "HOLD") and assert `ValidationError`.
-   **Penny Integrity**: Verify that `price_pennies` is correctly preserved through the Pydantic roundtrip.

### 4.2 Regression Testing
-   **Run**: `pytest tests/market/`
-   **Check**: `test_stock_market.py` relies heavily on legacy order structures. Expect failures here.
-   **Fix**: Update test fixtures in `conftest.py` to produce `CanonicalOrderDTOs` instead of dicts/StockOrders.

---

## 5. Risk Assessment (Pre-Implementation Audit)

-   **Risk**: `StockOrder` is mutable in legacy code; `CanonicalOrderDTO` is frozen.
    -   *Mitigation*: Identify where `order.quantity -= filled` happens. Replace with `replace(order, quantity=new_q)`.
-   **Risk**: UI Frontend (React/TS) might expect exact field names from the old dict.
    -   *Mitigation*: The `OrderTelemetrySchema` should use `Field(alias="legacy_name")` if absolutely necessary to preserve contract, OR update the frontend type definitions (preferred). **Decision**: Strict Pydantic names. Frontend update is out of scope for *this* CLI session but backend must be pure.
-   **Critical**: Zero-Sum violation if `price` float conversion drifts.
    -   *Control*: All financial calculations must strictly use `price_pennies`.

---

## 6. Mandatory Reporting

> [!IMPORTANT]
> As per protocol, you must create `communications/insights/wave5-dto-purity.md` before marking this task complete.
> This report must contain:
> 1.  Confirmation of `StockOrder` removal.
> 2.  List of files modified.
> 3.  Output of the test suite verifying no regressions.
```
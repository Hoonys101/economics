File: modules\system\api.py
```python
from __future__ import annotations
from typing import Any, Dict, List, Optional, Protocol, Union, TypedDict, runtime_checkable
from dataclasses import dataclass

# Define Currency Code (Usually String "USD")
CurrencyCode = str
DEFAULT_CURRENCY: CurrencyCode = "USD"
AgentID = int

@dataclass
class MarketContextDTO:
    """
    Context object passed to agents for making decisions.
    Contains strictly external market data (prices, rates, signals).
    """
    market_data: Dict[str, Any]
    market_signals: Dict[str, float]
    tick: int
    # Added to resolve TypeError in test_sales_engine_refactor
    # Represents currency exchange rates relative to base currency
    exchange_rates: Optional[Dict[str, float]] = None

@dataclass(frozen=True)
class MarketSignalDTO:
    """
    Represents the signal state of a specific market item.
    Frozen to ensure immutability during decision processing.
    """
    market_id: str
    item_id: str
    best_bid: Optional[float]
    best_ask: Optional[float]
    last_traded_price: Optional[float]
    last_trade_tick: int
    price_history_7d: List[float]
    volatility_7d: float
    order_book_depth_buy: int
    order_book_depth_sell: int
    # Mandatory fields (Must be supplied by caller/mock)
    total_bid_quantity: float
    total_ask_quantity: float
    is_frozen: bool

@dataclass(frozen=True)
class HousingMarketUnitDTO:
    unit_id: str
    price: float
    quality: float
    rent_price: Optional[float] = None

@dataclass(frozen=True)
class HousingMarketSnapshotDTO:
    for_sale_units: List[HousingMarketUnitDTO]
    units_for_rent: List[HousingMarketUnitDTO]
    avg_rent_price: float
    avg_sale_price: float

@dataclass(frozen=True)
class LoanMarketSnapshotDTO:
    interest_rate: float

@dataclass(frozen=True)
class LaborMarketSnapshotDTO:
    avg_wage: float

@dataclass(frozen=True)
class MarketSnapshotDTO:
    """
    A pure-data snapshot of the state of all markets at a point in time.
    """
    tick: int
    market_signals: Dict[str, MarketSignalDTO]
    # Mandatory field - Caller must provide a dict (even if empty)
    market_data: Dict[str, Any]
    housing: Optional[HousingMarketSnapshotDTO] = None
    loan: Optional[LoanMarketSnapshotDTO] = None
    labor: Optional[LaborMarketSnapshotDTO] = None

class AgentBankruptcyEventDTO(TypedDict):
    agent_id: int
    tick: int
    inventory: Dict[str, float]

@dataclass(frozen=True)
class PublicManagerReportDTO:
    tick: int
    newly_recovered_assets: Dict[str, float]
    liquidation_revenue: Dict[str, int]
    managed_inventory_count: float
    system_treasury_balance: Dict[str, int]

# ... (Rest of the file: OriginType, RegistryEntry, Protocols)
# ... Preserving existing Registry protocols as defined in Context
```

File: design\3_work_artifacts\specs\fix_market_dtos_spec.md
```markdown
# Spec: Synchronize Market DTO Schemas

## 1. Introduction
This specification addresses the critical schema desynchronization between `modules.system.api` DTO definitions and their instantiation in test suites and legacy modules. The mismatch is currently causing widespread `TypeError` failures in CI/CD pipelines (e.g., missing positional arguments, unexpected keyword arguments).

## 2. Scope & Objectives
*   **Target Modules**: `modules/system/api.py`
*   **Target Tests**:
    *   `tests/unit/test_sales_engine_refactor.py`
    *   `tests/integration/scenarios/diagnosis/test_agent_decision.py`
    *   `tests/unit/test_household_ai.py`
    *   `tests/unit/modules/system/execution/test_public_manager.py`
    *   `tests/integration/test_public_manager_integration.py`
*   **Goal**: Eliminate `TypeError` exceptions related to `MarketContextDTO`, `MarketSnapshotDTO`, and `MarketSignalDTO` by standardizing definitions and updating call sites.

## 3. Implementation Plan

### 3.1. API Definition Update (`modules/system/api.py`)
*   **`MarketContextDTO`**:
    *   Add `exchange_rates: Optional[Dict[str, float]] = None` field.
    *   *Rationale*: Supports multi-currency logic referenced in `test_sales_engine_refactor.py` without breaking existing callers that do not provide it (via default `None`).

### 3.2. Test Refactoring (Call Site Fixes)

#### A. `MarketSnapshotDTO` Instantiation
*   **Issue**: Missing `market_data` positional argument.
*   **Action**: Locate all instantiations in failing tests and inject an empty dictionary or relevant mock data.
*   **Pseudo-code Fix**:
    ```python
    # Before
    snapshot = MarketSnapshotDTO(tick=1, market_signals={...})
    
    # After
    snapshot = MarketSnapshotDTO(
        tick=1, 
        market_signals={...}, 
        market_data={}  # Injected
    )
    ```

#### B. `MarketSignalDTO` Instantiation
*   **Issue**: Missing `total_bid_quantity`, `total_ask_quantity`, `is_frozen`.
*   **Action**: Locate instantiations in `test_household_ai.py` and `test_public_manager*.py`.
*   **Pseudo-code Fix**:
    ```python
    # Before
    signal = MarketSignalDTO(
        market_id="food", item_id="apple", ..., volatility_7d=0.1,
        order_book_depth_buy=5, order_book_depth_sell=5
    )
    
    # After
    signal = MarketSignalDTO(
        market_id="food", item_id="apple", ..., volatility_7d=0.1,
        order_book_depth_buy=5, order_book_depth_sell=5,
        # Injected Defaults for Mocks
        total_bid_quantity=0.0,
        total_ask_quantity=0.0,
        is_frozen=False
    )
    ```

### 3.3. Factory/Fixture Updates
*   If a centralized mock factory exists (e.g., `tests/conftest.py` or a utility helper), update it once to propagate changes to all tests.
*   *Note*: The logs suggest direct instantiation in many places, implying a need for a "sweep" of the test files.

## 4. Verification Plan

### 4.1. Automated Verification
Run the specific failing tests to confirm resolution:
```bash
pytest tests/unit/test_sales_engine_refactor.py
pytest tests/integration/scenarios/diagnosis/test_agent_decision.py
pytest tests/unit/test_household_ai.py
```

### 4.2. Regression Check
Ensure `mypy` static analysis passes to confirm type safety across the changed files.

## 5. Mandatory Reporting & Insights

> **[IMPORTANT]** After applying these fixes, you MUST create/update the insight report at `communications/insights/spec-fix-market-dtos.md`.

**Report Content Requirements:**
1.  **Root Cause**: Document that the DTOs were evolved (likely for Phase 33/Global Economy) but the test suite was not refactored in tandem.
2.  **Tech Debt**: Note the lack of a centralized `DTOFactory` for tests, leading to brittle "Shotgun Surgery" requirements when DTOs change.
3.  **Test Evidence**: Paste the `pytest` summary showing the tests passing (green).

## 6. Risk Audit
*   **Risk**: `MarketContextDTO` usage in production code might rely on `exchange_rates` being present if the test was asserting logic based on it. By making it `Optional`, we must ensure the production code handles `None`.
*   **Mitigation**: The `Optional` default ensures backward compatibility. New logic using `exchange_rates` should guard with `if context.exchange_rates:`.
```
modules/system/api.py
```python
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, Union, runtime_checkable, TYPE_CHECKING, TypedDict
from dataclasses import dataclass, field
from enum import IntEnum, auto
from pydantic import BaseModel, Field

# Define Currency Code (Usually String "USD")
CurrencyCode = str
DEFAULT_CURRENCY: CurrencyCode = "USD"
AgentID = int

# ... (Existing DTOs: MarketContextDTO, MarketSignalDTO, etc. kept as is) ...

 @dataclass(frozen=True)
class MarketSignalDTO:
    market_id: str
    item_id: str
    best_bid: Optional[int]
    best_ask: Optional[int]
    last_traded_price: Optional[int]
    last_trade_tick: int
    price_history_7d: List[int]
    volatility_7d: float
    order_book_depth_buy: int
    order_book_depth_sell: int
    total_bid_quantity: float
    total_ask_quantity: float
    is_frozen: bool

 @dataclass(frozen=True)
class HousingMarketUnitDTO:
    unit_id: str
    price: int
    quality: float
    rent_price: Optional[int] = None

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
    market_data: Dict[str, Any]
    housing: Optional[HousingMarketSnapshotDTO] = None
    loan: Optional[LoanMarketSnapshotDTO] = None
    labor: Optional[LaborMarketSnapshotDTO] = None

 @dataclass
class MarketContextDTO:
    """
    Context object passed to agents for making decisions.
    Contains strictly external market data (prices, rates, signals).
    """
    market_data: Dict[str, Any]
    market_signals: Dict[str, int]
    tick: int
    exchange_rates: Optional[Dict[str, float]] = None

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

class OriginType(IntEnum):
    SYSTEM = 0
    CONFIG = 10
    USER = 50
    GOD_MODE = 100

class RegistryValueDTO(BaseModel):
    key: str
    value: Any
    domain: str = "global"
    origin: OriginType
    is_locked: bool = False
    last_updated_tick: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)

RegistryEntry = RegistryValueDTO

class RegistryObserver(Protocol):
    def on_registry_update(self, key: str, value: Any, origin: OriginType) -> None:
        ...

 @runtime_checkable
class IConfigurationRegistry(Protocol):
    def get(self, key: str, default: Any = None) -> Any: ...
    def set(self, key: str, value: Any, origin: OriginType = OriginType.USER) -> None: ...
    def snapshot(self) -> Dict[str, Any]: ...
    def reset_to_defaults(self) -> None: ...

 @runtime_checkable
class IGlobalRegistry(Protocol):
    def get(self, key: str, default: Any = None) -> Any: ...
    def set(self, key: str, value: Any, origin: OriginType = OriginType.CONFIG) -> bool: ...
    def lock(self, key: str) -> None: ...
    def unlock(self, key: str) -> None: ...
    def subscribe(self, observer: RegistryObserver, keys: Optional[List[str]] = None) -> None: ...
    def snapshot(self) -> Dict[str, RegistryValueDTO]: ...
    def get_metadata(self, key: str) -> Any: ...
    def get_entry(self, key: str) -> Optional[RegistryValueDTO]: ...

 @runtime_checkable
class IRestorableRegistry(IGlobalRegistry, Protocol):
    def delete_entry(self, key: str) -> bool: ...
    def restore_entry(self, key: str, entry: RegistryValueDTO) -> bool: ...

 @runtime_checkable
class IProtocolEnforcer(Protocol):
    def assert_implements_protocol(self, instance: Any, protocol: Any) -> None: ...

class IAgentRegistry(Protocol):
    def get_agent(self, agent_id: Any) -> Any: ...
    def get_all_financial_agents(self) -> List[Any]: ...
    def set_state(self, state: Any) -> None: ...

 @runtime_checkable
class ICurrencyHolder(Protocol):
    def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int: ...
    def get_assets_by_currency(self) -> Dict[CurrencyCode, int]: ...

 @runtime_checkable
class IAssetRecoverySystem(Protocol):
    def process_bankruptcy_event(self, event: AgentBankruptcyEventDTO) -> None: ...
    def receive_liquidated_assets(self, inventory: Dict[str, float]) -> None: ...
    def generate_liquidation_orders(self, market_signals: Dict[str, MarketSignalDTO], core_config: Any = None, engine: Any = None) -> List[Any]: ...

# ==============================================================================
# New: Database & Migration Protocols
# ==============================================================================

 @dataclass(frozen=True)
class MigrationReportDTO:
    """
    Report generated after a database schema migration attempt.
    """
    success: bool
    migrated_tables: List[str]
    rows_affected: int
    errors: List[str]
    timestamp: float
    schema_version: str = "1.0.0"

 @runtime_checkable
class IDatabaseMigrator(Protocol):
    """
    Protocol for the Database Migration Service.
    Responsible for ensuring the database schema matches the codebase's expectations.
    """
    def check_schema_health(self) -> Dict[str, bool]:
        """
        Verifies if critical tables and columns exist.
        Returns a dict mapping 'Table.Column' to Boolean existence.
        """
        ...

    def migrate(self) -> MigrationReportDTO:
        """
        Executes pending migrations (e.g., adding missing columns).
        Must be idempotent.
        """
        ...
```

design/3_work_artifacts/specs/db_migration_spec.md
```markdown
# Spec: Database Schema Migration & Integrity Fix

## 1. Context & Objective
- **Problem**: The `transactions` table in `sqlite` databases is missing the `total_pennies` column, which is required by the `TransactionData` DTO. This causes runtime crashes when `MarketRepository` attempts to save transaction logs.
- **Evidence**: `TD-DB-SCHEMA-DRIFT` in `TECH_DEBT_LEDGER.md`.
- **Goal**: Implement a robust auto-migration mechanism in the `SimulationRepository` initialization logic to detect schema drift and fix it automatically without data loss.

## 2. Technical Debt & Risk Audit
- **Debt Resolved**: `TD-DB-SCHEMA-DRIFT` (Partially addresses `TD-CRIT-FLOAT-CORE` by enabling penny storage).
- **Architecture Risk**:
    - **Split-Brain Schema**: `db_manager.py` uses `transactions_history` while `schema.py` uses `transactions`.
    - **Resolution**: This spec mandates `schema.py` and `SimulationRepository` as the SSoT. `db_manager.py` must be deprecated or aligned. We will focus on `schema.py`'s `transactions` table as the canonical source.
- **Migration Risk**:
    - **Precision Loss**: Converting legacy float `price * quantity` to `int` pennies might result in off-by-one errors due to floating point arithmetic.
    - **Mitigation**: Use `round(price * quantity * 100)` before casting to `int`.

## 3. Detailed Design

### 3.1. `SchemaMigrator` Component
A new class `SchemaMigrator` will be introduced in `simulation/db/migration.py`.

#### Logic Flow (Pseudo-code)
```python
class SchemaMigrator(IDatabaseMigrator):
    def __init__(self, connection: sqlite3.Connection):
        self.conn = connection

    def check_schema_health(self) -> Dict[str, bool]:
        # 1. Check if 'transactions' table exists
        # 2. If exists, check if 'total_pennies' column exists using PRAGMA table_info
        return {"transactions.total_pennies": exists}

    def migrate(self) -> MigrationReportDTO:
        # 1. Check health
        # 2. If 'transactions' table missing -> Create it (using schema.py logic)
        # 3. If 'transactions' exists but 'total_pennies' missing:
        #    a. ALTER TABLE transactions ADD COLUMN total_pennies INTEGER DEFAULT 0;
        #    b. UPDATE transactions SET total_pennies = CAST(ROUND(price * quantity * 100) AS INTEGER);
        # 4. Return Report
```

### 3.2. Integration Point
The `SimulationRepository.__init__` method must be updated to instantiate and run `SchemaMigrator` **before** initializing sub-repositories.

```python
# simulation/db/repository.py

class SimulationRepository:
    def __init__(self):
        self.conn = get_db_connection()
        
        # [NEW] Auto-Migration
        migrator = SchemaMigrator(self.conn)
        report = migrator.migrate()
        if not report.success:
            logger.error(f"Migration Failed: {report.errors}")
            raise RuntimeError("Database migration failed")

        self.agents = AgentRepository(self.conn)
        # ...
```

### 3.3. DTO Definitions
(Defined in `modules/system/api.py`)
- `MigrationReportDTO`
- `IDatabaseMigrator` (Protocol)

## 4. Verification Plan

### 4.1. Test Cases
1.  **Test: Fresh Install**:
    - Start with no DB.
    - Run `SimulationRepository()`.
    - Verify `transactions` table has `total_pennies`.
2.  **Test: Legacy Migration**:
    - Create a temp DB with `transactions` table WITHOUT `total_pennies`.
    - Insert a row: `price=1.5, quantity=2.0`.
    - Run `SchemaMigrator.migrate()`.
    - Verify `total_pennies` exists and equals `300`.
3.  **Test: Idempotency**:
    - Run `migrate()` twice.
    - Verify no errors and data remains unchanged.

### 4.2. Existing Test Impact
- `tests/test_settlement_index.py` and `tests/test_transactions.py` might implicitly rely on the DB. Ensure they use the updated `SimulationRepository`.

## 5. Implementation Steps
1.  Define `IDatabaseMigrator` in `modules/system/api.py`.
2.  Create `simulation/db/migration.py` implementing `SchemaMigrator`.
3.  Inject migration logic into `simulation/db/repository.py`.
4.  Add unit test `tests/test_db_migration.py`.
5.  (Optional) Align `db_manager.py` table names if time permits, otherwise mark as DEPRECATED.

## 6. Mandatory Reporting
- All findings from this design phase must be logged in `communications/insights/spec-fix-db-migration.md`.
```
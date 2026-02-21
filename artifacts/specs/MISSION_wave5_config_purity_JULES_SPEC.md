File: modules/system/api.py
```python
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, Union, runtime_checkable, TYPE_CHECKING, TypedDict, Literal
from dataclasses import dataclass, field
from enum import IntEnum, auto
from pydantic import BaseModel, Field

# Define Currency Code (Usually String "USD")
CurrencyCode = str
DEFAULT_CURRENCY: CurrencyCode = "USD"
AgentID = int

# ==============================================================================
# Configuration & Registry Protocols (SSoT)
# ==============================================================================

class OriginType(IntEnum):
    """
    Priority Level for Parameter Updates.
    Higher value = Higher Priority.
    """
    SYSTEM = 0          # Internal logic (Hardcoded defaults)
    CONFIG = 10         # Loaded from file (User Configuration)
    USER = 50           # Dashboard/UI manual override
    GOD_MODE = 100      # Absolute override (Scenario Injection)

class RegistryValueDTO(BaseModel):
    """
    Data Transfer Object for Registry Values.
    Replaces the legacy RegistryEntry dataclass.
    """
    key: str
    value: Any
    domain: str = "global"
    origin: OriginType
    is_locked: bool = False
    last_updated_tick: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)

# Alias for backward compatibility
RegistryEntry = RegistryValueDTO

class RegistryObserver(Protocol):
    def on_registry_update(self, key: str, value: Any, origin: OriginType) -> None:
        ...

@runtime_checkable
class IConfig(Protocol):
    """
    Consumer Interface for Configuration.
    Provides read-only access to system parameters.
    Modules should depend on this, not the full Registry.
    """
    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieves a configuration value.
        Must support dynamic resolution (always fetch current value).
        """
        ...
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Typed accessor for integers."""
        ...
        
    def get_float(self, key: str, default: float = 0.0) -> float:
        """Typed accessor for floats."""
        ...
        
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Typed accessor for booleans."""
        ...

@runtime_checkable
class IConfigurationRegistry(IConfig, Protocol):
    """
    Management Interface for the Global Registry acting as the Single Source of Truth (SSoT).
    Foundational for God Mode, Scenario Injection, and Runtime Tuning.
    """

    def set(self, key: str, value: Any, origin: OriginType = OriginType.USER) -> None:
        """
        Updates a configuration value with a specified origin.
        Should trigger any registered listeners for this key.
        """
        ...

    def lock(self, key: str) -> None:
        """Locks a key preventing modification from lower-priority origins."""
        ...

    def unlock(self, key: str) -> None:
        """Unlocks a key."""
        ...

    def subscribe(self, observer: RegistryObserver, keys: Optional[List[str]] = None) -> None:
        """Registers an observer for updates."""
        ...

    def snapshot(self) -> Dict[str, RegistryValueDTO]:
        """
        Returns a complete snapshot of the current configuration state.
        Useful for serialization or debugging.
        """
        ...

    def reset_to_defaults(self) -> None:
        """
        Resets all configuration values to their SYSTEM or CONFIG defaults,
        clearing USER overrides.
        """
        ...

@runtime_checkable
class IRestorableRegistry(IConfigurationRegistry, Protocol):
    """
    Extended interface for Registries that support state restoration/undo operations.
    Required for CommandService rollback functionality.
    """
    def delete_entry(self, key: str) -> bool:
        """
        Removes an entry completely. Used when rolling back a creation.
        Returns True if successful.
        """
        ...

    def restore_entry(self, key: str, entry: RegistryValueDTO) -> bool:
        """
        Restores a specific entry state (value + origin + lock).
        Used when rolling back a modification.
        Returns True if successful.
        """
        ...

# ==============================================================================
# Existing System DTOs
# ==============================================================================

@dataclass
class MarketContextDTO:
    """
    Context object passed to agents for making decisions.
    Contains strictly external market data (prices, rates, signals).
    """
    market_data: Dict[str, Any]
    market_signals: Dict[str, int]
    tick: int
    # Represents currency exchange rates relative to base currency
    exchange_rates: Optional[Dict[str, float]] = None

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

class AgentBankruptcyEventDTO(TypedDict):
    agent_id: int
    tick: int
    inventory: Dict[str, float]
    total_debt: int
    creditor_ids: List[int]

@dataclass(frozen=True)
class AssetBuyoutRequestDTO:
    """
    Request payload for the PublicManager to purchase assets from a distressed entity.
    """
    seller_id: AgentID
    inventory: Dict[str, float]
    market_prices: Dict[str, int]  # Current market price (pennies) for valuation
    distress_discount: float = 0.5 # e.g., 50% of market value

@dataclass(frozen=True)
class AssetBuyoutResultDTO:
    """
    Result of an asset buyout operation.
    """
    success: bool
    total_paid_pennies: int
    items_acquired: Dict[str, float]
    buyer_id: AgentID  # PublicManager ID
    transaction_id: Optional[str] = None

@dataclass(frozen=True)
class PublicManagerReportDTO:
    tick: int
    newly_recovered_assets: Dict[str, float]
    liquidation_revenue: Dict[str, int]
    managed_inventory_count: float
    system_treasury_balance: Dict[str, int]
    cumulative_deficit: int = 0  # Added to track total "bailout" funding injected

@runtime_checkable
class IProtocolEnforcer(Protocol):
    """
    Interface for test utilities that enforce strict protocol adherence.
    """
    def assert_implements_protocol(self, instance: Any, protocol: Any) -> None:
        ...

class IAgentRegistry(Protocol):
    def get_agent(self, agent_id: Any) -> Any: ...
    def get_all_financial_agents(self) -> List[Any]: ...
    def set_state(self, state: Any) -> None: ...

@runtime_checkable
class ICurrencyHolder(Protocol):
    """
    Protocol for agents/systems that hold currency.
    Used for M2 Money Supply calculation.
    """
    def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int: ...
    def get_assets_by_currency(self) -> Dict[CurrencyCode, int]: ...

@runtime_checkable
class IAssetRecoverySystem(Protocol):
    """
    Interface for the Public Manager acting as a receiver of assets.
    """
    def process_bankruptcy_event(self, event: AgentBankruptcyEventDTO) -> None: ...
    def execute_asset_buyout(self, request: AssetBuyoutRequestDTO) -> AssetBuyoutResultDTO: ...
    def receive_liquidated_assets(self, inventory: Dict[str, float]) -> None: ...
    def generate_liquidation_orders(self, market_signals: Dict[str, MarketSignalDTO], core_config: Any = None, engine: Any = None) -> List[Any]: ...
    def get_deficit(self) -> int: ...

@runtime_checkable
class ISystemFinancialAgent(Protocol):
    """
    Marker interface for system agents (like PublicManager) that are exempt
    from strict solvency checks during specific system operations.
    """
    def is_system_agent(self) -> bool: ...

# ==============================================================================
# Database & Migration Protocols
# ==============================================================================

@dataclass(frozen=True)
class MigrationReportDTO:
    success: bool
    migrated_tables: List[str]
    rows_affected: int
    errors: List[str]
    timestamp: float
    schema_version: str = "1.0.0"

@runtime_checkable
class IDatabaseMigrator(Protocol):
    def check_schema_health(self) -> Dict[str, bool]: ...
    def migrate(self) -> MigrationReportDTO: ...
```

File: design/3_work_artifacts/specs/MISSION_wave5_config_purity_spec.md
```markdown
# MISSION SPEC: wave5-config-purity (Config Proxy & Hardening)

## 1. Goal
Resolve **TD-CONF-GHOST-BIND** and **TD-CONF-MAGIC-NUMBERS** by replacing static import-time configuration bindings with a dynamic `ConfigProxy` pattern. This ensures that runtime changes to configuration (e.g., via God Mode or Scenario Injection) are immediately reflected in business logic without requiring a restart.

## 2. Scope
- **Core Infrastructure**: Implement `ConfigProxy` implementing `IConfig` in `modules/system`.
- **API Unification**: Consolidate `modules.finance.api.IConfig` into `modules.system.api.IConfig`.
- **Refactoring**: Update `FinanceEngine` and `TransactionEngine` to use injected configuration instead of static imports.
- **Magic Number Elimination**: Identify hardcoded literals in `FinanceEngine` and move them to `defaults.py` / `ConfigProxy`.

## 3. Detailed Design

### 3.1. Architecture: The Proxy Pattern

We will stop importing values directly from `config.py`. Instead, we will import a singleton `proxy` or inject it.

**Before (Legacy):**
```python
# modules/finance/engine.py
from config import FINANCE_Z_SCORE_THRESHOLD  # Bound at import time!

class FinanceEngine:
    def check_solvency(self, firm):
        if firm.score < FINANCE_Z_SCORE_THRESHOLD: # Stale value if config changed
            ...
```

**After (Target):**
```python
# modules/finance/engine.py
from modules.system.api import IConfig

class FinanceEngine:
    def __init__(self, config: IConfig):
        self.config = config

    def check_solvency(self, firm):
        # Dynamically fetches current value
        threshold = self.config.get_float("FINANCE_Z_SCORE_THRESHOLD", 1.5)
        if firm.score < threshold:
            ...
```

### 3.2. Component: `ConfigProxy` (modules/system/config_proxy.py)

- **Responsibility**: A lightweight wrapper around `IConfigurationRegistry`.
- **Interface**: Implements `modules.system.api.IConfig`.
- **Mechanism**:
  - Holds a reference to the active `IConfigurationRegistry`.
  - `get(key)` delegates to `registry.get(key)`.
  - Provides typed helpers (`get_int`, `get_float`) to reduce casting boilerplate.

### 3.3. Magic Number Ledger (Migration Target)

The following hardcoded values in `FinanceEngine` MUST be externalized to `config/finance.yaml` (or `defaults.py`) and accessed via keys:

| Location | Magic Number | New Config Key | Default |
| :--- | :--- | :--- | :--- |
| `FinanceEngine.calculate_z_score` | `1.2`, `1.4`, `3.3`, `0.6` | `FINANCE_Z_SCORE_WEIGHTS` | (Dict or separate keys) |
| `FinanceEngine.check_solvency` | `1.81` (Distress Threshold) | `FINANCE_Z_SCORE_DISTRESS_THRESHOLD` | `1.81` |
| `FinanceEngine.check_solvency` | `2.99` (Safe Threshold) | `FINANCE_Z_SCORE_SAFE_THRESHOLD` | `2.99` |
| `Bank.calculate_interest` | `0.02` (Spread) | `BANK_INTEREST_SPREAD_DEFAULT` | `0.02` |

## 4. Implementation Plan

### Phase 1: Infrastructure
1.  **Update API**: Deploy `modules/system/api.py` with `IConfig` and `IConfigurationRegistry`.
2.  **Create Proxy**: Implement `ConfigProxy` in `modules/system/config_proxy.py`.
3.  **Setup Registry**: Ensure `modules/system/registry.py` implements `IConfigurationRegistry` and is initialized in `main.py`.

### Phase 2: Refactoring `FinanceEngine`
1.  **Inject Config**: Update `FinanceEngine.__init__` to accept `config: IConfig`.
2.  **Replace Constants**: Replace usage of `FINANCE_...` constants with `self.config.get(...)`.
3.  **Update Call Sites**: Update `SimController` or `Factory` to pass the config instance to `FinanceEngine`.

### Phase 3: Magic Number Clean-up
1.  **Extract**: Search for `if x < 1.81:` logic in `modules/finance/engine.py`.
2.  **Define**: Add keys to `config/defaults.py`.
3.  **Replace**: Use `self.config.get_float("FINANCE_Z_SCORE_DISTRESS_THRESHOLD")`.

## 5. Testing & Verification

### 5.1. Unit Testing `ConfigProxy`
- **Test**: `tests/modules/system/test_config_proxy.py`
- **Case**: Update registry value -> Verify Proxy reflects change immediately.

### 5.2. Integration Testing `FinanceEngine`
- **Fixture**: Use `mock_config` fixture that implements `IConfig`.
- **Scenario**:
    1.  Initialize `FinanceEngine` with mock config.
    2.  Set `FINANCE_Z_SCORE_DISTRESS_THRESHOLD` to `100.0` (Absurdly high).
    3.  Pass a healthy firm (Score `3.0`).
    4.  Assert firm is marked as `DISTRESSED` (proving logic used the dynamic `100.0` and not the hardcoded/default `1.81`).

### 5.3. Existing Test Impact
- **Risk**: `tests/modules/finance/test_finance_engine.py` instantiates `FinanceEngine`.
- **Mitigation**: Update `conftest.py` to provide a default `mock_config` to all engine tests.

## 6. Risk Audit

- **[Critical] Circular Dependency**: `ConfigProxy` must NOT import from `modules.simulation`. It should only depend on `modules.system.api`.
- **[High] Performance**: `config.get()` adds a dictionary lookup overhead to tight loops.
    - **Mitigation**: For extremely hot loops (millions of ops), cache the value in a local variable *outside* the loop, but inside the method scope.
- **[Medium] Type Safety**: `get()` returns `Any`.
    - **Mitigation**: Use `get_float()`, `get_int()` methods with type hints.

## 7. Mandatory Reporting
- Acknowledge creation of `communications/insights/wave5-config-purity.md`.
- Record any discovered "Ghost Bindings" (modules importing `config` at top level) in the report.
```
File: modules/system/api.py
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

# ... [Keep existing Context DTOs like MarketContextDTO, etc.] ...

# --- NEW PROTOCOLS FOR WAVE 3 ANALYTICS PURITY ---

@runtime_checkable
class ISnapshotProvider(Protocol):
    """
    Protocol for entities that can provide a full state snapshot for analytics.
    Resolves TD-ANALYTICS-DTO-BYPASS by removing direct attribute access.
    """
    def get_analytics_snapshot(self) -> "AgentAnalyticsSnapshotDTO":
        """
        Returns a standardized snapshot containing all data required for 
        telemetry and persistence. 
        """
        ...

# ... [Keep existing Registry protocols] ...
```

File: simulation/dtos/api.py
```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, TYPE_CHECKING, Union, TypedDict
from pydantic import BaseModel, Field, ConfigDict # Added for TD-UI-DTO-PURITY

# Import System types
from modules.system.api import CurrencyCode, AgentID

# ... [Keep existing imports] ...

# --- TELEMETRY DTOs (Converted to Pydantic for TD-UI-DTO-PURITY) ---

class BaseTelemetryModel(BaseModel):
    """Base Pydantic model for all telemetry data."""
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)
    run_id: int
    time: int

class TransactionData(BaseTelemetryModel):
    buyer_id: Optional[AgentID]
    seller_id: Optional[AgentID]
    item_id: str
    quantity: float
    price: float
    total_pennies: int
    currency: CurrencyCode
    market_id: str
    transaction_type: str

class AgentStateData(BaseTelemetryModel):
    agent_id: AgentID
    agent_type: str
    assets: Dict[CurrencyCode, int]
    is_active: bool
    generation: int = 0
    
    # Household Specific
    is_employed: Optional[bool] = None
    employer_id: Optional[AgentID] = None
    needs_survival: Optional[float] = None
    needs_labor: Optional[float] = None
    inventory_food: Optional[float] = None
    time_worked: Optional[float] = None
    time_leisure: Optional[float] = None
    
    # Firm Specific
    current_production: Optional[float] = None
    num_employees: Optional[int] = None
    
    # Common / New
    market_insight: Optional[float] = 0.5

class EconomicIndicatorData(BaseTelemetryModel):
    unemployment_rate: Optional[float] = None
    avg_wage: Optional[float] = None
    food_avg_price: Optional[float] = None
    food_trade_volume: Optional[float] = None
    avg_goods_price: Optional[float] = None
    total_production: Optional[float] = None
    total_consumption: Optional[int] = None
    total_household_assets: Optional[int] = None
    total_firm_assets: Optional[int] = None
    total_food_consumption: Optional[int] = None
    total_inventory: Optional[float] = None
    avg_survival_need: Optional[float] = None
    total_labor_income: Optional[int] = None
    total_capital_income: Optional[int] = None
    
    # Phase 23
    avg_education_level: Optional[float] = None
    education_spending: Optional[float] = None
    education_coverage: Optional[float] = None
    brain_waste_count: Optional[int] = None

class MarketHistoryData(BaseTelemetryModel):
    market_id: str
    item_id: Optional[str] = None
    avg_price: Optional[float] = None
    trade_volume: Optional[float] = None
    best_ask: Optional[float] = None
    best_bid: Optional[float] = None
    avg_ask: Optional[float] = None
    avg_bid: Optional[float] = None
    worst_ask: Optional[float] = None
    worst_bid: Optional[float] = None

# --- SNAPSHOT DTOs (Internal Dataclasses for Logic/Providers) ---

@dataclass(frozen=True)
class AgentAnalyticsSnapshotDTO:
    """
    Standardized snapshot returned by ISnapshotProvider.
    This serves as the bridge between internal Agent state and external Telemetry Pydantic models.
    """
    agent_id: AgentID
    agent_type: str
    is_active: bool
    assets: Dict[CurrencyCode, int]
    generation: int
    
    # Optional fields (populated based on agent type)
    inventory: Dict[str, float] = field(default_factory=dict)
    
    # Household Specific
    is_employed: Optional[bool] = None
    employer_id: Optional[AgentID] = None
    needs: Dict[str, float] = field(default_factory=dict)
    time_allocation: Dict[str, float] = field(default_factory=dict)
    
    # Firm Specific
    production_data: Dict[str, Any] = field(default_factory=dict)
    hr_data: Dict[str, Any] = field(default_factory=dict)
    
    market_insight: float = 0.5

# ... [Keep existing DecisionInputDTO, SimulationState, etc.] ...
```

File: design/3_work_artifacts/specs/wave3_analytics_purity_spec.md
```markdown
# Spec: Wave 3 Operational & Analytics Purity

## 1. Overview
This specification addresses the refactoring of the `AnalyticsSystem` to resolve Technical Debt items `TD-ANALYTICS-DTO-BYPASS` and `TD-UI-DTO-PURITY`. The goal is to decouple the analytics engine from concrete agent implementations and enforce strict typing at the I/O boundary using Pydantic.

## 2. Technical Debt Resolution
- **TD-ANALYTICS-DTO-BYPASS**: `AnalyticsSystem` currently inspects `WorldState` agents using `isinstance` and accesses attributes dynamically (`getattr`). This will be replaced by the `ISnapshotProvider` protocol.
- **TD-UI-DTO-PURITY**: UI Telemetry currently relies on `dataclasses`. This will be upgraded to `pydantic.BaseModel` to ensure serialization safety and schema validation.

## 3. Architecture & Design

### 3.1. Interfaces (`modules/system/api.py`)
New Protocol defined:
```python
class ISnapshotProvider(Protocol):
    def get_analytics_snapshot(self) -> AgentAnalyticsSnapshotDTO: ...
```

### 3.2. Data Transfer Objects (`simulation/dtos/api.py`)
- **Telemetry Models (Pydantic)**: `AgentStateData`, `TransactionData`, `EconomicIndicatorData`, `MarketHistoryData` become `pydantic.BaseModel`.
- **Internal Snapshot (Dataclass)**: `AgentAnalyticsSnapshotDTO` acts as the high-performance carrier from Agent to Analytics System.

### 3.3. Component Logic (`AnalyticsSystem`)

#### Logic Pseudo-code
```python
def aggregate_tick_data(self, world_state: WorldState) -> Tuple[List[AgentStateData], ...]:
    run_id = world_state.run_id
    time = world_state.time
    
    # 1. Agent State Aggregation via Protocol
    telemetry_list: List[AgentStateData] = []
    
    # Filter for providers
    providers = [
        a for a in world_state.agents.values() 
        if isinstance(a, ISnapshotProvider) and a.is_active
    ]
    
    for provider in providers:
        # PURE DATA EXTRACTION
        snapshot: AgentAnalyticsSnapshotDTO = provider.get_analytics_snapshot()
        
        # MAPPING TO PYDANTIC
        # Logic to map snapshot.needs['survival'] -> agent_dto.needs_survival
        # Logic to map snapshot.inventory['food'] -> agent_dto.inventory_food
        
        dto = AgentStateData(
            run_id=run_id,
            time=time,
            agent_id=snapshot.agent_id,
            ...
        )
        telemetry_list.append(dto)
        
    # 2. Transaction Aggregation
    # Direct mapping from Transaction DTO to Pydantic TransactionData
    
    # 3. Indicator Aggregation
    # Mapping from Tracker dicts to EconomicIndicatorData Pydantic model
    
    return telemetry_list, ...
```

### 3.4. Agent Updates
- **`Household`**: Must implement `ISnapshotProvider`. `get_analytics_snapshot` returns `AgentAnalyticsSnapshotDTO` populated from its internal state/config.
- **`Firm`**: Must implement `ISnapshotProvider`. `get_analytics_snapshot` returns `AgentAnalyticsSnapshotDTO` populated from `FirmStateDTO`.

## 4. Verification Plan

### 4.1. New Test Cases
- **Protocol Adherence**: Verify `Household` and `Firm` satisfy `ISnapshotProvider`.
- **Pydantic Serialization**: Verify `AgentStateData.model_dump_json()` works correctly.
- **Purity Check**: Verify `AnalyticsSystem` no longer imports `Household` or `Firm` concrete classes.

### 4.2. Impact Analysis
- **Existing Mocks**: Tests in `tests/systems/test_analytics_system.py` likely mock `WorldState.agents` with plain objects. These mocks MUST be updated to implement `get_analytics_snapshot`.
- **Performance**: The double-conversion (Agent -> SnapshotDTO -> Pydantic) adds overhead.
    - *Mitigation*: Agents should cache `AgentAnalyticsSnapshotDTO` if it was already generated for other systems in the same tick.

### 4.3. Risk Assessment
- **Critical**: Missing fields in `AgentAnalyticsSnapshotDTO` will cause data loss in the Dashboard.
- **Mitigation**: The mapping logic in `AnalyticsSystem` must cover 100% of the fields currently extracted via `getattr`.

### 4.4. Mandatory Ledger Audit
- **Resolved**: `TD-ANALYTICS-DTO-BYPASS`, `TD-UI-DTO-PURITY`
- **Created**: None anticipated, provided Protocol is strictly followed.
- **Note**: A report must be filed at `communications/insights/wave3-analytics-purity-spec.md`.
```
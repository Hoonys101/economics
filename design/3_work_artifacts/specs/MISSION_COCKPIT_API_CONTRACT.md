File: modules\governance\cockpit\api.py
```python
from __future__ import annotations
from enum import Enum
from typing import Dict, Any, List, Optional, Union, Literal
from pydantic import BaseModel, Field, conint, confloat

# ==============================================================================
# 1. Shared Enums & Types
# ==============================================================================

class CommandType(str, Enum):
    PAUSE = "PAUSE"
    RESUME = "RESUME"
    STEP = "STEP"
    SET_PARAM = "SET_PARAM"
    TRIGGER_SHOCK = "TRIGGER_SHOCK"

class ShockType(str, Enum):
    LIQUIDITY_CRISIS = "LIQUIDITY_CRISIS"  # Sudden withdrawal of liquidity
    SUPPLY_SHOCK = "SUPPLY_SHOCK"        # Production cost spike
    DEMAND_SHOCK = "DEMAND_SHOCK"        # Consumption drop
    TAX_HIKE = "TAX_HIKE"                # Fiscal contraction

class AgentType(str, Enum):
    HOUSEHOLD = "HOUSEHOLD"
    FIRM = "FIRM"
    GOVERNMENT = "GOVERNMENT"

# ==============================================================================
# 2. WebSocket Command Channel (Client -> Server)
# ==============================================================================

class BaseCommand(BaseModel):
    type: CommandType
    token: str = Field(..., description="God Mode Token for authentication")

class PauseCommand(BaseCommand):
    type: Literal[CommandType.PAUSE]

class ResumeCommand(BaseCommand):
    type: Literal[CommandType.RESUME]

class StepCommand(BaseCommand):
    type: Literal[CommandType.STEP]
    steps: int = Field(default=1, ge=1)

class SetParamCommand(BaseCommand):
    type: Literal[CommandType.SET_PARAM]
    param_key: str = Field(..., description="Dot-notation key (e.g. 'finance.base_rate')")
    value: Union[float, int, str, bool]

class TriggerShockCommand(BaseCommand):
    type: Literal[CommandType.TRIGGER_SHOCK]
    shock_type: ShockType
    magnitude: float = Field(..., ge=0.0, le=1.0, description="Severity 0.0-1.0")
    duration_ticks: int = Field(..., ge=1)

# Discriminated Union for Polymorphic Command Handling
CockpitCommand = Union[
    PauseCommand,
    ResumeCommand,
    StepCommand,
    SetParamCommand,
    TriggerShockCommand
]

# ==============================================================================
# 3. WebSocket Data Channel (Server -> Client)
# ==============================================================================

class IntegrityMetrics(BaseModel):
    m2_leak: int = Field(..., description="Total money leak in Pennies")
    fps: float = Field(..., description="Current simulation ticks per second")
    tick: int

class MacroMetrics(BaseModel):
    gdp: int = Field(..., description="Nominal GDP in Pennies")
    cpi: float = Field(..., description="Consumer Price Index (Base 100)")
    unemployment_rate: float = Field(..., ge=0.0, le=1.0)
    gini_index: float = Field(..., ge=0.0, le=1.0)

class FinanceMetrics(BaseModel):
    base_rate: float
    m2_supply: int
    velocity: float

class PoliticsMetrics(BaseModel):
    approval_rating: float = Field(..., ge=0.0, le=100.0)
    ruling_party: str
    tax_revenue: int

class PopulationMetrics(BaseModel):
    active_population: int
    birth_rate: float
    death_rate: float
    quintile_wealth: List[float] = Field(..., min_items=5, max_items=5)

class WatchtowerSnapshotResponse(BaseModel):
    """
    Complete system snapshot sent via WebSocket /ws/live.
    """
    timestamp: float
    integrity: IntegrityMetrics
    macro: MacroMetrics
    finance: FinanceMetrics
    politics: PoliticsMetrics
    population: PopulationMetrics

# ==============================================================================
# 4. REST Inspector Endpoint (Server -> Client)
# ==============================================================================

class InventoryItem(BaseModel):
    item_id: str
    quantity: float
    avg_cost: float

class DecisionLogEntry(BaseModel):
    tick: int
    module: str
    action: str
    reasoning: str
    outcome_score: Optional[float] = None

class AgentInspectorResponse(BaseModel):
    agent_id: int
    type: AgentType
    is_alive: bool
    wallet_balance: Dict[str, int]
    inventory: List[InventoryItem]
    decision_log: List[DecisionLogEntry]
    stress_level: float = Field(..., ge=0.0, le=1.0)
    # Household Specific
    employer_id: Optional[int] = None
    # Firm Specific
    employees_count: Optional[int] = None

# ==============================================================================
# 5. REST Genealogy Endpoint (Server -> Client)
# ==============================================================================

class AgentSurvivalData(BaseModel):
    agent_id: int
    generation: int
    birth_tick: int
    death_tick: Optional[int]
    peak_wealth: int
    cause_of_death: Optional[str]
    initial_traits: Dict[str, float] # e.g. {"risk_tolerance": 0.5}

class GenealogyResponse(BaseModel):
    dataset: List[AgentSurvivalData]
    total_records: int
```

File: design\3_work_artifacts\specs\MISSION_COCKPIT_API_CONTRACT.md
```markdown
# Spec: Cockpit 2.0 API Contract (Wire Protocol)

## 1. Executive Summary
This specification defines the strict API contract between the Simulation Backend (FastAPI) and the Cockpit 2.0 Frontend (React). It replaces the legacy `asdict` serialization and loose dictionary commands with Pydantic-enforced schemas. This change addresses **TD-UI-DTO-PURITY** and enables type-safe integration for the upcoming "Agent Inspector" and "Genealogy" features.

## 2. API Contract & Schemas

### 2.1. WebSocket: Live Telemetry (`/ws/live`)
- **Direction**: Server → Client
- **Frequency**: 1Hz (Throttled)
- **Schema**: `WatchtowerSnapshotResponse` (Defined in `modules/governance/cockpit/api.py`)
- **Transport**: JSON Text

#### TypeScript Interface (Draft)
```typescript
export interface WatchtowerSnapshot {
  timestamp: number;
  integrity: {
    m2_leak: number;
    fps: number;
    tick: number;
  };
  macro: {
    gdp: number;
    cpi: number;
    unemployment_rate: number;
    gini_index: number;
  };
  // ... other sections map 1:1 to Pydantic
}
```

### 2.2. WebSocket: Command Channel (`/ws/command`)
- **Direction**: Client → Server
- **Authentication**: Header `X-GOD-MODE-TOKEN` required.
- **Schema**: `CockpitCommand` (Discriminated Union)
- **Validation**: Strict parsing via `TypeAdapter(CockpitCommand).validate_json(payload)`.

#### Example Payload (Set Parameter)
```json
{
  "type": "SET_PARAM",
  "token": "god_mode_123",
  "param_key": "finance.central_bank.base_rate",
  "value": 0.05
}
```

### 2.3. REST: Agent Inspector (`GET /api/v1/inspector/{agent_id}`)
- **Purpose**: detailed "System 2" debugging of a specific agent.
- **Response**: `AgentInspectorResponse`
- **Data Source**: `IAgentRepository` + `DecisionLog` (Memory Module).

#### Logic (Pseudo-code)
```python
@app.get("/api/v1/inspector/{agent_id}", response_model=AgentInspectorResponse)
def get_agent_details(agent_id: int, repo: AgentRepository = Depends(get_repo)):
    agent = repo.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Map Internal State to Contract DTO
    return AgentInspectorResponse(
        agent_id=agent.id,
        type=agent.type,
        is_alive=agent.is_alive,
        wallet_balance=agent.inventory.wallet,
        inventory=[
            InventoryItem(item_id=k, quantity=v, avg_cost=0.0) 
            for k, v in agent.inventory.goods.items()
        ],
        decision_log=fetch_decision_history(agent.id), # From Memory/Logs
        stress_level=agent.metrics.stress
    )
```

### 2.4. REST: Genealogy (`GET /api/v1/genealogy`)
- **Purpose**: Scatter plot data for "Nature vs Nurture" analysis.
- **Response**: `GenealogyResponse`
- **Query Params**: `limit: int = 1000`, `min_generation: int = 0`

## 3. Verification Plan

### 3.1. Testing Strategy
- **Contract Tests**: Verify that `pydantic` models correctly validate valid JSON and reject invalid JSON (e.g., missing fields, wrong types).
- **Integration Tests**: Refactor `tests/integration/test_cockpit_integration.py` to use the new `CockpitCommand` objects instead of raw dicts.
- **Zero-Sum Audit**: Verify `TriggerShockCommand` logic in the backend ensures any monetary shock is accounted for (e.g., strictly strictly transferring from `SystemTreasury` or logging as explicit Injection).

### 3.2. Mocking Guide
- Use `MagicMock(spec=WatchtowerSnapshotResponse)` for testing the WebSocket broadcaster.
- Do **NOT** use raw dicts in tests. Instantiate the Pydantic models.

## 4. Risk & Impact Audit

### 4.1. Technical Debt
- **Resolves TD-UI-DTO-PURITY**: Eliminates manual `asdict` calls.
- **Risk**: Existing frontend code expects the old `WatchtowerSnapshotDTO` structure. This is a **Breaking Change**. Frontend update is required synchronously.

### 4.2. Performance
- **Validation Overhead**: Pydantic validation adds CPU overhead.
- **Mitigation**: Command channel is low frequency (human speed). Telemetry channel is high frequency (1Hz); `WatchtowerSnapshotResponse` construction should be optimized.

### 4.3. Security
- **Command Injection**: Strict typing prevents arbitrary payload injection.
- **Auth**: `BaseCommand` enforces `token` presence in the payload (double-check with header auth).

## 5. Mandatory Reporting
> The following file MUST be created/updated with insights from this specification work:
> `communications/insights/spec-cockpit-api-contract.md`

```markdown
# Insight Report: Cockpit 2.0 API Contract

## 1. Architectural Decisions
- **Discriminated Unions**: Adopted for Commands to ensure strict type safety based on `type` field.
- **Pydantic V2**: Leveraging strict mode for `conint` and `confloat` to prevent logic errors (e.g., negative tax rates).

## 2. Technical Debt Addressal
- **TD-UI-DTO-PURITY**: Resolved by introducing `modules/governance/cockpit/api.py` with Pydantic models.
- **Observation**: Current `server.py` WebSocket logic is too coupled to `DashboardService`. Future refactor should inject a `TelemetryProvider` protocol.

## 3. Risks
- **Frontend Sync**: The React frontend `types/dashboard.ts` must be manually updated to match these Pydantic models until a generator (e.g., `datamodel-code-generator`) is integrated into the build pipeline.
```
```

File: communications\insights\spec-cockpit-api-contract.md
```markdown
# Insight Report: Cockpit 2.0 API Contract

## 1. Architectural Decisions
- **Discriminated Unions**: Adopted for Commands to ensure strict type safety based on `type` field. This allows the backend to automatically route commands to specific handlers based on the schema validation result.
- **Pydantic V2**: Leveraging strict mode for `conint` and `confloat` to prevent logic errors (e.g., negative tax rates, negative step counts).
- **Separation of Concerns**: The API contract is isolated in `modules/governance/cockpit/api.py`, decoupling the wire protocol from the internal simulation DTOs (`simulation/dtos`). This allows the internal model to evolve without immediately breaking the external API (via an adapter layer).

## 2. Technical Debt Addressal
- **TD-UI-DTO-PURITY**: Resolved by introducing strict Pydantic models. This eliminates the risk of `asdict` leaking internal state or non-serializable objects (like `MagicMock` or functions) to the JSON serializer.
- **Observation**: Current `server.py` WebSocket logic is too coupled to `DashboardService`. Future refactor should inject a `TelemetryProvider` protocol to allow for easier testing and mocking of the data stream.

## 3. Risks
- **Frontend Sync**: The React frontend `types/dashboard.ts` must be manually updated to match these Pydantic models until a generator (e.g., `datamodel-code-generator`) is integrated into the build pipeline.
- **Performance**: Pydantic validation on the high-frequency telemetry channel (1Hz) is acceptable, but if frequency increases, we may need to optimize serialization.
```
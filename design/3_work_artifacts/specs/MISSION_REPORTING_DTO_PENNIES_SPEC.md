# Specification Draft: Reporting DTO Penny-Hardening

## 1. simulation/dtos/api.py

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, TYPE_CHECKING, Union, TypedDict
from modules.simulation.dtos.api import FirmStateDTO, HouseholdConfigDTO, FirmConfigDTO
from simulation.models import Order
from simulation.dtos.decision_dtos import DecisionOutputDTO
from modules.finance.api import IFinancialAgent
from modules.simulation.api import AgentID, EconomicIndicatorsDTO
from modules.governance.api import SystemCommand
from simulation.dtos.commands import GodCommandDTO
from modules.system.api import (
    CurrencyCode,
    MarketSnapshotDTO,
    HousingMarketSnapshotDTO,
    LoanMarketSnapshotDTO,
    LaborMarketSnapshotDTO,
    HousingMarketUnitDTO,
    MarketContextDTO
)

# Alias for standardization
OrderDTO = Order

if TYPE_CHECKING:
    from simulation.core_agents import Household
    from simulation.firms import Firm
    from simulation.dtos.scenario import StressScenarioConfig
    from modules.household.dtos import HouseholdStateDTO

@dataclass
class TransactionData:
    """
    Immutable record of a standardized transaction.
    Penny-Hardened: 'total_pennies' is the Source of Truth.
    """
    run_id: int
    time: int
    buyer_id: AgentID
    seller_id: AgentID
    item_id: str
    quantity: float
    total_pennies: int  # SSoT: Integer Pennies
    market_id: str
    transaction_type: str
    currency: CurrencyCode
    price_display: float = 0.0  # DEPRECATED: For display only (total_pennies / quantity / 100)

@dataclass
class AgentStateData:
    """
    Snapshot of an Agent's state at a specific tick.
    """
    run_id: int
    time: int
    agent_id: AgentID
    agent_type: str
    assets: Dict[CurrencyCode, int]  # Hardened: Integer Pennies
    is_active: bool
    is_employed: Optional[bool] = None
    employer_id: Optional[AgentID] = None
    needs_survival: Optional[float] = None
    needs_labor: Optional[float] = None
    inventory_food: Optional[float] = None
    current_production: Optional[float] = None
    num_employees: Optional[int] = None
    education_xp: Optional[float] = None
    generation: Optional[int] = 0
    time_worked: Optional[float] = None
    time_leisure: Optional[float] = None

@dataclass
class EconomicIndicatorData:
    """
    Aggregated Economic Indicators.
    Financial aggregations MUST be in Integer Pennies.
    """
    run_id: int
    time: int
    # Financial Aggregates (Integer Pennies)
    total_household_assets: Optional[int] = None
    total_firm_assets: Optional[int] = None
    total_labor_income: Optional[int] = None
    total_capital_income: Optional[int] = None
    
    # Statistical / Rate Indicators (Float)
    unemployment_rate: Optional[float] = None
    avg_wage: Optional[float] = None
    food_avg_price: Optional[float] = None
    food_trade_volume: Optional[float] = None
    avg_goods_price: Optional[float] = None
    total_production: Optional[float] = None
    total_consumption: Optional[float] = None
    total_food_consumption: Optional[float] = None
    total_inventory: Optional[float] = None
    avg_survival_need: Optional[float] = None
    
    # Phase 23: Education
    avg_education_level: Optional[float] = None
    education_spending: Optional[float] = None
    education_coverage: Optional[float] = None
    brain_waste_count: Optional[int] = None

@dataclass
class MarketHistoryData:
    """
    Market Statistics for a specific tick.
    Discrete price points are Integers (Pennies).
    Averages remain Floats.
    """
    time: int
    market_id: str
    item_id: Optional[str] = None
    trade_volume: Optional[float] = None
    
    # Discrete Signal Points (Integers)
    best_ask: Optional[int] = None
    best_bid: Optional[int] = None
    worst_ask: Optional[int] = None
    worst_bid: Optional[int] = None
    
    # Calculated Averages (Floats)
    avg_price: Optional[float] = None
    avg_ask: Optional[float] = None
    avg_bid: Optional[float] = None

@dataclass
class AIDecisionData:
    run_id: int
    tick: int
    agent_id: AgentID
    decision_type: str
    decision_details: Optional[Dict[str, Any]] = None
    predicted_reward: Optional[float] = None
    actual_reward: Optional[float] = None

# --- TypedDicts for JSON Serialization/Interface ---

class GoodsDTO(TypedDict, total=False):
    id: str
    name: str
    category: str
    is_durable: bool
    is_essential: bool
    initial_price: int
    base_need_satisfaction: float
    quality_modifier: float
    type: str
    satiety: float
    decay_rate: float

class MarketHistoryDTO(TypedDict, total=False):
    """
    TypedDict alignment with MarketHistoryData.
    """
    avg_price: float
    trade_volume: float
    best_ask: int
    best_bid: int
    avg_ask: float
    avg_bid: float
    worst_ask: int
    worst_bid: int

@dataclass
class GovernmentPolicyDTO:
    income_tax_rate: float
    sales_tax_rate: float
    corporate_tax_rate: float
    base_interest_rate: float

@dataclass
class DecisionInputDTO:
    market_snapshot: MarketSnapshotDTO
    goods_data: List[Dict[str, Any]]
    market_data: Dict[str, Any]
    current_time: int
    fiscal_context: Optional[FiscalContext] = None
    macro_context: Optional[MacroFinancialContext] = None
    stress_scenario_config: Optional[Any] = None
    government_policy: Optional[GovernmentPolicyDTO] = None
    agent_registry: Optional[Dict[str, int]] = None
    housing_system: Optional[Any] = None
    market_context: Optional[MarketContextDTO] = None

@dataclass
class DecisionContext:
    goods_data: List[GoodsDTO]
    market_data: Dict[str, MarketHistoryDTO]
    current_time: int
    state: Union[HouseholdStateDTO, FirmStateDTO]
    config: Union[HouseholdConfigDTO, FirmConfigDTO]
    market_snapshot: Optional[MarketSnapshotDTO] = None
    government_policy: Optional[GovernmentPolicyDTO] = None
    stress_scenario_config: Optional[StressScenarioConfig] = None
    agent_registry: Dict[str, AgentID] = field(default_factory=dict)
    market_context: Optional[MarketContextDTO] = None

@dataclass
class FiscalContext:
    government: IFinancialAgent

@dataclass
class SimulationState:
    # ... (Existing fields, truncated for brevity as they are unchanged)
    time: int
    households: List[Household]
    firms: List[Firm]
    agents: Dict[AgentID, Any]
    # ...
    # Simplified for draft context
    pass
```

## 2. design/3_work_artifacts/specs/reporting_penny_hardening_spec.md

```markdown
# Spec: Reporting DTO Penny-Hardening

## 1. Overview
This specification mandates the strict adoption of Integer (Penny) types for all financial fields within Reporting DTOs. It addresses the architectural risk of floating-point drift during data aggregation and persistence. It explicitly decouples the `AnalyticsSystem` from the legacy, float-based `Tracker` for asset aggregation.

## 2. Scope
- **Target Components**: `AnalyticsSystem`, `EconomicIndicatorData`, `MarketHistoryData`, `TransactionData`.
- **Excluded**: `Tracker` internal logic (Phase 2 refactor).

## 3. Data Structure Changes

### 3.1. `MarketHistoryData` (Type Refinement)
- **Goal**: Align discrete market signals with the Order Book's native integer precision.
- **Changes**:
  - `best_ask`: `float` -> `Optional[int]`
  - `best_bid`: `float` -> `Optional[int]`
  - `worst_ask`: `float` -> `Optional[int]`
  - `worst_bid`: `float` -> `Optional[int]`
  - `avg_price`: Remains `float` (calculated).

### 3.2. `TransactionData` (Deprecation & Hardening)
- **Goal**: Establish `total_pennies` as the SSoT for settlement reporting.
- **Changes**:
  - `price` (float) -> Renamed to `price_display`. DEPRECATED.
  - `total_pennies` (int) -> Primary field for financial auditing.
  - **Constraint**: `Transaction` object creation must ensure `total_pennies` is populated from the Settlement Engine.

### 3.3. `EconomicIndicatorData` (Aggregation Source)
- **Goal**: Ensure global asset sums are exact integers.
- **Changes**:
  - No schema changes needed (fields are already `int` per context), but **Population Logic** must change.

## 4. Logic Updates: `AnalyticsSystem`

### 4.1. Asset Aggregation Hardening
- **Current (Legacy)**:
  ```python
  hh_assets = tracker.get("total_household_assets") # returns float
  hh_assets_val = int(hh_assets) # UNSAFE CAST
  ```
- **New (Hardened)**:
  - Iterate directly over `world_state.agents` (or filtered lists `households`, `firms`).
  - Use `agent.get_assets_by_currency()[DEFAULT_CURRENCY]` (which returns `int`).
  - **Pseudo-code**:
    ```python
    total_hh_assets = 0
    for h in world_state.households:
        if isinstance(h, ICurrencyHolder):
            total_hh_assets += h.get_assets_by_currency().get(DEFAULT_CURRENCY, 0)
    ```

### 4.2. Market History Population
- **Logic**: When constructing `MarketHistoryData`, retrieve `best_bid`/`best_ask` from `MarketSnapshotDTO` (which should already be `int` per `MarketSignalDTO` definition) instead of calculating from float averages.

## 5. Technical Debt & Risk Analysis (Mandatory Ledger Audit)

### 5.1. Impact on Existing Debt
- **Resolves `TD-TRANS-INT-SCHEMA`**: Explicitly fixes the float price issue in Reporting DTOs.
- **Mitigates `TD-UI-DTO-PURITY`**: Enforces strict typing, reducing reliance on implicit float conversions in the UI layer.

### 5.2. New Risks
- **Frontend Compatibility**: The Dashboard UI might expect `price` in `TransactionData`.
  - **Mitigation**: The renamed `price_display` or a computed property `price` returning `total_pennies / quantity / 100.0` can serve as a bridge.
- **Tracker Drift**: Discrepancy between `AnalyticsSystem` (Int) and `Tracker` (Float) might confuse users if both are displayed.
  - **Decision**: `AnalyticsSystem` is the SSoT for persistent history. `Tracker` is for runtime heuristics.

## 6. Verification Plan

### 6.1. Protocol Compliance Test
- **Test**: `test_analytics_aggregation_purity`
- **Setup**: Mock Agents implementing `ICurrencyHolder`.
- **Action**: Run `aggregate_tick_data`.
- **Assertion**:
  - `EconomicIndicatorData.total_household_assets` equals sum of Mock Agents' penny balances exactly.
  - `MarketHistoryData.best_ask` is an `int` (type check).

### 6.2. Deprecation Check
- **Test**: `test_transaction_dto_deprecation`
- **Action**: Instantiate `TransactionData`.
- **Assertion**: Accessing `price` should ideally warn (if property used) or field should be absent.

### 6.3. Golden Data
- Use `fixtures/golden_households.json` to verify asset loading into `EconomicIndicatorData`.

## 7. Mandatory Reporting
- A detailed insight report has been generated at: `communications/insights/spec-reporting-dto-pennies.md`
```

## 3. communications/insights/spec-reporting-dto-pennies.md

```markdown
# Insight Report: Reporting DTO Penny-Hardening

## 1. Architectural Decisions
- **Decoupling from Tracker**: The `AnalyticsSystem` was previously dependent on `world_state.tracker` for asset aggregation. This introduced a "Float-contamination" risk where integer assets were converted to floats for tracking, then cast back to ints for reporting. The new spec mandates direct aggregation from Agents using the `ICurrencyHolder` protocol.
- **Discrete Market Signals**: `MarketHistoryData` treated `best_bid`/`best_ask` as floats. Since these represent specific orders in the Order Book, they must be Integers (Pennies). This change aligns the reporting layer with the `MatchingEngine`.

## 2. Technical Debt Identified
- **Tracker Obsolescence**: The `Tracker` class operates on floats and is becoming a legacy artifact. Future refactoring should replace `Tracker` internal logic with the same Integer-based aggregation used in `AnalyticsSystem`.
- **DTO Duplication**: `MarketHistoryDTO` (TypedDict) and `MarketHistoryData` (Dataclass) existed with conflicting type definitions (`int` vs `float`). This spec unifies them.

## 3. Risks & Mitigations
- **UI Breakage**: Frontend components consuming `TransactionData.price` will break.
  - **Mitigation**: A temporary property or `price_display` field is included, but marked DEPRECATED.
- **Performance**: Iterating all agents for aggregation in Python might be slower than maintaining a running total.
  - **Mitigation**: Acceptable for current scale (N < 10,000). Future optimization can use `Registry` listeners (Observer Pattern) to maintain running Integer sums.

## 4. Test Evidence Requirement
(To be filled during Implementation Phase)
- `test_analytics_purity.py` results must prove 0-penny drift.
```
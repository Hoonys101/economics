# Structural Audit Report: AUDIT-STRUCTURAL

**Date**: 2024-05-23
**Task ID**: AUDIT-STRUCTURAL
**Auditor**: Jules

## 1. Executive Summary

This audit identified critical structural issues in the `simulation` module, specifically concerning "God Classes" and "Abstraction Leaks" in the decision-making pipeline. The `Household` class has exceeded the line limit threshold, becoming a maintenance bottleneck. Furthermore, raw market objects are leaking into agent decision phases via `DecisionInputDTO`, violating the "Purity Gate" architecture.

## 2. God Class Analysis

### 2.1 Household Agent (`simulation/core_agents.py`)
- **Status**: **SATURATED (God Class)**
- **Size**: Approx. **1037 lines** (Threshold: 800 lines).
- **Findings**:
  - The `Household` class functions as a massive facade, orchestrating Bio, Econ, and Social components.
  - While it delegates logic to components (`BioComponent`, `EconComponent`, etc.), the facade itself contains significant glue code, property overrides, and orchestration logic.
  - It handles `make_decision`, `update_needs`, `consume`, `clone`, and legacy compatibility methods all in one place.
- **Recommendation**:
  - **Decomposition**: Urgent need to further decompose `Household`.
  - **Strategy**:
    - Move `clone` logic to a `HouseholdFactory` or `LifecycleManager`.
    - Move `make_decision` orchestration logic entirely to `DecisionUnit` (it is partially there, but the facade still does significant DTO prep).
    - Remove legacy compatibility properties if possible.

### 2.2 Firm Agent (`simulation/firms.py`)
- **Status**: **SAFE**
- **Size**: Approx. 430 lines.
- **Findings**:
  - The `Firm` class is within acceptable limits.
  - It delegates well to `HRDepartment`, `FinanceDepartment`, etc.

## 3. Abstraction Leak Analysis

### 3.1 Raw Market Access in `Household.make_decision`
- **Location**: `simulation/core_agents.py` inside `make_decision`.
- **Violation**:
  ```python
  # Housing Snapshot
  housing_market_obj = markets.get("housing")
  if housing_market_obj and hasattr(housing_market_obj, "sell_orders"):
       # ... accesses raw sell_orders ...
  ```
- **Impact**: The agent directly inspects the raw `OrderBookMarket` object to build a snapshot. This couples the agent to the specific implementation of the market.
- **Corrective Action**:
  - Move this logic to `MarketSnapshotFactory` in the orchestrator.
  - The `DecisionInputDTO` should receive a pre-built `MarketSnapshotDTO`.

### 3.2 Raw Market Access in `Firm.make_decision`
- **Location**: `simulation/firms.py` inside `_calculate_invisible_hand_price`.
- **Violation**:
  ```python
  def _calculate_invisible_hand_price(self, markets: Dict[str, Any], current_tick: int) -> None:
      market = markets.get(self.specialization)
      # ...
      bids = market.get_all_bids(self.specialization)
  ```
- **Impact**: The firm accesses raw market methods (`get_all_bids`) during its decision phase (even if technically "shadow mode").
- **Corrective Action**:
  - Calculate `excess_demand_signal` in the Market System before the decision phase.
  - Pass this signal via `MarketSnapshotDTO.market_signals`.

### 3.3 Root Cause: `DecisionInputDTO`
- **Location**: `simulation/dtos/api.py`.
- **Finding**:
  ```python
  @dataclass
  class DecisionInputDTO:
      markets: Dict[str, Any]  # <--- THE LEAK
      # ...
  ```
- **Impact**: The presence of `markets` in the input DTO invites usage.
- **Corrective Action**:
  - **Remove `markets`** from `DecisionInputDTO`.
  - Ensure all necessary data is available in `market_snapshot` or `market_data`.

## 4. Remediation Plan (Prioritized)

1.  **Stop the Bleeding**: Remove `markets` from `DecisionInputDTO` to prevent future leaks. This will break existing code (`Household`, `Firm`), forcing immediate refactoring.
2.  **Refactor Household Decision Prep**: Move `HousingMarketSnapshotDTO` creation to `MarketSnapshotFactory`.
3.  **Refactor Firm Shadow Price**: Move "Invisible Hand" calculation to a system-level service or pre-calculate signals in `Market`.
4.  **Household Decomposition**: Schedule a dedicated task to reduce `Household` class size, focusing on extracting Lifecycle and Factory logic.

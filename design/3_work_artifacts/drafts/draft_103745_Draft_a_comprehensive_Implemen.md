# Implementation Specification: Phase 28 - The Great Moderator

## 1. Executive Overview

This document provides the detailed implementation plan for Phase 28, "The Great Moderator." The primary objective is to introduce automatic stabilizers into the simulation's economy to dampen boom-bust cycles and enable "soft landings." This will be achieved by refactoring the government entity and introducing sophisticated fiscal and monetary policy managers.

**CRITICAL**: This specification is designed for the **future architecture** defined in `design/3_work_artifacts/specs/GOD_FILE_DECOMPOSITION_SPEC.md`. All implementation must align with the post-refactoring state of `TD-140`, `TD-141`, and `TD-142`.

---

## 2. Work Order Breakdown & Implementation Plan

### **WO-144: Government Structure Refactor**

**Objective**: Decompose the monolithic government entity into a modern Facade/Component structure, following the `Household` agent refactoring precedent.

#### 2.1. New Module Structure

A new module `modules/government` will be created.

```
modules/
└── government/
    ├── api.py
    ├── government_agent.py
    ├── components/
    │   ├── fiscal_policy_manager.py
    │   └── monetary_policy_manager.py
    └── dtos.py
```

#### 2.2. API and DTO Definition (`modules/government/api.py`)

This file will define the public interface for the government module.

```python
# modules/government/api.py
from __future__ import annotations
from typing import TypedDict, List, Protocol
from dataclasses import dataclass

# === Data Transfer Objects ===

@dataclass
class TaxBracketDTO:
    """Defines a single progressive tax bracket."""
    floor: float
    rate: float
    ceiling: float | None # None for the highest bracket

@dataclass
class FiscalPolicyDTO:
    """State of the current fiscal policy."""
    progressive_tax_brackets: List[TaxBracketDTO]
    # TBD: Other fiscal tools like subsidies, welfare
    
@dataclass
class MonetaryPolicyDTO:
    """State of the current monetary policy."""
    target_interest_rate: float
    inflation_target: float
    unemployment_target: float
    # TBD: QE/QT parameters

@dataclass
class GovernmentStateDTO:
    """The complete state of the Government agent."""
    id: int
    assets: float
    fiscal_policy: FiscalPolicyDTO
    monetary_policy: MonetaryPolicyDTO

# === Component Interfaces ===

class IFiscalPolicyManager(Protocol):
    """Interface for managing the government's fiscal policy."""
    
    def determine_fiscal_stance(self, market_snapshot: "MarketSnapshotDTO") -> FiscalPolicyDTO:
        """Adjusts tax brackets based on economic conditions."""
        ...

    def calculate_tax_liability(self, policy: FiscalPolicyDTO, income: float) -> float:
        """Calculates the tax owed based on a progressive bracket system."""
        ...

class IMonetaryPolicyManager(Protocol):
    """Interface for managing the government's monetary policy (Central Bank)."""

    def determine_monetary_stance(self, market_snapshot: "MarketSnapshotDTO") -> MonetaryPolicyDTO:
        """Adjusts the target interest rate based on a Taylor-like rule."""
        ...

# === Facade Class (for type hinting) ===
class Government(Protocol):
    """Facade for the government agent."""
    state: GovernmentStateDTO

    def make_policy_decision(self, market_snapshot: "MarketSnapshotDTO") -> None:
        ...
```

### **WO-145: Progressive Tax System (Fiscal Policy)**

**Objective**: Implement a progressive tax system as an automatic stabilizer.

#### 2.3. Fiscal Policy Manager (`modules/government/components/fiscal_policy_manager.py`)

This component will be stateless and operate on DTOs.

```python
# modules/government/components/fiscal_policy_manager.py

class FiscalPolicyManager:
    """Implements fiscal policy logic."""

    def determine_fiscal_stance(self, market_snapshot: "MarketSnapshotDTO") -> FiscalPolicyDTO:
        """
        Pseudo-code:
        1. Analyze market_snapshot for GDP growth, inflation.
        2. IF economy is overheating (high inflation/growth):
        3.   Optionally, make tax brackets slightly more aggressive (TBD).
        4. ELIF economy is in recession (low/negative growth):
        5.   Optionally, make tax brackets more lenient (TBD).
        6. ELSE:
        7.   Return default progressive tax brackets.
        8. RETURN new FiscalPolicyDTO.
        """
        # For now, returns a static policy. Dynamic adjustment is a future task.
        default_brackets = [
            TaxBracketDTO(floor=0, rate=0.10, ceiling=20000),
            TaxBracketDTO(floor=20000, rate=0.25, ceiling=80000),
            TaxBracketDTO(floor=80000, rate=0.40, ceiling=None),
        ]
        return FiscalPolicyDTO(progressive_tax_brackets=default_brackets)

    def calculate_tax_liability(self, policy: FiscalPolicyDTO, income: float) -> float:
        """
        Pseudo-code:
        1. total_tax = 0
        2. remaining_income = income
        3. FOR bracket in policy.progressive_tax_brackets:
        4.   IF income > bracket.floor:
        5.     taxable_in_bracket = min(income, bracket.ceiling or income) - bracket.floor
        6.     total_tax += taxable_in_bracket * bracket.rate
        7. RETURN total_tax
        """
        # ... implementation ...
        pass
```

**Integration Point**: The `TaxAgency` will use `FiscalPolicyManager.calculate_tax_liability`. This requires a `GOVERNMENT_PHASE` in the `TickScheduler` to run before the `TAX_COLLECTION_PHASE`, ensuring the policy is set for the current tick.

### **WO-146: Monetary Policy & Taylor Rule**

**Objective**: Implement a Taylor Rule-based monetary policy to manage inflation and employment.

#### 2.4. Monetary Policy Manager (`modules/government/components/monetary_policy_manager.py`)

This component will be stateless and operate on DTOs.

```python
# modules/government/components/monetary_policy_manager.py

class MonetaryPolicyManager:
    """Implements monetary policy logic via a Taylor Rule."""

    def determine_monetary_stance(self, market_snapshot: "MarketSnapshotDTO") -> MonetaryPolicyDTO:
        """
        Calculates the target interest rate using a Taylor-like rule.
        
        Pseudo-code:
        1. Get current inflation and unemployment from market_snapshot.
        2. Define targets: inflation_target=2.0%, unemployment_target=5.0%.
        3. Define neutral_rate = 2.0%.
        4. inflation_gap = current_inflation - inflation_target
        5. unemployment_gap = current_unemployment - unemployment_target
        
        6. # Taylor Rule Formula
        7. target_rate = neutral_rate + (0.5 * inflation_gap) - (0.5 * unemployment_gap)
        8. target_rate = max(0.01, target_rate) # Ensure non-negative
        
        9. RETURN MonetaryPolicyDTO(
               target_interest_rate=target_rate,
               inflation_target=inflation_target,
               unemployment_target=unemployment_target
           )
        """
        # ... implementation ...
        pass
```
**Integration Point**: The `LoanMarket` and firm financing decisions (the *new* `finance_manager.py` from `TD-142`) will use this `target_interest_rate` as the base rate. This requires the `GOVERNMENT_PHASE` to run before agent financial decisions.

### **WO-147: Soft Landing Verification**

**Objective**: Create a new verification suite to prove the effectiveness of the stabilizers. This replaces previous behavioral tests that are now invalid.

#### 2.5. Verification Plan

1.  **Create New Script**: `scripts/verify_soft_landing.py`.
2.  **Baseline Scenario**:
    *   Run a 1000-tick simulation with the new stabilizers **disabled** (e.g., via a config flag that sets a flat tax and fixed interest rate).
    *   Record key metrics: GDP, inflation, unemployment, Gini coefficient.
    *   Calculate volatility (standard deviation) for each metric.
    *   Count the number and duration of recessions (e.g., 2 consecutive ticks of negative GDP growth).
    *   Save results to `reports/soft_landing_baseline.json`.
3.  **Stabilizer Scenario**:
    *   Run the same 1000-tick simulation with stabilizers **enabled**.
    *   Record the same metrics.
    *   Calculate volatility and recession count.
    *   Save results to `reports/soft_landing_stabilized.json`.
4.  **Verification**:
    *   The test passes if:
        *   GDP volatility is reduced by at least 25%.
        *   Inflation volatility is reduced by at least 25%.
        *   The number of recessionary periods is reduced.
    *   Generate comparison plots (`gdp_volatility.png`, `inflation_stability.png`).

---

## 3. Risk & Impact Audit (Addressing Pre-flight Check)

-   **`TD-140/141/142` Dependency**: This entire plan is contingent on the God File decomposition. **Parallel Checkpoints** must be established.
    -   **Checkpoint 1 (API Alignment)**: Before full implementation, the `api.py` files for the new policy and data modules must be finalized and agreed upon.
    -   **Checkpoint 2 (Integration)**: As the refactored components (`consumption_manager`, `finance_manager`, `agent_repository`) become available, they must be integrated into the new policy managers' logic, replacing any temporary mock interfaces.
-   **Architectural Purity**:
    -   **Phased Execution**: A new phase, `Phase.GOVERNMENT_POLICY`, will be added to the `TickScheduler` sequence, executing after market data is aggregated and before `Phase.HOUSEHOLD_DECISIONS`.
    -   **DTO-Only Flow**: The `TickScheduler` will be responsible for calling the `Government.make_policy_decision` method, passing the `MarketSnapshotDTO`. The resulting `GovernmentStateDTO` will be added to the context for subsequent phases. There will be **no direct calls** between agents and the government.
-   **Test Suite Invalidation**: All previous scenario tests (`verify_golden_age.py`, etc.) are considered **deprecated**. They will be replaced by `verify_soft_landing.py`. This is an accepted and planned consequence of introducing stabilizers.

---

## 4. Mandatory Reporting & Mocking Strategy

-   **Jules' Insights**: All work on these WOs must log insights and identified technical debt to `communications/insights/WO-XXX.md`.
-   **Golden Data & Mocks**:
    -   A `golden_government_state.json` fixture will be created.
    -   During development, while `TD-140/141/142` are in progress, mock implementations of the refactored components (`MockConsumptionManager`, etc.) will be used for unit testing the policy managers. These mocks MUST adhere strictly to the agreed-upon `api.py` definitions from Checkpoint 1.
    -   The `verify_soft_landing.py` script will become the new source of truth for "golden" economic cycle data.

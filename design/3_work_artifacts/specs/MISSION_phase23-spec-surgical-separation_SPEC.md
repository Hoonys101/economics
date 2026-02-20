modules/firm/api.py
```python
"""
Firm API Module
Defines the public interface, DTOs, and stateless engine contracts for Firm agents.
Adheres strictly to the SEO (Stateless Engine & Orchestrator) pattern.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Protocol, runtime_checkable
from enum import Enum

from modules.simulation.dtos.api import FirmStateDTO as BaseFirmStateDTO
from modules.system.api import MarketSnapshotDTO
from simulation.models import Order
from simulation.dtos.decision_dtos import DecisionOutputDTO

# --- Enums ---

class FirmStrategy(Enum):
    PROFIT_MAXIMIZATION = "PROFIT_MAXIMIZATION"
    MARKET_SHARE = "MARKET_SHARE"
    SURVIVAL = "SURVIVAL"

# --- DTOs: State ---

@dataclass
class FirmStateDTO(BaseFirmStateDTO):
    """
    Expanded State DTO covering all aspects of a Firm,
    consolidating previously fragmented Department states.
    """
    # HR State
    employee_ids: List[int]
    wages: Dict[int, int]  # Employee ID -> Penny Wage
    last_fired_tick: int
    last_hired_tick: int
    hiring_momentum: float
    labor_demand_met: float

    # Finance State
    debt_pennies: int
    credit_limit_pennies: int
    last_dividend_tick: int
    consecutive_loss_ticks: int
    retained_earnings_pennies: int
    
    # Strategy State
    current_strategy: FirmStrategy
    target_margin: float

    # Production/Inventory State (Base DTO covers inventory)
    production_capacity: float
    capacity_utilization: float

# --- DTOs: Inputs ---

@dataclass
class FinanceDecisionInputDTO:
    """Input for FinanceEngine."""
    state: FirmStateDTO
    market_snapshot: MarketSnapshotDTO
    config: Any  # FirmConfigDTO
    current_tick: int
    credit_rating: float  # External signal

@dataclass
class HRDecisionInputDTO:
    """Input for HREngine."""
    state: FirmStateDTO
    budget_plan: BudgetPlanDTO  # Output from FinanceEngine
    market_snapshot: MarketSnapshotDTO
    config: Any  # FirmConfigDTO
    current_tick: int
    labor_market_avg_wage: int

# --- DTOs: Outputs ---

@dataclass
class BudgetPlanDTO:
    """Output from FinanceEngine. Determines constraints for other engines."""
    total_budget_pennies: int
    labor_budget_pennies: int
    capital_budget_pennies: int
    marketing_budget_pennies: int
    dividend_payout_pennies: int
    debt_repayment_pennies: int
    is_solvent: bool

@dataclass
class HRDecisionOutputDTO:
    """Output from HREngine."""
    hiring_orders: List[Order]  # Labor Buy Orders
    firing_ids: List[int]       # Employees to release
    wage_updates: Dict[int, int] # ID -> New Wage
    target_headcount: int

# --- Interfaces (Protocols) ---

@runtime_checkable
class IFinanceEngine(Protocol):
    """Stateless engine for financial planning."""
    def plan_budget(self, input_dto: FinanceDecisionInputDTO) -> BudgetPlanDTO:
        ...

@runtime_checkable
class IHREngine(Protocol):
    """Stateless engine for human resources management."""
    def manage_workforce(self, input_dto: HRDecisionInputDTO) -> HRDecisionOutputDTO:
        ...

# --- Stubs for Implementation ---

class FinanceEngine(IFinanceEngine):
    def plan_budget(self, input_dto: FinanceDecisionInputDTO) -> BudgetPlanDTO:
        ...

class HREngine(IHREngine):
    def manage_workforce(self, input_dto: HRDecisionInputDTO) -> HRDecisionOutputDTO:
        ...

```

design/3_work_artifacts/specs/phase23_surgical_separation_spec.md
```markdown
# Phase 23 Spec: Operation Surgical Separation

## 1. Overview
This specification details the refactoring of the `Firm` agent and `WorldState` to resolve critical architectural debt.
- **Goal**: Decouple stateful "Departments" (HR, Finance) into stateless "Engines" (SEO Pattern) and fix the singleton ambiguity in `WorldState`.
- **Target Debt**: `TD-ARCH-FIRM-COUP` (High), `TD-ARCH-GOV-MISMATCH` (Medium).

## 2. Technical Debt Analysis
- **TD-ARCH-FIRM-COUP**: Current `Department` classes hold back-references to `Firm` (`self.parent`), creating circular dependencies and spaghetti state mutation.
- **TD-ARCH-GOV-MISMATCH**: `WorldState` exposes both a list (`governments`) and a property (`government`), leading to inconsistent access patterns.

## 3. Detailed Design

### 3.1. Firm Architecture (SEO Pattern)

The `Firm` class will act purely as an **Orchestrator**, holding state in `FirmStateDTO` and delegating logic to stateless engines.

#### Data Flow
1.  **Input**: `DecisionContext` (Market data, Config).
2.  **Step 1: Financial Planning**
    -   Orchestrator calls `FinanceEngine.plan_budget(input)`.
    -   **Input**: `FinanceDecisionInputDTO` (State + Market).
    -   **Output**: `BudgetPlanDTO` (Allocated pennies for Labor, Capital, etc.).
3.  **Step 2: HR Management**
    -   Orchestrator calls `HREngine.manage_workforce(input, budget)`.
    -   **Input**: `HRDecisionInputDTO` (State + BudgetPlan + Market).
    -   **Output**: `HRDecisionOutputDTO` (Hiring orders, Firing list, Wage updates).
4.  **Step 3: Execution (Side Effects)**
    -   Orchestrator applies `BudgetPlan` (e.g., pay dividends, repay debt).
    -   Orchestrator applies `HRDecision` (e.g., send orders to market, update `state.employee_ids`).

#### Class Structure Refactor
-   **Remove**: `simulation.firms.departments.HRDepartment`, `FinanceDepartment`.
-   **Create**: `modules.firm.engines.finance.FinanceEngine`, `modules.firm.engines.hr.HREngine`.
-   **Update**: `simulation.firms.Firm` to initialize these engines in `__init__`.

### 3.2. WorldState Hygiene

Refactor `simulation/world_state.py` to enforce Single Source of Truth for the Government agent.

-   **Change**: Replace `self.governments: List[Government]` with `self.government: Optional[Government]`.
-   **Constructor**: Update `__init__` (or the initializer logic) to assign the primary government directly to `self.government`.
-   **Access**: Remove the `def government(self)` property getter/setter hack. Access `self.government` directly.
-   **Impact**: Audit all call sites using `.governments` list iteration and refactor to use the singleton.

## 4. Implementation Steps

### Step 1: DTO & API Definition
-   Implement `modules/firm/api.py` (as defined in the API Draft).
-   Ensure `FirmStateDTO` captures ALL state previously held in departments (e.g., `hiring_momentum`, `consecutive_loss_ticks`).

### Step 2: Engine Extraction
-   Move logic from `HRDepartment.manage()` to `HREngine.manage_workforce()`.
-   Move logic from `FinanceDepartment.allocate()` to `FinanceEngine.plan_budget()`.
-   **Constraint**: Engines must NOT reference `self.parent` or `Firm` instance.

### Step 3: Orchestrator Wiring
-   Update `Firm.make_decision()` to call engines in sequence: `Finance` -> `HR`.
-   Implement the logic to *apply* the DTO results to `self._econ_state`.

### Step 4: WorldState Refactor
-   Modify `WorldState` class attributes.
-   Run `grep` to find `world.governments` usage and replace with `world.government`.

## 5. Verification & Testing

### 5.1. Unit Tests
-   **Mocking**: Use strict protocol mocking for engines.
    ```python
    def test_firm_orchestration():
        finance_mock = MagicMock(spec=IFinanceEngine)
        hr_mock = MagicMock(spec=IHREngine)
        # Verify Orchestrator passes correct DTOs
        firm = Firm(..., engines={finance: finance_mock, hr: hr_mock})
        firm.make_decision(...)
        assert finance_mock.plan_budget.called
        assert isinstance(finance_mock.plan_budget.call_args[0][0], FinanceDecisionInputDTO)
    ```

### 5.2. Integration Check
-   Run `tests/test_firm_integration.py` (create if missing).
-   Verify a firm can survive 10 ticks without crashing due to missing state attributes.

## 6. Risk Assessment & Audit

-   **Risk**: Logic regression in HR hiring thresholds (loss of "memory").
    -   *Mitigation*: Ensure `FirmStateDTO` includes `hiring_momentum` and `last_fired_tick`.
-   **Risk**: `WorldState` refactor breaks `SimulationInitializer`.
    -   *Mitigation*: Update the initializer to set `world.government = created_gov`.

## 7. Mandatory Reporting
-   Create `communications/insights/phase23-spec-surgical-separation.md`.
-   Log any "Ghost State" discovered in legacy Departments that was missed in the DTO.
-   Document the successful removal of `self.parent` references.
```
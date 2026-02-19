modules/governance/api.py
```python
from __future__ import annotations
from typing import Protocol, List, Dict, Any, Optional, runtime_checkable
from dataclasses import dataclass
from modules.system.api import ICurrencyHolder, CurrencyCode, AgentID, IAgentRegistry

@dataclass
class GovernmentConfigDTO:
    """Configuration DTO for Government Agent initialization."""
    initial_assets: int
    tax_rate_income: float
    tax_rate_corporate: float
    tax_rate_sales: float
    budget_allocation: Dict[str, float]

@runtime_checkable
class IGovernment(ICurrencyHolder, Protocol):
    """
    Protocol defining the public interface of the Government agent.
    Used by WorldState and TickOrchestrator to interact with the singleton/primary government.
    """
    id: AgentID
    is_active: bool
    
    def get_monetary_delta(self, currency: CurrencyCode) -> int:
        """Returns the net change in money supply caused by government operations."""
        ...

    def reset_tick_flow(self) -> None:
        """Resets tick-local flow counters (e.g., spending, tax collection) at the start of a tick."""
        ...
        
    def settle_atomic(self, amount: int, counterparty_id: AgentID, reason: str) -> bool:
        """
        Executes an atomic settlement operation. 
        Replaces legacy collect_tax/pay_subsidy methods.
        """
        ...

class IGovernmentRegistry(Protocol):
    """
    Interface for accessing Government instances within WorldState.
    Supports future multi-government scenarios while maintaining backward compatibility.
    """
    @property
    def government(self) -> Optional[IGovernment]:
        """
        Returns the primary government (singleton accessor).
        Should return the first element of governments list or None.
        """
        ...
    
    @property
    def governments(self) -> List[IGovernment]:
        """Returns the list of all registered governments."""
        ...

    def register_government(self, gov: IGovernment, is_primary: bool = False) -> None:
        """Registers a new government instance."""
        ...

```

design/3_work_artifacts/specs/government_structure_refactor_spec.md
```markdown
# Spec: Government Structure Refactor (Singleton-List Unification)

## 1. Introduction

- **Purpose**: Resolve the architectural divergence between `WorldState.governments` (List) and `Simulation.government` (Singleton/Ghost Attribute).
- **Scope**: `simulation/world_state.py`, `simulation/initialization/initializer.py`, `modules/governance/api.py`.
- **Goals**:
  - Eliminate "Ghost Attributes" (dynamic attributes not defined in `__init__` or class body).
  - Establish `governments` (List) as the Single Source of Truth (SSoT).
  - Maintain backward compatibility for `state.government` accessors via properties.

## 2. Problem Analysis (Technical Debt)

- **Ghost Attribute**: `WorldState` instances currently possess a `government` attribute created dynamically at runtime via `Simulation.__setattr__` -> `WorldState.__setattr__` (implicit) or direct assignment in `initializer.py`.
- **Split Truth**: `state.governments` is initialized as `[]` and remains empty because the initializer assigns to `sim.government` (the ghost attribute) instead of appending to the list.
- **Type Safety**: Static analysis tools (mypy) and IDEs cannot see `state.government`, leading to `Any` types and potential runtime errors if the ghost attribute isn't set.
- **Protocol Violation**: `WorldState` does not strictly implement `IGovernmentRegistry`.

## 3. Detailed Design

### 3.1. Component: `WorldState` Refactor

- **File**: `simulation/world_state.py`
- **Changes**:
  1.  **Strict Type Hinting**: Explicitly define `self.governments: List[Government]` (or `List[IGovernment]`).
  2.  **Property Accessor**: Implement `@property` for `government` to proxy `self.governments[0]`.
  3.  **Setter Logic**: Implement setter for `government` to ensure synchronization with the list.

#### Logic (Pseudo-code)

```python
class WorldState:
    def __init__(self, ...):
        # ... existing init ...
        self.governments: List[Any] = [] # SSoT

    @property
    def government(self) -> Optional[Any]:
        """
        Backward compatibility accessor for the primary government.
        Returns the first government in the list.
        """
        if not self.governments:
            return None
        return self.governments[0]

    @government.setter
    def government(self, value: Any) -> None:
        """
        Sets the primary government. 
        Replaces the first element if exists, or appends if empty.
        Enforces List SSoT.
        """
        if not self.governments:
            self.governments.append(value)
        else:
            self.governments[0] = value
            # Optional: Log warning about replacing primary government
```

### 3.2. Component: `SimulationInitializer` Update

- **File**: `simulation/initialization/initializer.py`
- **Changes**:
  - Stop assigning to `sim.government` directly.
  - Use `sim.world_state.governments.append(gov)` (or the new setter).

#### Logic (Pseudo-code)

```python
# In SimulationInitializer.build_simulation

# OLD
# sim.government = Government(...)
# sim.agents[sim.government.id] = sim.government

# NEW
gov = Government(...)
sim.world_state.governments.append(gov) # Explicit List Population
# sim.government property will now resolve correctly to this instance.
sim.agents[gov.id] = gov
```

### 3.3. DTO & SimulationState Impact

- **File**: `simulation/dtos/api.py` (`SimulationState`)
- **Impact**: The `SimulationState` DTO currently has `government: Any`.
- **Resolution**: In `TickOrchestrator._create_simulation_state_dto`, ensure we pass `state.government` (which now uses the property). No change needed in DTO definition for this phase, but `WorldState` must ensure the property returns a valid object, not None, during active ticks.

## 4. Verification Plan

### 4.1. New Test Cases

1.  **Singleton-List Sync**:
    - Set `state.government = gov`.
    - Assert `state.governments[0] == gov`.
    - Assert `len(state.governments) == 1`.

2.  **List Priority**:
    - `state.governments.append(gov1)`
    - `state.governments.append(gov2)`
    - Assert `state.government == gov1` (Primary is index 0).

3.  **Initializer Integrity**:
    - Run `SimulationInitializer`.
    - Assert `sim.world_state.governments` is not empty.
    - Assert `sim.world_state.government` is not None.

### 4.2. Legacy Test Impact (Risk Assessment)

- **Mocking**: Existing tests using `mock_state.government = Mock()` will work *if* `mock_state` is a `MagicMock` (it allows attribute assignment).
- **Refactor Requirement**: Any test creating a *real* `WorldState` instance and manually setting `government` will trigger the new setter. If the test assumes `government` is independent of `governments`, it might fail if it checks `governments` length.
- **Action**: Run strict search for `state.government =` assignments in `tests/`.

## 5. Risk Assessment

- **Circular Import**: Low risk. `WorldState` already imports `Government` (inside TYPE_CHECKING).
- **Performance**: Negligible overhead from property access.
- **Breaking Changes**: None for external consumers accessing `state.government`.

## 6. Mandatory Reporting

> **[Insight Recorded]**: A detailed analysis of the "Ghost Attribute" anti-pattern and the remediation strategy has been recorded in `communications/insights/analyze-gov-structure.md`.

```

communications/insights/analyze-gov-structure.md
```markdown
# Architectural Insight: Government Structure Analysis

- **Date**: 2026-02-19
- **Mission**: `analyze-gov-structure`
- **Author**: Gemini-CLI Scribe

## 1. Discovery: The Ghost Attribute Anti-Pattern

During the audit of `simulation/world_state.py` and `initializer.py`, a significant structural divergence was identified regarding the `Government` agent.

- **Definition**: `WorldState` defines `self.governments: List[Government] = []`.
- **Usage**: The entire codebase (Orchestrator, Simulation Facade) interacts with `state.government` (Singleton).
- **Mechanism**: `state.government` exists *only* because `SimulationInitializer` dynamically assigns it at runtime. It is not defined in `WorldState.__init__`.
- **Consequence**: `state.governments` (the explicitly defined list) remains empty `[]` throughout the simulation lifecycle. The "real" government lives in a dynamic attribute invisible to static analysis tools.

## 2. Technical Debt ID: `TD-ARCH-GOV-MISMATCH`

This issue creates two specific debts:
1.  **Split Source of Truth**: Data exists in an un-typed dynamic attribute while the typed attribute remains empty.
2.  **Fragile Initialization**: Logic relying on `resolve_agent_id("GOVERNMENT")` (if it were to check the list) would fail.

## 3. Remediation Strategy

The remediation (detailed in `specs/government_structure_refactor_spec.md`) adopts a **"Property Proxy"** pattern:
- The List (`governments`) becomes the underlying storage (SSoT).
- The Singleton (`government`) becomes a `@property` accessor/setter that manipulates the List.

This ensures backward compatibility for all `state.government` calls while enforcing structural integrity and allowing for future multi-government scenarios.
```
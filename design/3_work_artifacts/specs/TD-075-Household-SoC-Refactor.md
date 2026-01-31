# Work Order: - Household Facade Refinement

**Phase:** 3
**Priority:** MEDIUM
**Prerequisite:** None
**Technical Debt Addressed:** [TD-075: `Household` Facade Bloat (850+ lines)](file:///design/TECH_DEBT_LEDGER.md)

---

## 1. Problem Statement

The `Household` class in `simulation/core_agents.py`, while functioning as a facade, still retains direct ownership of some economic state and logic, violating the Single Responsibility Principle (SRP). Attributes and methods related to price perception and inflation expectation (`expected_inflation`, `update_perceived_prices`, etc.) bloat the facade and should reside within the `EconComponent`.

The Pre-Refactoring Audit mandates that the public API of the `Household` class **must not change**. Any refactoring must preserve the existing property-based access patterns (e.g., `household.expected_inflation`).

## 2. Objective

Improve the architectural purity of the `Household` agent by delegating all economic state and logic to `EconComponent`, while maintaining 100% backward compatibility of the `Household`'s public API.

## 3. Target Module & API Specification

### Target Files
- `simulation/core_agents.py` (To be modified)
- `modules/household/econ_component.py` (To be modified)
- `modules/household/api.py` (To be created/updated)

### API Definition (`modules/household/api.py`)

```python
# modules/household/api.py
from typing import Dict, Protocol, List, Any, Deque
from collections import deque

from simulation.dtos import StressScenarioConfig

class IHouseholdEcon(Protocol):
 """
 Interface defining the economic responsibilities and state
 managed by the EconComponent.
 """
 # --- Existing Properties to be maintained ---
 assets: float
 inventory: Dict[str, float]
 # ... other existing econ properties

 # --- NEWLY DELEGATED STATE ---
 expected_inflation: Dict[str, float]
 perceived_avg_prices: Dict[str, float]
 price_history: "defaultdict[str, deque]"
 adaptation_rate: float

 def update_perceived_prices(
 self,
 market_data: Dict[str, Any],
 stress_scenario_config: StressScenarioConfig | None = None
 ) -> None:
 """
 Calculates and updates the agent's inflation expectation and
 perceived average prices based on market data.
 """
 ...

```

## 4. Implementation Plan

### Track A: Enhance `EconComponent`

1. **Relocate State:** In `modules/household/econ_component.py`, move the initialization of the following attributes from `Household.__init__` to `EconComponent.__init__`. The `EconComponent` can access the parent `Household`'s `personality` and `config_module` via `self.parent`.

 ```python
 # In EconComponent.__init__
 self.parent = parent # Household instance
 self.config = config_module

 # Phase 23: Inflation Expectation & Price Memory
 self.expected_inflation: Dict[str, float] = defaultdict(float)
 self.perceived_avg_prices: Dict[str, float] = {}
 self.price_history: "defaultdict[str, deque]" = defaultdict(lambda: deque(maxlen=10))

 # Initialize perceived prices from config/goods_data if possible
 for g in self.parent.goods_info_map.values():
 self.perceived_avg_prices[g["id"]] = g.get("initial_price", 10.0)

 # Adaptation Rate (Personality Based)
 self.adaptation_rate: float = getattr(self.config, "ADAPTATION_RATE_NORMAL", 0.2)
 if self.parent.personality == Personality.IMPULSIVE:
 self.adaptation_rate = getattr(self.config, "ADAPTATION_RATE_IMPULSIVE", 0.5)
 elif self.parent.personality == Personality.CONSERVATIVE:
 self.adaptation_rate = getattr(self.config, "ADAPTATION_RATE_CONSERVATIVE", 0.1)

 ```

2. **Relocate Logic:** Move the entire method body of `update_perceived_prices` from the `Household` class to the `EconComponent` class. The method signature should remain the same. It will now use `self.parent.goods_info_map` and `self.config` instead of accessing them directly.

### Track B: Refactor `Household` Facade

1. **Remove Redundant Code:** In `simulation/core_agents.py`, delete the attributes and logic moved in Track A from the `Household.__init__` method.

2. **Delegate Method Call:** Modify the `Household.update_perceived_prices` method to be a single-line delegation to its `EconComponent`.

 ```python
 # In Household class
 @override
 def update_perceived_prices(self, market_data: Dict[str, Any], stress_scenario_config: Optional["StressScenarioConfig"] = None) -> None:
 self.econ_component.update_perceived_prices(market_data, stress_scenario_config)
 ```

3. **Preserve Public API (Critical):** Add new `@property` delegations to the `Household` class for each attribute that was moved to `EconComponent`. This is essential to prevent breaking changes.

 ```python
 # In Household class, after other property delegations

 @property
 def expected_inflation(self) -> Dict[str, float]:
 return self.econ_component.expected_inflation

 @expected_inflation.setter
 def expected_inflation(self, value: Dict[str, float]) -> None:
 self.econ_component.expected_inflation = value

 @property
 def perceived_avg_prices(self) -> Dict[str, float]:
 return self.econ_component.perceived_avg_prices

 @perceived_avg_prices.setter
 def perceived_avg_prices(self, value: Dict[str, float]) -> None:
 self.econ_component.perceived_avg_prices = value

 @property
 def price_history(self) -> "defaultdict[str, deque]":
 return self.econ_component.price_history

 @price_history.setter
 def price_history(self, value: "defaultdict[str, deque]") -> None:
 self.econ_component.price_history = value

 @property
 def adaptation_rate(self) -> float:
 return self.econ_component.adaptation_rate

 @adaptation_rate.setter
 def adaptation_rate(self, value: float) -> None:
 self.econ_component.adaptation_rate = value
 ```

### Track C: Update Data Contracts

1. **Update DTO Creation:** In `simulation/core_agents.py`, modify the `Household.create_state_dto` method. The `expected_inflation` field should now source its data from the new property, which delegates to the `EconComponent`. The structure of the final `HouseholdStateDTO` must not change.

 ```python
 # In Household.create_state_dto
 def create_state_dto(self) -> HouseholdStateDTO:
 """Creates a comprehensive DTO of the household's current state."""
 return HouseholdStateDTO(
 # ... all other fields are unchanged
 expected_inflation=self.expected_inflation, # This now uses the @property delegate
 # ...
 )
 ```

## 5. Verification Plan

1. **Unit & Integration Tests**: All existing tests must pass. Execute `pytest tests/simulation/` and `pytest tests/modules/household/`.
2. **New Unit Tests**: Create a new test file `tests/modules/household/test_econ_component.py`. Add specific tests for the `EconComponent.update_perceived_prices` method, verifying correct calculation under different `market_data` conditions.
3. **Data Contract Verification**:
 - Write a script that:
 a. Instantiates a `Household` agent using the code *before* refactoring.
 b. Calls `create_state_dto()` and saves the output to `before.json`.
 c. Instantiates an identical `Household` agent using the code *after* refactoring.
 d. Calls `create_state_dto()` and saves the output to `after.json`.
 e. Asserts that `before.json` and `after.json` are identical.

## 6. 🚨 Risk & Impact Audit

- **Architectural Risk (Circular Reference)**: **LOW**. The existing Dependency Injection pattern (`parent` reference in components) is maintained.
- **Test Suite Impact**: **MEDIUM**. Tests that directly mock `Household.expected_inflation` may need to be updated to mock `Household.econ_component.expected_inflation` instead. Tests relying only on the public API should pass.
- **Configuration Dependency**: **NONE**. No new configuration values are introduced.
- **Data Contract Integrity**: **HIGH**. The `HouseholdStateDTO` is a critical contract for the AI engine. The verification plan *must* be followed to ensure its structure remains unchanged.

---

### **[Routine] Mandatory Reporting**
Jules, during implementation, you are required to document any unforeseen complexities, architectural insights, or new technical debt discovered. Create a new markdown file in `communications/insights/` with the filename `insight_WO-092_<your_finding>.md` to report your findings.

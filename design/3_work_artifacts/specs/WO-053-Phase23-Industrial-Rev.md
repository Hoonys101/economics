# Work Order: - Industrial Revolution Core Integration

**Phase:** 23
**Priority:** HIGH
**Prerequisite:** None

## 1. Problem Statement
The current simulation lacks a mechanism for technological breakthroughs to impact economic output directly. The `TechnologyManager` exists but is not integrated into the core production logic, making its impact zero. This prevents the simulation of key economic events like the Industrial Revolution.

## 2. Objective
Integrate the `TechnologyManager` with the `ProductionDepartment` to enable technology-driven productivity growth. The "Chemical Fertilizer" technology will act as the first implementation, tripling the productivity of firms in the FOOD sector upon adoption.

## 3. Target Metrics
| Metric | Current | Target |
|---|---|---|
| Food Production (Post-Tech) | `tfp * labor^a * capital^b` | `(tfp * 3.0) * labor^a * capital^b` |
| Tech Adoption by Visionaries | 0 | 100% (immediate) |
| Tech Diffusion to others | 0% | > 0% (gradual, based on diffusion rate) |

---

# `industrial_revolution_spec.md`

## 1. System Architecture & SoC Refactoring
To adhere to strict SoC and resolve the risks identified in the pre-flight audit, the integration will be orchestrated by the main simulation loop (`main.py`). This avoids creating "God Object" dependencies.


*(Diagram Placeholder: A simple diagram showing `main.py` calling `StatsService` -> passing results to `TechnologyManager` -> passing `TechnologyManager` to `Firm`)*

- **`main.py` (Orchestrator):**
 1. Calculates aggregate statistics (`human_capital_index`).
 2. Calls `TechnologyManager.update()` with the necessary data.
 3. Injects the `TechnologyManager` instance into the `firm.produce()` call.
- **`TechnologyManager` (System):**
 1. Receives data, does not fetch it.
 2. Manages the state of technology (unlocks, adoption).
- **`ProductionDepartment` (Component):**
 1. Receives the `TechnologyManager` and uses it to get a multiplier.

## 2. Interface Specification (`api.py`)
The following interfaces define the contract for the technology system. DTOs are used to ensure loose coupling.

```python
#
# File: simulation/systems/tech/api.py
#
from __future__ import annotations
from typing import List, Protocol, TypedDict, Set

# --- Data Transfer Objects (DTOs) ---

class FirmTechInfoDTO(TypedDict):
 """Minimal firm data required for technology diffusion."""
 id: int
 sector: str
 is_visionary: bool

class HouseholdEducationDTO(TypedDict):
 """Minimal household data required for human capital calculation."""
 is_active: bool
 education_level: float

# --- System Interface ---

class TechnologySystemAPI(Protocol):
 """
 Defines the public contract for the TechnologyManager.
 It operates on DTOs and primitive types, not full agent objects.
 """

 def update(
 self,
 current_tick: int,
 firms: List[FirmTechInfoDTO],
 human_capital_index: float
 ) -> None:
 """
 Updates the state of technology diffusion.
 - Checks for new tech unlocks.
 - Processes the S-curve adoption for all active technologies.
 """
 ...

 def get_productivity_multiplier(self, firm_id: int) -> float:
 """
 Returns the total productivity multiplier for a given firm
 based on its adopted technologies.
 """
 ...

 def has_adopted(self, firm_id: int, tech_id: str) -> bool:
 """Checks if a firm has adopted a specific technology."""
 ...
```

## 3. Logic Steps (Pseudo-code)

### 3.1. `main.py` (Simulation Loop)
```python
# main.py
def run_simulation():
 # ... initialization of simulation, firms, households, technology_manager ...

 for tick in range(SIMULATION_TICKS):
 # 1. [ORCHESTRATION] Calculate aggregate stats
 active_households_dto = [
 HouseholdEducationDTO(is_active=h.is_active, education_level=getattr(h, 'education_level', 0))
 for h in simulation.households
 ]

 total_edu = sum(h['education_level'] for h in active_households_dto if h['is_active'])
 active_count = sum(1 for h in active_households_dto if h['is_active'])
 human_capital_index = total_edu / active_count if active_count > 0 else 1.0

 # 2. [ORCHESTRATION] Update technology system state
 active_firms_dto = [
 FirmTechInfoDTO(id=f.id, sector=f.sector, is_visionary=getattr(f, 'is_visionary', False))
 for f in simulation.firms if f.is_active
 ]
 technology_manager.update(tick, active_firms_dto, human_capital_index)

 # 3. [AGENT ACTIONS]
 for firm in simulation.firms:
 if not firm.is_active:
 continue

 # ... other firm logic ...

 # [INJECTION] Inject the tech manager into the production call
 firm.production_department.produce(tick, technology_manager)
```

### 3.2. `TechnologyManager` Refactoring
```python
# simulation/systems/technology_manager.py

# REMOVE _update_human_capital_index method.

# MODIFY update signature
# def update(self, current_tick: int, simulation: Any) -> None: # OLD
def update(self, current_tick: int, firms: List[FirmTechInfoDTO], human_capital_index: float) -> None: # NEW
 # self._update_human_capital_index(simulation.households) # REMOVE
 self.human_capital_index = human_capital_index # SET from parameter

 # ... Unlock Check logic remains the same ...

 # MODIFY to use the injected 'firms' DTO list
 # for firm in simulation.firms: # OLD
 for firm_dto in firms: # NEW
 # ... logic uses firm_dto['id'], firm_dto['sector'], etc. ...

# MODIFY _unlock_tech to accept the DTO list
# def _unlock_tech(self, tech: TechNode, simulation: Any): # OLD
def _unlock_tech(self, tech: TechNode, firms: List[FirmTechInfoDTO]): # NEW
 # ... logic iterates over 'firms' DTO list ...
```

### 3.3. `ProductionDepartment` Integration
```python
# simulation/components/production_department.py
# No major change needed, just ensure the `if technology_manager:` block is correctly implemented.

def produce(self, current_time: int, technology_manager: TechnologySystemAPI | None = None) -> float:
 # ... existing logic ...

 # Technology Multiplier ()
 tech_multiplier = 1.0
 if technology_manager:
 # The call to get_productivity_multiplier already exists.
 # This confirms the integration point.
 tech_multiplier = technology_manager.get_productivity_multiplier(self.firm.id)

 tfp = self.firm.productivity_factor * tech_multiplier

 # ... rest of the production logic ...
```

## 4. Verification Plan

1. **Unit Test (`test_technology_manager.py`):**
 - `test_effective_diffusion_rate`: Assert that `_get_effective_diffusion_rate` returns `base_rate * (1 + 0.5 * (HCI - 1.0))` for various `human_capital_index` inputs.
 - `test_unlock_and_visionary_adoption`: Call `update()` on the tick where "TECH_AGRI_CHEM_01" unlocks. Assert that all firms with `is_visionary=True` and `sector='FOOD'` have adopted the tech via `has_adopted()`.
 - `test_diffusion_over_time`: After the unlock tick, run `update()` for 20 more ticks. Assert that some non-visionary firms in the 'FOOD' sector have adopted the tech.

2. **Integration Test (`tests/integration/test_phase23_production.py`):**
 - `test_production_boost_from_fertilizer_tech`:
 1. Create two identical firms (`firm_A`, `firm_B`) in the 'FOOD' sector.
 2. Create a `TechnologyManager` and unlock "TECH_AGRI_CHEM_01".
 3. Manually have `firm_A` adopt the tech using `_adopt()`.
 4. Run `firm_A.produce(tech_manager)` and `firm_B.produce(tech_manager)`.
 5. Assert `production_A` is approximately `3.0 * production_B`.

## 5. Mocking Guide
- For integration tests, use `pytest` fixtures. Create a `technology_manager_fixture` that yields a configured `TechnologyManager`.
- **DO NOT** use `MagicMock` for the `TechnologyManager` in `test_production_boost_from_fertilizer_tech`. Instantiate a real `TechnologyManager` to ensure the internal logic of `get_productivity_multiplier` is also tested.
- Use `golden_firms` and `golden_households` fixtures from `conftest.py` to create realistic agent populations for testing the `update` method.

## 6. 🚨 Risk & Impact Audit (Resolution Plan)

- **High Coupling via "God Object"**: **RESOLVED**. The design mandates that `TechnologyManager.update` receives only DTOs and primitive types (`firms: List[FirmTechInfoDTO]`, `human_capital_index: float`), not the `simulation` object. The main loop is responsible for data preparation and injection.
- **SRP Violation**: **RESOLVED**. The responsibility of calculating `human_capital_index` has been removed from `TechnologyManager` and moved to the orchestrator (`main.py`). The manager now receives this value as a parameter, adhering to SRP.
- **Test Coverage Gap**: **ADDRESSED**. The "Verification Plan" explicitly requires a new integration test (`test_production_boost_from_fertilizer_tech`) to validate that the `tech_multiplier` correctly impacts the output of the `ProductionDepartment.produce` method.
- **Technical Debt Contradiction**: **ALIGNED**. The proposed design strictly follows the established precedent of decomposing dependencies (TD-065, TD-066), preventing the re-introduction of architectural debt.

---

### **[Routine] Mandatory Reporting**
*Jules, during implementation, you are required to log any unforeseen complexities, suggested improvements, or potential technical debt. Create a new markdown file in `communications/insights/` named `YYYY-MM-DD_WO-053_insights.md` to document your findings.*

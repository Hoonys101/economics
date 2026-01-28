# WO-136: Strategy Generalization (Tactical Sanitation)

## 1. 🎯 Objective
Eliminate "Config Pollution" and "Hardcoded Scenarios" by introducing a formalized **Strategy Pattern**.
Currently, scenarios (like Phase 23) inject parameters by monkey-patching the global `config` object via `setattr`. This makes data flow opaque and debugging difficult. We will replace this with a explicit `ScenarioStrategy` DTO.

## 2. 🚩 Identified Technical Debt
- **TD-133 (Config Pollution)**: `SimulationInitializer` reads JSON and uses `setattr(self.config, ...)` to overwrite global constants.
- **TD-134 (Branching Complexity)**: Logic depends on checking `config.active_scenario == '...'` or implicitly relied on overwritten values.

## 3. 🛠️ Implementation Requirements

### Step 1: Define `ScenarioStrategy` DTO
Create `simulation/dtos/strategy.py`:
```python
@dataclass(frozen=True)
class ScenarioStrategy:
    name: str
    is_active: bool
    # Generic Parameters (Not Scenario Specific)
    tfp_multiplier: float = 1.0
    monetary_shock_target: Optional[float] = None
    fiscal_shock_tax_rate: Optional[float] = None
    # ... add fields found in initializer.py mapping
```

### Step 2: Refactor `SimulationInitializer`
- Remove the `setattr` loop in `build_simulation`.
- Instead, instantiate the `ScenarioStrategy` DTO from the JSON data.
- Store this strategy in `Simulation` instance (`sim.strategy`).

### Step 3: Inject Strategy (Dependency Injection)
- Pass `sim.strategy` into components that need it, specifically:
    - `TechnologyManager` (needs TFP multiplier)
    - `CentralBank` (needs monetary shock targets)
    - `Government` (needs fiscal shock targets)
- **Constraint**: Do NOT pass the raw `config` module if only strategy params are needed. Pass `strategy` DTO.

### Step 4: Cleanup
- Remove any `if config.active_scenario == ...` checks in the codebase.
- Ensure `TechnologyManager` reads `strategy.tfp_multiplier` instead of `config.TECH_FERTILIZER_MULTIPLIER`.

## 4. ✅ Acceptance Criteria
1.  **Zero `setattr`**: Searching `setattr(self.config` in `initializer.py` returns 0 matches.
2.  **Explicit Data Flow**: Components receive strategy params via `__init__`, not by reading modified global config.
3.  **Backward Compatibility**: Existing scenarios (Phase 23, Phase 29) must load correctly into the new DTO structure.

## 5. 🔗 Reference
- `simulation/initialization/initializer.py` (Lines 111-140)
- `config/scenarios/*.json`

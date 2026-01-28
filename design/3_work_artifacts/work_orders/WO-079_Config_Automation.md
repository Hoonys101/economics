# Work Order: WO-079 Config Automation

**Target**: `simulation` module (Config & Refactoring)
**Context**: TD-007 (Hardcoded Constants) & TD-046 (Firm Constants)
**Pre-condition**: WO-078 (Engine SoC) is COMPLETED. `SimulationInitializer` is active.

## 0. Executive Summary
This work order focuses on **Phase 2: Configuration Automation**.
We will centralize hardcoded thresholds and parameters from `engine.py`, `firms.py`, and `agents.py` into a unified `SimulationConfig` system.
This enables "Zero-Code Stress Testing" by allowing parameters to be injected via JSON profiles.

## 1. Architecture Design (Config System)

### 1.1 `simulation/config.py` Structure
Create a hierarchically structured configuration system using `dataclasses`.

```python
# simulation/config.py (New File)

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import json
import os

@dataclass
class EconomyConfig:
    # Macroeconomic Parameters
    TAX_RATE: float = 0.2
    BASE_INTEREST_RATE: float = 0.05
    GOV_BUDGET_BOND_RATIO: float = 0.3  # Ratio of budget funded by bonds
    BAILOUT_THRESHOLD_RATIO: float = 0.5 # Equity ratio threshold for bailout

@dataclass
class AgentConfig:
    # Agent Behaviors
    LABOR_ELASTICITY_MIN: float = 0.3
    CONSUMPTION_SMOOTHING: float = 0.8
    INVENTORY_BUFFER: float = 2.0  # Target inventory coverage in months
    
@dataclass
class SimulationConfig:
    economy: EconomyConfig = field(default_factory=EconomyConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    # Simulation Settings
    MAX_TICKS: int = 1000
    TICKS_PER_YEAR: int = 100

    @classmethod
    def load(cls, profile_path: Optional[str] = None) -> "SimulationConfig":
        """
        Load config from a JSON file.
        1. Create default config.
        2. If profile_path exists, load JSON.
        3. Recursively update fields (Override).
        4. Return instance.
        """
        # Implementation required
        pass
```

## 2. Implementation Steps

### Step 1: Create `simulation/config.py`
- Implement the `SimulationConfig`, `EconomyConfig`, `AgentConfig` classes.
- Implement the `load` method with recursive dictionary update logic.
- **Constraint**: Do NOT use a global singleton instance in `config.py`. The config instance must be passed around (Dependency Injection).

### Step 2: Create JSON Profiles
Create directory `profiles/` and add:
1.  `profiles/default.json` (Empty object `{}` or explicit defaults)
2.  `profiles/industrial_revolution.json`:
    ```json
    {
        "economy": {
            "TAX_RATE": 0.1, 
            "BASE_INTEREST_RATE": 0.02 
        },
        "agent": {
            "LABOR_ELASTICITY_MIN": 0.1,
            "INVENTORY_BUFFER": 5.0
        }
    }
    ```

### Step 3: Refactor `SimulationInitializer`
Modify `simulation/initialization/initializer.py`:
- Accept `config_profile: str` in `__init__`.
- Call `SimulationConfig.load(config_profile)` to create a `self.config` instance.
- Pass `self.config` to the `Simulation` constructor.

### Step 4: Inject & Migrate (The Big Refactor)
Modify `simulation/engine.py`, `simulation/firms.py`, `simulation/core_agents.py`:
1.  **Inject**: Ensure `Simulation` class stores `self.config`.
2.  Pass `config` (or sub-configs like `config.economy`) to `Firm`, `Household`, `Government` when they are created.
3.  **Replace**:
    - `TAX_RATE` (global const) -> `self.config.economy.TAX_RATE`
    - `LABOR_MARKET_FLEXIBILITY` -> `self.config.agent.LABOR_ELASTICITY_MIN`
    - `INVENTORY_TARGET` -> `self.config.agent.INVENTORY_BUFFER`
    - And any other identified constants.

**Migration Table**:
| Legacy Constant | Location | New Config Path |
|---|---|---|
| `TAX_RATE` | agents.py | `config.economy.TAX_RATE` |
| `BASE_INTEREST_RATE` | engine.py | `config.economy.BASE_INTEREST_RATE` |
| `INVENTORY_TARGET` | firms.py | `config.agent.INVENTORY_BUFFER` |

## 3. Verification Plan

### 3.1 Unit Test: `tests/simulation/test_config_loading.py` (New)
- Test 1: Load default (no file) -> Verify default values.
- Test 2: Load `industrial_revolution.json` -> Verify values are overridden correctly.
- Test 3: Partial override -> Verify non-overridden values remain defaults.

### 3.2 Regression Test
- Run `tests/simulation/test_engine.py` using the default config.
- Ensure all assessments pass without modification to the test logic itself.

## 4. Constraints & Rules
- **No Global State**: Do not rely on `simulation.config.sim_config` global variable. Use injection.
- **Type Safety**: All config fields must be typed.
- **Zero Logic Change**: Do not change the calculation formulas, only the parameter sources.

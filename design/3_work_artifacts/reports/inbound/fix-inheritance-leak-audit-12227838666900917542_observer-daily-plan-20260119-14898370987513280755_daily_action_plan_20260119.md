# 📋 20260119 Daily Action Plan

**1. 🚦 System Health**
- **Architecture**: Critical
- **Top Risks**:
    1. **Immediate Crash**: Simulation fails at Tick 1 due to `Household.age` setter attribute error.
    2. **God Classes**: `simulation/core_agents.py` and `simulation/engine.py` are over 1000/900 lines, violating complexity thresholds.

**2. 🚨 Critical Alerts (Must Fix)**
- **Bug**: `AttributeError: property 'age' of 'Household' object has no setter`
    - **Location**: `simulation/systems/demographic_manager.py` line 44
    - **Impact**: Simulation cannot run a single tick.

**3. 🚀 Proposed Action Plan (Jules' Proposal)**

#### **Proposal 1: Fix Household Age Setter Logic**
- **Why**: `Household` delegates `age` to `DemographicsComponent` via a property, but lacks a setter. `DemographicManager` tries to increment `agent.age` directly.
- **Target**: `simulation/core_agents.py` (Household class) or `simulation/systems/demographic_manager.py`
- **Plan**:
    - Modify `Household.age` property in `simulation/core_agents.py` to include a setter that updates `self.demographics.age`.
    - Alternatively, update `DemographicManager` to access `agent.demographics.age` directly if `Household` is just a facade. Given `DemographicManager` seems to iterate over generic agents, adding the setter to the `Household` facade is the safer, more encapsulated approach.

#### **Proposal 2: Refactor God Class `simulation/core_agents.py`**
- **Why**: The file exceeds 1000 lines and mixes data containment (DTO-like fields) with logic delegates (Components).
- **Target**: `simulation/core_agents.py`
- **Plan**:
    - Continue the "Component-Entity" refactoring.
    - Move `Talent`, `Skill` classes to `simulation/agents/capabilities.py`.
    - Ensure `Household` becomes purely a shell delegating to components (`PsychologyComponent`, `DemographicsComponent`, etc.), reducing its line count.

#### **Proposal 3: Clean up Design Artifacts**
- **Why**: `design/gemini_output/*` files are flagged as Critical complexity but are likely generated reference code.
- **Target**: `scripts/observer/scan_codebase.py`
- **Plan**:
    - Update the scanner to exclude `design/` directory from the complexity metrics to avoid false positives in the health report.
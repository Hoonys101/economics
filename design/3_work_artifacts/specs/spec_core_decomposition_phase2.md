# Refactoring Spec: Firm & Household Orchestrator Decomposition (Phase 2)

## 1. Overview
**Problem**: `Firm` (1276 lines) and `Household` (1042 lines) remain "God Classes" despite earlier refactoring. They violate the 800-line limit and contain overlapping responsibilities like initialization, cloning, and granular domain logic.

**Goal**: Move creation logic to Factories and domain logic to specialized engines. Reduce orchestrator size to < 800 lines.

## 2. Proposed New Components

### 2.1. Factories (Simulation Layer)
- **[NEW] `simulation/factories/firm_factory.py`**:
    - `create_firm(...)`: Standard initialization.
    - `clone_firm(source_firm)`: Deep copy logic (moving away from `.clone()` method on agent).
- **[NEW] `simulation/factories/household_factory.py`**:
    - `create_household(...)`: Standard initialization.
    - `clone_household(source_hh)`: Deep copy logic.

### 2.2. Domain Engines (Module Layer)
- **[NEW] `modules/firms/engines/brand_engine.py`**:
    - Logic for brand equity decay, marketing ROI calculation, and quality-based reputation.
- **[NEW] `modules/households/engines/consumption_engine.py`**:
    - Logic for Maslow-based utility maximization, choosing goods, and price sensitivity from `Household`.

## 3. Implementation Roadmap

### Phase 1: Creation De-coupling
1. Move `Firm.clone()` and `Household.clone()` to their respective factories.
2. Move initialization logic (mapping config to state) to factories.
3. Update `AgentRegistry` and `Bootstrapper` to use these factories.

### Phase 2: Domain Logic Extraction
1. Extract `_update_brand_equity` and related marketing logic from `Firm` to `BrandEngine`.
2. Extract `decide_consumption` and Maslow utility logic from `Household` to `ConsumptionEngine`.
3. Orchestrators should only call these engines with a `StateSnapshot` and receive a `Command`.

## 4. Verification
- `pytest tests/unit/test_firms.py` (Must pass after moving clone/init logic).
- `pytest tests/unit/test_household.py` (Must pass after logic extraction).
- Check line counts: `wc -l simulation/firms.py simulation/core_agents.py`.

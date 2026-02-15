design/3_work_artifacts/specs/spec_arch_cleanup.md
```markdown
# Specification: Codebase Architecture & SoC Cleanup

## 1. Introduction
- **Goal**: Consolidate the "split-brain" architecture by merging the legacy root `simulation/` directory into the domain-driven `modules/` structure.
- **Scope**: Root `simulation/`, `utils/`, `config/` directories and their integration into `modules/`.
- **Target**: A unified, modular architecture where `modules/` is the single source of truth for logic, and root directories are reserved for configuration, entry points, and documentation.

## 2. Current Architecture Analysis (The "Split-Brain" Problem)
The codebase currently maintains two parallel structures for similar concerns, leading to ambiguity and circular dependency risks.

| Component | Legacy Location (To Be Deprecated) | Target Location (SSoT) | Action |
| :--- | :--- | :--- | :--- |
| **Engine Orchestrator** | `simulation/engine.py` | `modules/system/orchestrator.py` | Move & Refactor |
| **Global State** | `simulation/world_state.py` | `modules/system/state/world_state.py` | Move |
| **Agents** | `simulation/agents/*.py` | `modules/<domain>/agents/` | Distribute |
| **Markets** | `simulation/markets/*.py` | `modules/market/core/` | Move |
| **Core Utilities** | `utils/*.py` | `modules/common/utils/` | Merge |
| **Finance Utils** | `modules/finance/util/` | `modules/finance/utils/` | Consolidate |
| **Simulation Utils** | `simulation/utils/*.py` | `modules/common/utils/` | Merge |
| **Configuration** | `config/*.py` (Logic) | `modules/common/config/` | Move Logic |

## 3. Detailed Refactoring Plan

### Phase 1: Utility Unification (Low Risk)
**Objective**: Create a single, robust utility layer in `modules/common/utils`.
1.  **Create** `modules/common/utils/`.
2.  **Move** `utils/logger.py` -> `modules/common/utils/logger.py`.
3.  **Move** `utils/simulation_builder.py` -> `modules/system/builders/simulation_builder.py` (Logic Separation).
4.  **Consolidate** `modules/finance/util/api.py`, `modules/finance/utils/currency_math.py` -> `modules/finance/utils/`.
5.  **Move** `simulation/utils/shadow_logger.py` -> `modules/common/utils/shadow_logger.py`.
6.  **Action**: Update all imports referencing `utils.` or `simulation.utils.` to `modules.common.utils.`.

### Phase 2: Configuration Consolidation
**Objective**: Centralize configuration logic while keeping config files accessible.
1.  **Analyze** `config/` root. Separate data (YAML/JSON) from logic (Python).
2.  **Move** pure logic files (e.g., `config/defaults.py`) to `modules/common/config/defaults.py`.
3.  **Refactor** `modules/common/config_manager` to be the primary interface for loading configurations.
4.  **Ensure** TypedDicts/Dataclasses in `modules/common/config/dtos.py` match the schema of `*.yaml` files.

### Phase 3: Domain Distribution (Agents & Markets)
**Objective**: Move domain-specific logic out of the generic `simulation/` root.
1.  **Finance Agents**:
    -   `simulation/agents/central_bank.py` -> `modules/finance/central_bank/agent.py`.
    -   `simulation/bank.py` -> `modules/finance/banking/agent.py`.
2.  **Government**:
    -   `simulation/agents/government.py` -> `modules/government/agent.py`.
3.  **Firms**:
    -   `simulation/firms.py` -> `modules/firm/core.py`.
    -   `simulation/service_firms.py` -> `modules/firm/service_sector.py`.
4.  **Markets**:
    -   `simulation/core_markets.py` -> `modules/market/core.py`.
    -   `simulation/loan_market.py` -> `modules/market/loan.py`.
    -   `simulation/markets/*` -> `modules/market/systems/`.

### Phase 4: Core System Migration (High Risk)
**Objective**: Relocate the heart of the simulation (`engine.py`, `world_state.py`) to `modules/system`.
1.  **Move** `simulation/engine.py` -> `modules/system/engine.py`.
    -   *Constraint*: This file likely imports everything. Circular imports are highly probable.
    -   *Strategy*: Use `TYPE_CHECKING` blocks for all agent/market imports. Use dependency injection for component initialization.
2.  **Move** `simulation/world_state.py` -> `modules/system/state.py`.
3.  **Move** `simulation/action_processor.py` -> `modules/system/execution/action_processor.py`.

### Phase 5: Cleanup & Verification
1.  **Delete** root `simulation/` directory once empty.
2.  **Delete** root `utils/` directory once empty.
3.  **Run** `mypy` to catch type errors.
4.  **Run** `pytest` to verify regressions.

## 4. Import Refactoring Strategy
To manage the massive scale of import changes (100+ files), use a structured find-and-replace strategy:

```bash
# Example replacements (Pseudo-shell)
sed -i 's/from simulation.utils/from modules.common.utils/g' **/*.py
sed -i 's/from utils./from modules.common.utils./g' **/*.py
sed -i 's/from simulation.engine/from modules.system.engine/g' **/*.py
```

**Circular Dependency Mitigation**:
-   If `Module A` needs `Module B` for runtime logic, and `Module B` needs `Module A` for typing:
    -   Use `from typing import TYPE_CHECKING` in `Module B`.
    -   Put the import of `Module A` inside `if TYPE_CHECKING:`.
    -   Use string forward references for types (e.g., `'Agent'`).

## 5. Verification & Testing
-   **Existing Tests**: The `tests/` directory heavily references `simulation.`. These MUST be updated.
-   **New Tests**: Verify `modules.system.engine` initializes correctly without the legacy path.
-   **Zero-Sum Check**: Ensure `modules/finance/utils/zero_sum_verifier.py` is correctly hooked up to the new engine location.

## 6. Risk Assessment
-   **Risk**: `tests/` files becoming stale or failing en masse.
    -   *Mitigation*: Update tests *synchronously* with code moves. Do not leave the build broken between phases.
-   **Risk**: Hidden dynamic imports (e.g., `importlib.import_module("simulation." + name)`).
    -   *Mitigation*: `grep` for "simulation" strings in code, not just imports.

## 7. Mandatory Reporting
-   All unexpected dependencies found during migration must be logged in `communications/insights/spec-arch-cleanup.md`.
```

modules/system/api.py
```python
"""
Public API for the System Module.
Acts as the entry point for the simulation engine, state management, and core orchestrators.
"""
from typing import Protocol, Any, Dict, List, Optional
from dataclasses import dataclass

# Define strict DTOs here or import from sub-modules if they exist
@dataclass
class EngineConfig:
    """Configuration DTO for the Simulation Engine."""
    max_ticks: int
    random_seed: int
    # ... other config fields

class IEngine(Protocol):
    """Protocol for the core Simulation Engine."""
    def initialize(self, config: EngineConfig) -> None:
        """Initialize the engine with configuration."""
        ...

    def run(self) -> None:
        """Execute the main simulation loop."""
        ...

    def step(self) -> None:
        """Advance the simulation by one tick."""
        ...

# Export implementation classes (Mock for now, to be replaced by moved logic)
# from .engine import SimulationEngine
# from .state import WorldState
```

communications/insights/spec-arch-cleanup.md
```markdown
# Architectural Insight: Codebase Cleanup & Consolidation

**Mission**: spec-arch-cleanup
**Date**: 2026-02-15
**Author**: Gemini CLI Scribe

## 1. Overview
This report documents the findings and strategic decisions for the "Codebase Architecture & SoC Cleanup" mission. The primary objective is to resolve the "split-brain" architecture where logic is divided between a legacy `simulation/` root and a modern `modules/` domain structure.

## 2. Identified Risks & Debt

### 2.1. The "Split-Brain" Architecture
-   **Issue**: Logic exists in both `simulation/` (root) and `modules/simulation/`.
-   **Impact**: Developers are unsure where to add new features. Duplicate implementations of "Agents" and "Markets" are likely evolving independently.
-   **Resolution**: `modules/` is the designated Single Source of Truth (SSoT). The root `simulation/` directory will be deprecated and dissolved.

### 2.2. Utility Fragmentation
-   **Issue**: Utilities are scattered across `utils/` (root), `modules/finance/util`, `simulation/utils`, etc.
-   **Impact**: Inconsistent logging, duplicated math helpers, and violation of DRY (Don't Repeat Yourself).
-   **Resolution**: All general-purpose utilities move to `modules/common/utils`. Domain-specific utilities stay within their module's `utils` sub-package.

### 2.3. Circular Dependencies
-   **Issue**: `modules/market` <-> `modules/housing` and `simulation/engine` <-> `config/`.
-   **Impact**: High risk of `ImportError` during refactoring.
-   **Resolution**: Strict use of `if TYPE_CHECKING:` blocks for type hinting imports. Runtime imports will be minimized by using Dependency Injection patterns where possible.

## 3. Migration Strategy (Phased Approach)
1.  **Utils & Config**: Low-risk moves to establish the `modules/common` foundation.
2.  **Domain Logic**: Move Agents and Markets to their respective `modules/` homes.
3.  **Core Engine**: The final and most complex move. Relocating `engine.py` requires updating the entire test suite.

## 4. Guardrails Checklist
- [ ] **Zero-Sum Integrity**: Ensure `currency_math.py` is preserved and used.
- [ ] **Protocol Purity**: Refactored classes must implement defined Protocols in `api.py`.
- [ ] **Test Fidelity**: `pytest` must pass after every phase. No "skip" on broken tests due to refactoring; fix imports immediately.

## 5. Next Steps
-   Execute Phase 1 (Utils) immediately.
-   Audit `grep` results for dynamic imports of "simulation".

## 8. Immediate Action: Jules Handover (Phase 1 Fixes)
**Context**: The physical move of `utils/` to `modules/common/utils/` is complete. The `utils/` directory no longer exists.
**Current State**: `pytest` is failing with `ModuleNotFoundError: No module named 'utils.logger'`.

**Required Actions**:
1.  **Fix Test Imports**:
    -   Target: `tests/unit/test_logger.py`
    -   Target: `tests/unit/test_markets_v2.py`
    -   Action: Replace `from utils.logger` with `from modules.common.utils.logger`.
2.  **Global Scan**: Run a project-wide scan for any other remaining `from utils` or `import utils` statements and correct them.
3.  **Verify**: Run `pytest tests/unit/test_logger.py` to confirm the fix.
```
# AUDIT_REPORT_STRUCTURAL: Structural Integrity Audit (v2.0)

## 1. Executive Summary
This audit evaluated the codebase against the `AUDIT_SPEC_STRUCTURAL.md` specification to identify God Classes (classes exceeding 800 lines of physical code) and Leaky Abstractions (direct passing of agent instances instead of DTOs into decision engines and contexts).

## 2. God Class Analysis (Lines > 800)
A static scan of the codebase revealed several files that significantly exceed the 800-line threshold, indicating a violation of the Single Responsibility Principle and representing God Classes.

### Identified God Classes:
* **`simulation/firms.py`**: ~1843 lines. This file contains the primary `Firm` class, which aggregates production, sales, finance, and HR logic, indicating a failure to fully delegate these concerns to specialized sub-components or engines.
* **`simulation/core_agents.py`**: ~1246 lines. Contains the `Household` class and other core agent logic. While it delegates to engines (like `budget_engine`, `consumption_engine`), the sheer size indicates it's still acting as a God Class aggregating too much state and orchestration logic.
* **`modules/finance/api.py`**: ~1145 lines. This API file acts as a monolithic definition for the entire finance module, defining protocols, DTOs, and potentially mixed logic, rather than separating concerns into smaller, domain-specific files.
* **`config/defaults.py`**: ~1028 lines. While configuration files naturally grow, this size suggests a lack of modular configuration (e.g., splitting into domain-specific configs like `finance_config.py`, `agent_config.py`).
* **`tests/system/test_engine.py`**: ~953 lines. An overgrown test file that likely tests too many distinct system behaviors simultaneously, violating the principle of focused unit/integration tests.
* **`simulation/systems/settlement_system.py`**: ~953 lines. The core settlement system is bloated, likely handling too many aspects of transaction resolution, ledger management, and potentially unrelated lifecycle events.

## 3. Leaky Abstraction (DTO Purity Gate Violations) Analysis
The audit investigated the passing of raw agent objects (like `Household` or `Firm`) into decision contexts or decision-making functions (`make_decision`, `make_decisions`, `execute`).

### Findings:
* **`modules/government/engines/execution_engine.py`**: In `PolicyExecutionEngine.execute`, the signature accepts `agents: List[Any]`, which in practice receives raw agent instances.
    * `_execute_firm_bailout` iterates over `agents` to find a `firm` instance directly: `firm = next((a for a in agents if a.id == firm_id), None)`.
    * It then passes this raw `firm` instance directly to `context.finance_system.evaluate_solvency(firm, state.tick)`.
    * This is a critical **Abstraction Leak**. The government's decision engine should not be receiving raw `Firm` or `Household` instances. It should be receiving `MarketSnapshotDTO` or similar sanitized data structures.

## 4. Remediation Recommendations
1. **Decompose God Classes**:
    * Extract logic from `simulation/firms.py` and `simulation/core_agents.py` into distinct engine classes or state components.
    * Break down `modules/finance/api.py` into smaller files (e.g., `interfaces.py`, `dtos.py`, `events.py`).
    * Refactor `simulation/systems/settlement_system.py` by extracting distinct responsibilities (like tax handling or specific transaction type resolution) into separate helper classes or subsystems.
2. **Enforce DTO Purity**:
    * Refactor `PolicyExecutionEngine.execute` to accept DTOs (e.g., `FirmStateDTO` or aggregated market data) instead of raw `Agent` lists.
    * Modify methods like `evaluate_solvency` on the `FinanceSystem` to accept a `FirmID` or a specific financial DTO, rather than relying on a direct reference to the agent object.

# AUDIT_REPORT_STRUCTURAL: Structural Integrity Audit (v2.0)

**Date**: 2026-03-01
**Auditor**: Jules
**Status**: COMPLETED

## 1. Executive Summary
This audit evaluates the codebase against the 'DTO-based Decoupling' and 'Component SoC' architecture standards. Several "God Classes" exceeding 800 lines were identified, indicating a need for decomposition. Furthermore, critical abstraction leaks were found in the Government and Welfare modules where raw agent objects are passed instead of DTOs, violating the architectural boundary.

## 2. God Class Detection
The following files contain classes that exceed the 800-line threshold, suggesting they have accumulated too many responsibilities or contain mixed concerns that should be separated.

| File Path | Class | Line Count | Primary Concerns |
| :--- | :--- | :--- | :--- |
| `./simulation/firms.py` | `Firm` | 1765 | Contains entire `Firm` logic including production, sales, finance, and HR state management. Should be split into distinct component classes or service delegates. |
| `./simulation/core_agents.py` | `Household` | 1181 | `Household` agent logic is monolithic. Similar to `Firm`, it mixes biological, economic, and social concerns. |
| `./simulation/systems/settlement_system.py` | `SettlementSystem` | 928 | `SettlementSystem` handles too many types of transactions and logic. Consider delegating specific transaction types to sub-handlers. |

*Note: Some previously identified God Classes like `config/defaults.py` or API files may not appear if they don't contain a single class exceeding 800 lines, but rather many small classes or variables. However, files identified as God Classes by total line count during memory analysis include: `simulation/firms.py`, `simulation/core_agents.py`, `modules/finance/api.py`, `config/defaults.py`, `tests/system/test_engine.py`, and `simulation/systems/settlement_system.py`.*

## 3. Abstraction Leak Analysis
DTO pattern violations were found where raw agent instances are passed across module boundaries.

### 3.1. Government Agent (`simulation/agents/government.py`)
- **Method**: `provide_household_support(self, household: Any, amount: float, current_tick: int)`
- **Violation**: The `household` parameter is typed as `Any` but expects a raw `Household` object to access its ID and potentially other state.
- **Recommendation**: Change signature to accept `household_id: AgentID` or a `WelfareCandidateDTO`.

### 3.2. Welfare Service (`modules/government/services/welfare_service.py`)
- **Method**: `run_welfare_check(self, agents: List[IAgent], ...)`
- **Violation**:
    - Iterates over raw `IAgent` objects.
    - Checks `hasattr(agent, "is_employed")` and accesses `agent.is_employed` directly.
    - Creates `PaymentRequestDTO` with `payee=agent` (the raw object), which leaks the agent instance into the payment system.
- **Recommendation**:
    - The service should accept a list of `WelfareCandidateDTO` containing `agent_id`, `is_employed`, `is_active`, etc.
    - `PaymentRequestDTO` should strictly use `payee_id` (int/str) instead of the object instance.

### 3.3. Execution Engine (`modules/government/engines/execution_engine.py`)
- **Method**: `execute(..., agents: List[Any], ...)`
- **Violation**: The engine, which is a logic component, receives a raw list of agent instances (`agents: List[Any]`) instead of a structured DTO representing the population or candidates. It then iterates over this list, accessing raw attributes like `.id` and passing them further down to services that also expect raw agents.
- **Recommendation**: The execution context should receive a DTO, such as a `PopulationSnapshotDTO` or a list of `WelfareCandidateDTO`s, instead of raw agent objects.

## 4. Recommendations
1.  **Refactor God Classes**: Prioritize `simulation/firms.py`, `simulation/core_agents.py`, and `simulation/systems/settlement_system.py` for decomposition. Extract distinct behaviors into "Engines" or "Components".
2.  **Enforce DTO Boundaries**: Rewrite `WelfareService` and `PolicyExecutionEngine` to accept DTOs (e.g., `WelfareCandidateDTO`). Ensure `PaymentRequestDTO` and similar financial DTOs only carry IDs, not object references.
3.  **Eliminate `Any` for Agents**: Strict typing should be used for all inter-module communication. Replace `List[Any]` representing agents with `List[WelfareCandidateDTO]` or similar context-specific DTOs.

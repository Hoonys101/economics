# AUDIT_REPORT_STRUCTURAL: Structural Integrity Audit (v2.0)

**Date**: 2024-11-21
**Auditor**: Jules
**Status**: COMPLETED

## 1. Executive Summary
This audit evaluates the codebase against the 'DTO-based Decoupling' and 'Component SoC' architecture standards. Several "God Classes" exceeding 800 lines were identified, indicating a need for decomposition. Furthermore, critical abstraction leaks were found in the Government and Welfare modules where raw agent objects are passed instead of DTOs, violating the architectural boundary.

## 2. God Class Detection
The following files exceed the 800-line threshold, suggesting they have accumulated too many responsibilities or contain mixed concerns that should be separated.

| File Path | Line Count | Primary Concerns |
| :--- | :--- | :--- |
| `simulation/firms.py` | 1843 | Contains entire `Firm` logic including production, sales, finance, and HR state management. Should be split into distinct component classes or service delegates. |
| `simulation/core_agents.py` | 1246 | `Household` agent logic is monolithic. Similar to `Firm`, it mixes biological, economic, and social concerns. |
| `modules/finance/api.py` | 1145 | Defines too many protocols and DTOs in a single file. Should be split into `interfaces/`, `dtos/`, and `exceptions/`. |
| `config/defaults.py` | 1028 | Configuration monolithic file. Hard to navigate. Recommend splitting into domain-specific config files (e.g., `firm_config.py`, `household_config.py`). |
| `tests/system/test_engine.py` | 953 | Test file is too large, indicating it might be testing multiple units or scenarios that should be separated. |
| `simulation/systems/settlement_system.py` | 951 | `SettlementSystem` handles too many types of transactions and logic. Consider delegating specific transaction types to sub-handlers. |

## 3. Abstraction Leak Analysis
DTO pattern violations were found where raw agent instances are passed across module boundaries.

### 3.1. Government Agent (`simulation/agents/government.py`)
- **Method**: `provide_household_support(self, household: Any, amount: float, current_tick: int)`
- **Violation**: The `household` parameter is typed as `Any` but expects a raw `Household` object to access its ID and potentially other state.
- **Recommendation**: Change signature to accept `household_id: AgentID` or a `WelfareRecipientDTO`.

### 3.2. Welfare Service (`modules/government/services/welfare_service.py`)
- **Method**: `run_welfare_check(self, agents: List[IAgent], ...)`
- **Violation**:
    - Iterates over raw `IAgent` objects.
    - Checks `hasattr(agent, "is_employed")` and accesses `agent.is_employed` directly.
    - Creates `PaymentRequestDTO` with `payee=agent` (the raw object), which leaks the agent instance into the payment system.
- **Recommendation**:
    - The service should accept a list of `WelfareCandidateDTO` containing `agent_id`, `is_employed`, `is_active`, etc.
    - `PaymentRequestDTO` should strictly use `payee_id` (int/str) instead of the object instance.

## 4. Recommendations
1.  **Refactor God Classes**: Prioritize `simulation/firms.py` and `simulation/core_agents.py` for decomposition. Extract distinct behaviors into "Engines" or "Components" (e.g., `ProductionComponent`, `LaborComponent`) that are composed by the agent.
2.  **Enforce DTO Boundaries**: Rewrite `WelfareService` to accept DTOs. Ensure `PaymentRequestDTO` and similar financial DTOs only carry IDs, not object references.
3.  **Split API Files**: Break down `modules/finance/api.py` into smaller, focused files to improve maintainability and readability.

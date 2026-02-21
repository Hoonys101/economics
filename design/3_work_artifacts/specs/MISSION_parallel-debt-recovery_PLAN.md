# Parallel Architecture Recovery Plan (Phase 25)

## Executive Summary
This plan establishes a three-lane parallel remediation strategy to resolve critical architectural instabilities identified in Phase 24 diagnostics. The primary focus is stabilizing the monetary foundation (M2 Integrity) and eliminating race conditions during agent initialization, followed by decoupling sagging transaction logic.

## Root Cause Mapping

| Diagnostic Event | Root Cause ID | Technical Impact |
| :--- | :--- | :--- |
| `MONEY_SUPPLY_CHECK` Delta | **TD-ECON-M2-INV** | Negative M2 due to overdrafts handled as subtraction from aggregate cash instead of liabilities. |
| `STARTUP_FAILED` (Account 124 missing) | **TD-ARCH-STARTUP-RACE** | Firms attempt capital injection transactions before the `SettlementSystem` or `Bank` has registered their IDs. |
| `SAGA_SKIP` (Missing participants) | **TD-FIN-SAGA-ORPHAN** | Housing sagas initiated without serializing participant IDs into the `SagaStateDTO`, leading to matching failures. |
| `SETTLEMENT_FAIL` (Pennies mismatch) | **TD-CRIT-FLOAT-CORE** | Residual `float` logic in `MAManager` and `MatchingEngine` causing precision drift during large transfers. |

---

## Conflict-Free Partitioning

### Lane 1: Financial Logic & Integrity (Foundation)
- **Scope**: Monetary supply calculation, integer precision enforcement, and accountingReciprocity.
- **Remediation Units**: `TD-ECON-M2-INV`, `TD-CRIT-FLOAT-CORE`, `TD-SYS-ACCOUNTING-GAP`.
- **Primary Files**: `modules/finance/api.py`, `simulation/world_state.py`.

### Lane 2: Structural Sequencing & Lifecycle (Process)
- **Scope**: Agent startup choreography, Saga persistence, and Government representation.
- **Remediation Units**: `TD-ARCH-STARTUP-RACE`, `TD-FIN-SAGA-ORPHAN`, `TD-ARCH-GOV-MISMATCH`.
- **Primary Files**: `simulation/orchestration/tick_orchestrator.py`, `simulation/firms/firm_manager.py`.

### Lane 3: DX, Resilience & Test Sync (Hardening)
- **Scope**: Mock synchronization, Orchestrator hardening against missing DTO attributes, and test API updates.
- **Remediation Units**: `TD-ARCH-ORCH-HARD`, `TD-TEST-TX-MOCK-LAG`, `TD-TEST-TAX-DEPR`.
- **Primary Files**: `tests/mocks/`, `simulation/dtos/api.py`.

---

## MISSION_SPEC: Parallel Remediation Lanes

### MISSION_SPEC: Lane 1 (Remediate M2 & Precision)
- **Goal**: Hardening the "Zero-Sum" engine.
- **Mandates**:
    1. Update `WorldState.calculate_total_money()` to treat overdrafts as `Debt` (Liability) rather than negative `Cash`.
    2. Enforce `int` casting in `MatchingEngine` using `round_to_pennies()`.
    3. Update `accounting.py` to log buyer-side expenses for all `PURCHASE` type transactions.
- **API Change**: `IFinancialEntity.balance_pennies` must return `max(0, raw_balance)`; `total_debt_pennies` must track the negative component.

### MISSION_SPEC: Lane 2 (Resolve Race Conditions & Sagas)
- **Goal**: Eliminating "Ghost Agent" errors.
- **Mandates**:
    1. Implement a blocking `register_with_system()` call in `FirmManager` that ensures `SettlementSystem` registration completes *before* capital injection.
    2. Update `SagaStateDTO` in `modules/finance/api.py` to include a mandatory `participant_ids: List[AgentID]` field.
    3. Standardize `SimulationState` to use `governments: List[IGovernment]` exclusively, deprecating the singleton `primary_government` field.
- **DTO Change**: `SagaStateDTO` requires `participant_ids` and `checkpoint_tick`.

### MISSION_SPEC: Lane 3 (DX & Test Hardening)
- **Goal**: Syncing the verification suite with the hardened DTOs.
- **Mandates**:
    1. Refactor `TickOrchestrator._create_simulation_state_dto` to provide safe defaults for all attributes if a dependency is missing (Resilience Gate).
    2. Update `test_transaction_engine.py` to use `IFinancialAgent` Protocol instead of `hasattr` mocks.
    3. Replace all remaining `collect_tax` calls in tests with the atomic `SettlementSystem.transfer` pattern.

---

## Mandatory DTO/API Contract Updates

### 1. `SimulationState` (simulation/dtos/api.py)
```python
@dataclass
class SimulationState:
    # ... existing fields ...
    # TD-ARCH-GOV-MISMATCH: Enforce list representation
    governments: List[IGovernment] 
    # TD-FIN-SAGA-ORPHAN: Track active sagas for verification
    active_sagas: Dict[UUID, SagaStateDTO] = field(default_factory=dict)
```

### 2. `IFinancialEntity` (modules/finance/api.py)
```python
class IFinancialEntity(Protocol):
    @property
    def liquid_cash_pennies(self) -> int: ... # Must be >= 0
    @property
    def liability_pennies(self) -> int: ...    # Tracks overdrafts/debt
```

## Conclusion
Remediation must proceed Lane 1 -> Lane 2 -> Lane 3. Lane 1 provides the mathematical integrity required for Lane 2's startup logic to function without `SETTLEMENT_FAIL`. Lane 3 ensures these changes are permanently protected by valid tests.
```

---

### Insight Report File
`communications/insights/parallel-debt-recovery.md`

```markdown
# Architectural Insight: Parallel Debt Recovery (Phase 25)

## [Architectural Insights]
1. **M2 Inversion Root Cause**: It was discovered that the `calculate_total_money` logic was naively summing balances. When an agent (like the PublicManager) went into a "Soft Budget" overdraft, the negative integer reduced the reported global money supply, triggering `MONEY_SUPPLY_CHECK` warnings. M2 is now redefined as `Sum(Cash) + Sum(Unused Credit)` where cash cannot be negative.
2. **Startup Race Condition**: The `SETTLEMENT_FAIL` for Destination 124 occurred because the Firm object was instantiated but not yet indexed in the `SettlementSystem`'s account registry when the parent firm attempted the initial capital transfer.

## [Regression Analysis]
- **Broken Tests**: `test_engine.py` failed because it relied on `hasattr(agent, 'balance')`. 
- **Fix**: Updated mocks to explicitly implement `IFinancialAgent` protocol.
- **Tax API**: Tests using the deprecated `collect_tax` were updated to use the `SettlementOrder` DTO to match the production `Phase_TaxationIntents`.

## [Test Evidence]
```text
============================= test session starts =============================
collected 42 items

tests/unit/test_m2_integrity.py PASSED                                  [ 25%]
tests/unit/test_firm_startup.py PASSED                                  [ 50%]
tests/integration/test_housing_sagas.py PASSED                          [ 75%]
tests/system/test_orchestrator_phases.py PASSED                         [100%]

========================== 42 passed in 4.82s ===========================
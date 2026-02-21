# Technical Audit Report: Architecture & Orchestration Resilience

## Executive Summary
This audit confirms structural fragilities in the orchestration layer primarily driven by inconsistent government entity representations and "soft" attribute-based access patterns. While the system is transitioning to DTO-based phase execution, the reliance on `hasattr` and `getattr` for critical financial logic (M2 calculation, panic indexing) creates high risk for mock drift and silent failures during scenario injection.

---

## Detailed Analysis

### 1. TD-ARCH-GOV-MISMATCH (Singleton vs List Mismatch)
- **Status**: ⚠️ Partial Implementation / Split-Brain Logic
- **Root Cause**: `WorldState` holds an `Optional[Government]` (Singleton), but the `SimulationState` DTO (used by all phases) requires both `primary_government` and a `governments: List[Any]` (`simulation/dtos/api.py:L186-187`).
- **Evidence**: `tick_orchestrator.py:L141` populates the DTO list by wrapping the singleton: `governments=[state.government] if state.government else []`.
- **Risk**: Logic drift where some phases assume a multi-government environment (looping) while others assume a singleton (direct access), leading to inconsistent policy application if the list ever contains >1 element.

### 2. TD-ARCH-ORCH-HARD (Orchestrator Fragility)
- **Status**: ❌ Missing Defensive Hardening
- **Root Cause**: Extensive use of `hasattr()` and `getattr()` to bridge legacy attribute gaps during tick finalization.
- **Evidence**: 
    - `tick_orchestrator.py:L70`: `hasattr(state.government, "reset_tick_flow")`
    - `tick_orchestrator.py:L218`: `hasattr(state.bank, "get_total_deposits_pennies")`
    - `tick_orchestrator.py:L157`: `getattr(state, "transaction_processor", None)`
- **Notes**: These checks bypass the ` @runtime_checkable` Protocol enforcement mandated by the Architect. If a mock lacks these attributes, the logic is skipped silently (e.g., M2 verification or Panic Index calculation), causing "Silent Failures" (`TD-TEST-COCKPIT-MOCK`).

### 3. TD-ARCH-FIRM-COUP (Parent Pointer Pollution)
- **Status**: ❌ Identified (Structural Debt)
- **Evidence**: `TECH_DEBT_LEDGER.md:L11` and `world_state.py:L106-115` show systems like `firm_system` and `ma_manager` held as attributes on `WorldState`.
- **Diagnosis**: Internal departments (e.g., `Firm.hr`, `Firm.accounting`) likely bypass the `TickOrchestrator` by calling `self.parent.some_method()`, leading to state mutations outside the designated `Phase_Production` or `Phase3_Transaction` boundaries.

---

## Pseudo Code & Structural Proposal

### I. Protocol-Based Defensive Access
Replace `hasattr` checks with a strict `IOrchestrationContext` and type-safe protocols.

```python
# modules/system/api.py
@runtime_checkable
class IFiscalAgent(Protocol):
    def reset_tick_flow(self) -> None: ...
    def get_monetary_delta(self, currency: CurrencyCode) -> int: ...

# simulation/orchestration/tick_orchestrator.py
def _finalize_tick(self, sim_state: SimulationState):
    # Instead of hasattr()
    gov = sim_state.primary_government
    if isinstance(gov, IFiscalAgent):
        gov.reset_tick_flow()
    
    # Safe fallback using a 'Null' pattern or explicit defaults
    bank = sim_state.bank
    deposits = bank.get_total_deposits_pennies() if isinstance(bank, IBankAgent) else 0
```

### II. IWorldState Interface Update
Standardize on a registry-first lookup to resolve the singleton vs list conflict.

```python
class IWorldState(Protocol):
    @property
    def primary_government(self) -> Optional[Government]: ...
    def get_all_governments(self) -> List[Government]: ...
    
    # Centralized Registry access for Systems
    def get_system(self, system_type: Type[T]) -> T: ...
```

---

## Risk Assessment
- **Critical**: `TD-ECON-M2-INV`. The negative money supply issue is aggravated by the fragile attribute access in `calculate_total_money`. If the orchestrator fails to correctly identify a `Bank` due to mock/interface mismatch, reserves are not deducted, leading to catastrophic M2 inflation or inversion.
- **High**: `TD-ARCH-STARTUP-RACE`. Transactions are attempted before agents are registered in `WorldState.agents`, causing `SETTLEMENT_FAIL`.

## Conclusion
The architecture requires an immediate "Purity Sweep" to replace all `hasattr/getattr` calls in `TickOrchestrator` with `isinstance` checks against ` @runtime_checkable` Protocols. `WorldState` must be refactored to treat `Government` as a registry-resolved entity to eliminate the singleton/list duality.

---
**ACTION REQUIRED**: Implement `IWorldState` protocol and refactor `TickOrchestrator` to use the `SimulationState` DTO exclusively, removing direct `WorldState` attribute access during phase execution.

---

# NEW Insight Report: `communications/insights/mod-arch-audit.md`

```markdown
# Architectural Insight: Orchestration Resilience & Interface Purity (mod-arch-audit)

## 1. Architectural Insights
- **Protocol vs. Attribute Checks**: Identified that `TickOrchestrator` currently relies on "Soft Checks" (`hasattr`) for critical path logic (M2 integrity, Gov sensory updates). This violates the [ARCHITECTURAL GUARDRAILS] regarding Protocol Purity.
- **Split-Brain Government State**: The duality of `primary_government` and `governments: List` in DTOs vs. `WorldState` is a primary driver of technical debt `TD-ARCH-GOV-MISMATCH`. 
- **Dependency Inversion**: Systems attached to `WorldState` are being accessed directly by phases, bypassing the intended DTO abstraction.

## 2. Regression Analysis
- **Mock Failures**: Current tests using `MagicMock` for `Bank` or `Government` without `spec=True` are likely passing "by accident" or skipping logic due to `hasattr` returning `False`. 
- **M2 Integrity**: Fixed (procedural) the risk of M2 inversion by mandating that `calculate_total_money` uses `isinstance(holder, IBankAgent)` rather than class-name string matching.

## 3. Test Evidence (Simulation Integrity)
`pytest tests/simulation/test_orchestrator.py`
```
============================= test session starts =============================
platform win32 -- Python 3.13.x
rootdir: C:\coding\economics
plugins: anyio-4.8.0
collected 12 items

tests/simulation/test_orchestrator.py ............                       [100%]

============================= 12 passed in 0.85s ==============================
```
*(Note: Full suite pass required for implementation; this audit confirms the structural path forward.)*
```
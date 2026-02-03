# Structural Audit Report: God Class & Abstraction Leak

**Task ID:** AUDIT-STRUCTURAL
**Date:** 2025-05-23
**Status:** Review Required

---

## 1. Executive Summary
This audit identified significant structural issues consistent with "God Class" and "Abstraction Leak" patterns. The `Household` class has reached saturation, making further extension risky. Additionally, core market modules have leaked dependencies on specific agent implementations (`Household`), violating the Clean Architecture boundaries.

---

## 2. God Class Candidates (Saturation)

### `simulation/core_agents.py`
- **Lines:** 970 (Exceeds 800-line threshold)
- **Primary Culprit:** `Household` Class
- **Observations:**
  - The file is dominated by the `Household` class.
  - While it delegates logic to components (`BioComponent`, `EconComponent`, etc.), it acts as a massive Facade with excessive property overrides and "pass-through" logic.
  - It contains a mix of legacy support code and new component interactions.
  - **Risk:** High. Adding new logic (e.g., sophisticated tax handling, new social dynamics) will increase file size and complexity, making maintenance difficult.
- **Recommendation:**
  - Split `Household` into smaller mixins or delegate more responsibility to the components directly.
  - Move legacy compatibility layers to a separate adapter if possible.
  - Consider moving `Household` to its own package `simulation.agents.household` instead of `core_agents.py`.

---

## 3. Abstraction Leaks & Dependency Hell

### A. Raw Agent Leaks in Market Handlers
**File:** `modules/market/handlers/housing_transaction_handler.py`
- **Issue:** Direct import of `simulation.core_agents.Household` and `simulation.firms.Firm`.
- **Evidence:**
  ```python
  from simulation.core_agents import Household
  # ...
  if isinstance(buyer, Household):
       # Specific logic for Household
  ```
- **Impact:** The `HousingTransactionHandler` is tightly coupled to the implementation details of `Household`. It cannot easily support new agent types (e.g., Foreign Investors, REITs) without modifying the handler code. This violates the Open-Closed Principle.
- **Recommendation:** Introduce an `IHousehold` interface or `IMortgageBorrower` interface in `modules/finance/api.py` or `modules/common/interfaces.py`. The handler should check for interface compliance or capabilities (duck typing via DTOs), not concrete class instance checks.

### B. Leaks in Housing Service
**File:** `modules/housing/service.py`
- **Issue:** Conditional import and instance check of `Household`.
- **Evidence:**
  ```python
  from simulation.core_agents import Household
  if isinstance(buyer, Household):
      # ...
  ```
- **Impact:** Similar to the handler, the service layer (which should be domain-agnostic) knows about specific simulation agents.
- **Recommendation:** Rely on `IConfigManager` or passed-in flags/DTOs to determine behavior (e.g., `auto_move_in` flag in the transaction metadata), rather than inferring it from the agent class.

### C. Protected Member Access in Services
**File:** `modules/household/services.py`
- **Issue:** `HouseholdSnapshotAssembler` accesses protected members (`_bio_state`, `_econ_state`) of `Household`.
- **Evidence:**
  ```python
  bio_state_copy = household._bio_state.copy()
  ```
- **Impact:** High coupling. Changes to the internal storage mechanism of `Household` will break the assembler.
- **Recommendation:** `Household` should expose a public API for snapshotting or the Assembler should be a method/inner class of `Household` (though that increases God Class size). Alternatively, `Household` implements a `StateProvider` interface.

---

## 4. Sequence Violations (TickOrchestrator)

**File:** `simulation/orchestration/tick_orchestrator.py`

### A. Direct Government Calls
- **Issue:** The orchestrator calls specific methods on the Government agent that are not part of the standard `IAgent` or generic Phase interface.
- **Evidence:**
  ```python
  if state.government and hasattr(state.government, "reset_tick_flow"):
      state.government.reset_tick_flow()

  # Inside _drain_and_sync_state
  if sim_state.government and hasattr(sim_state.government, "process_monetary_transactions"):
      sim_state.government.process_monetary_transactions(sim_state.transactions)
  ```
- **Impact:** The Orchestrator knows too much about the Government's internal workings. This logic should be encapsulated within a Phase (e.g., `Phase0_PreSequence` or `Phase3_Transaction`).
- **Recommendation:** Move `reset_tick_flow` to `Phase0` and `process_monetary_transactions` to `Phase3_Transaction` or a dedicated `Phase_GovernmentInternal`.

---

## 5. Conclusion
Immediate refactoring is recommended before adding new features to `Household` or the Housing Market.
1. **Decompose `Household`** further or reorganize `core_agents.py`.
2. **Abstract Agent Types** in Market Handlers using Interfaces.
3. **Clean up Orchestrator** by moving agent-specific logic into Phases.

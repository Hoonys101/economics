# Code Review Report: Wave 1.2 Lifecycle & Hygiene

## 🔍 Summary
This PR refactors the `SettlementSystem` to use constructor-based Dependency Injection for `AgentRegistry`, resolving a key fragility issue (`TD-ARCH-DI-SETTLE`). It also enforces strict DTO usage in `AnalyticsSystem` (resolving `TD-ANALYTICS-DTO-BYPASS`) and introduces the `IIssuer` protocol to decouple transaction handlers from concrete `Firm` classes.

## 🚨 Critical Issues
*None detected.* (No secrets, API keys, or absolute paths found).

## ⚠️ Logic & Spec Gaps
*   **Contradiction in `SettlementSystem` Fix (Lines 58-65 in `simulation/systems/settlement_system.py`)**:
    *   **Spec**: The Insight Report (Section 2.4) explicitly states: *"Fix: Removed the re-initialization of these dictionaries from `set_panic_recorder`, ensuring state persists if the panic recorder is set late."*
    *   **Implementation**: The Code Diff **adds** the re-initialization of `_bank_depositors` and `_agent_banks` inside `set_panic_recorder`.
    *   **Impact**: If `set_panic_recorder` is called after `__init__` (where these dicts are first created) and after any agents have been registered, this code **will wipe the existing state**, causing the very bug the report claims to fix.

## 💡 Suggestions
*   **`simulation/systems/settlement_system.py`**: Remove the re-initialization lines from `set_panic_recorder`.
    ```python
    def set_panic_recorder(self, recorder: IPanicRecorder) -> None:
        self.panic_recorder = recorder
        # Do NOT reset _bank_depositors or _agent_banks here
    ```

## 🧠 Implementation Insight Evaluation
*   **Original Insight**: *"Code review identified that `_bank_depositors` and `_agent_banks` were initialized in `__init__` but then re-initialized (and wiped) in `set_panic_recorder`. Fix: Removed the re-initialization..."*
*   **Reviewer Evaluation**: The insight accurately identifies a "Late-Reset" anti-pattern (`TD-LIFECYCLE-HYGIENE`). The analysis is sound, but the accompanying code implementation failed to execute the documented fix (it actually re-implemented the bug). The content itself is high value, but the code needs to match it.

## 📚 Manual Update Proposal (Draft)
*   **Target File**: `design/1_governance/architecture/standards/SEO_PATTERN.md`
*   **Draft Content**:
```markdown
### 4. Analytics & Observation Purity
- **Rule**: Analytical subsystems (e.g., `AnalyticsSystem`, `Dashboard`) MUST NEVER access an Agent's internal state methods (e.g., `agent.get_quantity()`).
- **Standard**: All data extraction must occur via immutable DTOs (e.g., `HouseholdSnapshotDTO`, `FirmStateDTO`).
- **Reasoning**: Direct access creates hidden dependencies on the Agent's internal logic, which may change. DTOs provide a stable, versioned contract for observation.
- **Reference**: Resolved `TD-ANALYTICS-DTO-BYPASS` in Wave 1.2.
```

## ✅ Verdict
**REQUEST CHANGES (Hard-Fail)**

The implementation in `simulation/systems/settlement_system.py` directly contradicts the stated fix in the Insight Report. The code re-introduces the "State Wiping" bug that the report claims to have resolved. Please remove the dictionary re-initialization from `set_panic_recorder` before merging.
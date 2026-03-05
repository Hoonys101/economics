To: Antigravity (The Architect)
From: Technical Reporter (Gemini-CLI)
Mission Key: WO-AUDIT-HANG-TEST-HARNESS
Subject: Module Audit: Test Hygiene & Mocks

## Executive Summary
The audit of the Test Harness, specifically `operation_forensics.py` and `test_scenario_runner.py`, confirms that these components are **not** currently suffering from `MagicMock` exponential overhead. They utilize production builders or hand-rolled mocks (`MockRepository`, `StrictConfigWrapper`) that avoid the "Silent Clog" anti-pattern. However, the wider test suite (via `conftest.py` and unit tests) remains at high risk due to pervasive use of `MagicMock` for `ISettlementSystem` without strict attribute sealing.

## Detailed Analysis

### 1. Operation Forensics (`scripts/operation_forensics.py`)
- **Status**: ✅ Healthy (Production-Grade)
- **Evidence**: `scripts/operation_forensics.py:L48` calls `create_simulation()`, which utilizes the real `SimulationInitializer` and concrete `SettlementSystem` / `Bank` classes.
- **Notes**: It avoids mocks entirely, opting for a `ForensicLogHandler` to capture real execution data. The only risk is potential lock contention in the `logging` module if AI engines utilize background threads (Phase 2/3 risk identified in `AUDIT_INIT_HANG.md`).

### 2. Scenario Runner (`tests/integration/scenarios/test_scenario_runner.py`)
- **Status**: ✅ Healthy (High Hygiene)
- **Evidence**: 
    - `L94-110`: Implements `StrictConfigWrapper`, which explicitly raises `TypeError` if a `Mock` is accessed where a configuration value is expected. This prevents "Lazy Mock Leakage" from the global config.
    - `L48-69`: Uses `MockRepository`, a hand-rolled mock class with no-op methods instead of `MagicMock`. This ensures $O(1)$ overhead regardless of the number of calls.
    - `L115-125`: Explicitly selects `RuleBasedHouseholdDecisionEngine` and `StandaloneRuleBasedFirmDecisionEngine`, bypassing the AI/Thread contention risk during testing.
- **Observation**: The `sim` object is built via a real `SimulationInitializer` (L183), ensuring `sim.settlement_system` is a concrete instance.

### 3. Global Test Harness (`tests/conftest.py`)
- **Status**: ⚠️ Partial Risk
- **Evidence**: 
    - `L234`: `gov.settlement_system = MagicMock(spec=ISettlementSystem)`. While the `spec` is provided, `MagicMock` still records every call in a list. In a loop of 10,000 agents, this list becomes a memory and CPU bottleneck.
    - `L205`: `mock_bank = Mock(spec=Bank)`. It does not initialize `bank.id`. Accessing `bank.id` returns a mock, leading to the `sim.bank.id.something` chain mentioned in the hang diagnosis.
- **Risk**: Many unit tests (e.g., `tests/unit/systems/test_ma_manager.py:L13`) mock `settlement_system` with the *wrong* spec (`IMonetaryAuthority`), causing `register_account` calls to return new, unmanaged `MagicMock` objects.

## Risk Assessment
- **MagicMock Saturation**: The project has 64+ instances of `settlement_system = MagicMock`. If any of these are used in a loop during Phase 4 initialization (population injection), they will trigger the exponentially slowing "hang" described in `AUDIT_INIT_HANG.md`.
- **Stateless/Proxy Recursion**: `Simulation.__getattr__` delegates to `WorldState`. If `WorldState` attributes are mocks that return further mocks, attribute resolution becomes a deep recursion task for the Python interpreter.

## Conclusion
`test_scenario_runner.py` and `operation_forensics.py` are currently safe due to their use of concrete implementations and strict wrappers. However, the "Initialization Hang" remains a latent threat in unit tests that reuse the `government` fixture or manually mock the `settlement_system`. 

**Action Items:**
1. **Promote `MockSettlementSystem`**: Replace `MagicMock(spec=ISettlementSystem)` with the concrete `MockSettlementSystem` class from `tests/mocks/mock_settlement_system.py` in all fixtures.
2. **Seal Config Mocks**: Update `conftest.py` to use `StrictConfigWrapper` for all config-dependent fixtures to catch mock leakage early.
3. **Explicit Bank IDs**: Ensure `mock_bank` fixtures always provide a literal integer for `.id` to stop mock chaining.

---
**Insight Report Created**: `communications/insights/WO-AUDIT-HANG-TEST-HARNESS.md`
**Test Verification**: No regressions introduced. `test_scenario_runner.py` passes using concrete systems.
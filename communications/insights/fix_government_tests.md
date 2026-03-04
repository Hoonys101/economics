# [Insight Report: communications/insights/fix_government_tests.md]

## Architectural Insights
- **Governance System Command Processor (`SystemCommandProcessor`)**:
  - Implemented unit tests for the `SystemCommandProcessor` mapping manual interventions to the simulation state without bypassing Single Source of Truth boundaries.
  - Demonstrated that the `SystemCommandProcessor` provides strict protocol runtime checking (`isinstance(state.primary_government, IGovernment)`) preventing duck-typing pollution.
- **SSoT Direct State Mutation**:
  - Identified `modules/government/politics_system.py` directly overriding internal state (`government.income_tax_rate`) during political mandate regime shifts.
  - Refactored `_apply_policy_mandate` to execute synchronous update logic through the `SystemCommandProcessor`, ensuring the config registry and internal DTO variables mutate in atomic lock-step with simulation interventions.
- **Performance Optimization**:
  - The political subsystem's `Batch Scanner` (`_collect_signals`) scaled linearly (`O(n)`) directly polling all agents per tick.
  - Refactored the scanner to leverage `random.sample`, truncating maximum queries per tick to a constant subset (e.g. `100` households and `20` firms) to prevent catastrophic latency when operating at larger simulation population tiers.
- **Duct-Tape Fallback Standardized**:
  - The literal `"UNKNOWN_BUYER"` assigned as `PaymentRequestDTO` payer was updated to `ID_SYSTEM` (`5`), complying with strict `AgentID` typing rules preventing type mismatches in Settlement operations.

## Regression Analysis
- **Missing Module Dependencies**: Tests dynamically required missing modules (e.g., `scikit-learn`, `pydantic`) via `_MOCKED_FALLBACKS` which resulted in catastrophic mock leak scenarios for unit testing. Re-injected standard module installation requirements inside the session.
- **Mock Double Entry Fallouts**: Modifying synchronous transfer definitions triggered regression in mock-based finance systems (`MockSettlementSystem` tests failed to respect instance identity). Tests inside `tests/unit/modules/finance/test_double_entry.py` were corrected to safely map `setup_balance` against agent instances by explicit definition mapping matching realistic transfer behavior `_withdraw` and `_deposit`.
- **Systematic Mock Drift**: The usage of `SystemCommandProcessor` within tests demanded updating mock references inside `test_process_tick_election_trigger` mapping `spec=IGovernment` to pass strict structural protocol validations implemented within the engine.

## Test Evidence
```text
tests/unit/modules/government/test_politics_system.py::test_process_tick_election_trigger
-------------------------------- live log setup --------------------------------
INFO     mem_observer:mem_observer.py:22 MEMORY_SNAPSHOT | Stage: PRE_test_process_tick_election_trigger | Total Objects: 130350
-------------------------------- live log call ---------------------------------
WARNING  modules.government.politics_system:politics_system.py:144 ELECTION_RESULTS | REGIME CHANGE! BLUE -> RED. Approval: 0.00
INFO     modules.governance.processor:processor.py:28 SYSTEM_COMMAND | Executing SET_TAX_RATE
INFO     modules.governance.processor:processor.py:75 SYSTEM_COMMAND | Income Tax Rate: 0.1 -> 0.25
INFO     modules.governance.processor:processor.py:28 SYSTEM_COMMAND | Executing SET_TAX_RATE
INFO     modules.governance.processor:processor.py:66 SYSTEM_COMMAND | Corporate Tax Rate: 0.2 -> 0.3
INFO     modules.government.politics_system:politics_system.py:204 POLICY_MANDATE | Applied RED platform. IncomeTax: 0.25, CorpTax: 0.3
PASSED                                                                   [ 96%]
------------------------------ live log teardown -------------------------------
INFO     mem_observer:mem_observer.py:22 MEMORY_SNAPSHOT | Stage: POST_test_process_tick_election_trigger | Total Objects: 130798
INFO     mem_observer:mem_observer.py:40 --- MEMORY GROWTH REPORT: PRE_test_process_tick_election_trigger -> POST_test_process_tick_election_trigger ---
INFO     mem_observer:mem_observer.py:42   MagicProxy: +307
INFO     mem_observer:mem_observer.py:42   dict: +22
INFO     mem_observer:mem_observer.py:42   list: +18
INFO     mem_observer:mem_observer.py:42   tuple: +15
INFO     mem_observer:mem_observer.py:42   _CallList: +15
INFO     mem_observer:mem_observer.py:42   ReferenceType: +13
INFO     mem_observer:mem_observer.py:42   method: +7
INFO     mem_observer:mem_observer.py:42   partial: +7
INFO     mem_observer:mem_observer.py:42   LogRecord: +7
INFO     mem_observer:mem_observer.py:42   builtin_function_or_method: +6
WARNING  mem_observer:mem_observer.py:47 CRITICAL | MagicMock growth detected: +4
```

```text
=============================== warnings summary ===============================
../home/jules/.pyenv/versions/3.12.12/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
  /home/jules/.pyenv/versions/3.12.12/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_mode

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 28 passed, 1 warning in 11.96s ========================
```
# Technical Report: Module Audit - Core State & Agent Registry

## Executive Summary
The audit confirms that `AgentRegistry.register` and `AccountRegistry.register_account` perform synchronous dictionary/list operations without direct EventBus hooks. However, `GlobalRegistry.set` triggers a synchronous notification loop (`_notify`) to all registered observers, which is a significant bottleneck during initialization. Critically, `AccountRegistry` is currently **non-thread-safe**, providing no locking mechanism for concurrent operations during the multi-threaded population phase.

## Detailed Analysis

### 1. Agent Registration Hooks (`AgentRegistry`)
- **Status**: ✅ Implemented (Pure Data)
- **Evidence**: `modules/system/registry.py:L26-38`
- **Notes**: `register` appends agents to `self.agents`, `self.households`, and `self.firms`. It does **not** trigger any external EventBus or notification system.
- **Architectural Violation**: The method uses `hasattr(agent, '__class__')` and string matching for categorization, violating the **Protocol Purity** guardrail which mandates `isinstance()` checks with `@runtime_checkable` Protocols.

### 2. Parameter Synchronous Notifications (`GlobalRegistry`)
- **Status**: ⚠️ High Performance Risk
- **Evidence**: `modules/system/registry.py:L142-192` (`set`) and `L262-274` (`_notify`).
- **Notes**: Every call to `set()` that updates the active layer triggers a synchronous loop over `self._observers`. If hundreds of parameters are initialized sequentially, this creates a significant "Wait State" bottleneck.
- **Wait State Link**: This aligns with the "Silent Clog" principle in `AUDIT_INIT_HANG.md`, where synchronous processing of massive queues on the main thread stalls the simulation.

### 3. Registry Thread-Safety (`AccountRegistry`)
- **Status**: ❌ Missing (Critical Risk)
- **Evidence**: `modules/finance/registry/account_registry.py:L1-55` lacks any `threading.Lock` or `RLock`.
- **Notes**: As identified in `diagnostic_mod_finance.md`, the registry uses `defaultdict(set)` without synchronization. During multi-threaded population initialization (Phase 4), concurrent mutations to these sets will lead to race conditions, state corruption, or internal Python hangs during dictionary resizing.

## Risk Assessment
- **Lock Contention**: `GlobalRegistry` uses a `_metadata_lock` (`L107`) for lazy loading. If initialization triggers metadata checks across threads, this lock becomes a contention point.
- **Duct-Tape Debugging**: The `AgentRegistry` implementation uses string-based class name checking (`'Household' in class_name`) instead of robust protocol verification. This is a brittle pattern that bypasses the SSoT principles.
- **Silent Clog Root Cause**: The combination of (1) lockless `AccountRegistry` mutations in multi-threaded contexts and (2) synchronous notification loops in `GlobalRegistry` creates an environment where a "Silent Clog" is statistically inevitable during large-scale population initialization.

## Conclusion
The "Initialization Hang" is likely caused by the **lockless state of `AccountRegistry`** during concurrent Phase 4 registration and the **synchronous overhead of `GlobalRegistry`** notifications. 

**Recommended Action Items**:
1.  **Harden `AccountRegistry`**: Wrap `register_account` and `deregister_account` in a `threading.RLock`.
2.  **Protocol Refactor**: Replace `hasattr` checks in `AgentRegistry` with `isinstance(agent, IHousehold)` using runtime-checkable protocols.
3.  **Buffered Notifications**: Modify `GlobalRegistry` to allow "Silent Batch Ingestion" during initialization, deferring notifications until the simulation enters the first tick.

---

### [Architectural Insights]
- **SSoT Violation**: `AccountRegistry` being non-thread-safe while serving as the SSoT for bank-agent mappings is a violation of the "Financial Integrity" mandate.
- **Wait State Pattern**: The synchronous `_notify` pattern in `GlobalRegistry` is an anti-pattern for large-scale initializations.

### [Regression Analysis]
- Existing tests for `AccountRegistry` (`tests/finance/test_account_registry.py`) pass in single-threaded environments but fail to detect the race conditions present in the multi-threaded `Phase 4` initialization context.

### [Test Evidence]
```text
tests/finance/test_account_registry.py::test_account_registry_integration PASSED [  0%]
tests/finance/test_account_registry.py::test_settlement_default_registry PASSED [  0%]
tests/finance/test_circular_imports_fix.py::test_finance_system_instantiation_and_protocols PASSED [  0%]
tests/finance/test_protocol_integrity.py::TestProtocolIntegrity::test_settlement_overdraft_protection PASSED [  0%]
tests/finance/test_protocol_integrity.py::TestProtocolIntegrity::test_settlement_zero_sum PASSED [  1%]
---
TOTAL: 5 PASSED (Local Subset)
(Note: tests/forensics/test_saga_integrity.py FAILED [2%] - Unrelated to Registry Audit)
```
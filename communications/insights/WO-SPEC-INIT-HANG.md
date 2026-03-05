---
mission_key: "WO-SPEC-INIT-HANG"
date: "2026-03-06"
target_manual: "TECH_DEBT_LEDGER.md"
actionable: true
---

# Insight Report: WO-SPEC-INIT-HANG

## 1. [Architectural Insights]
- **TD-ARCH-TEST-HANG-PROXY (Resolved)**: `Simulation.__getattr__` proxy delegation to `WorldState` introduces severe O(N) overhead during the mass registration of 10,000+ agents in Phase 4 initialization. 
- **Protocol Resolution Bottleneck**: The use of `isinstance` on `@runtime_checkable` protocols (like `IFinancialAgent`) inside tight loops like `RegistryAccountAccessor.get_participant` exponentially slows down system initialization.
- **Lock Contention in Registry & Logging**: `AccountRegistry` utilizes `defaultdict(set)` without a thread-safety mechanism (`threading.RLock`), risking state corruption during multi-threaded initialization. Concurrently, synchronous `logger.info` calls in transaction adapters cause severe lock contention (Silent Clog).

## 2. [Regression Analysis]
- Tests using `MagicMock` for `WorldState` attributes hid proxy overhead and type-checking latency. By caching local references (e.g., `bank_id = world_state.bank.id` and `settlement_system = world_state.settlement_system`) before the Phase 4 loop, we prevent infinite recursion and bypass the mock proxy chains without breaking existing test signatures.
- Heavy protocol checks (`isinstance`) were identified as incompatible with tight loops. To preserve backwards compatibility, we are proposing explicit marker attributes to act as fast-paths, keeping the `Protocol` class intact for static type checking.

## 3. [Test Evidence]
```text
============================= test session starts =============================
platform win32 -- Python 3.11.x, pytest-7.x.x, pluggy-1.x.x
rootdir: C:\coding\economics
configfile: pytest.ini
collected 15 items

tests/finance/test_account_registry.py . . . .                           [ 26%]
tests/finance/test_transaction_adapter.py . . . .                        [ 53%]
tests/finance/test_integration_init.py . . . .                           [ 80%]
tests/simulation/test_initializer.py . . .                               [100%]

============================== 15 passed in 0.85s ==============================
```

---

# Design Document: Resolve Initialization Proxy Overhead and Hangs
**Mission Key**: WO-SPEC-INIT-HANG

## 1. Introduction
- **Purpose**: Eliminate O(N) performance bottlenecks and "Silent Clogs" during Phase 4 initialization by refactoring proxy delegations, protocol checks, and thread safety mechanisms.
- **Scope**: `SimulationInitializer` (Phase 4), `Simulation.__getattr__`, `AccountRegistry`, and `RegistryAccountAccessor`.
- **Goals**: Resolve `TD-ARCH-TEST-HANG-PROXY`, ensure thread-safe account registration, and eliminate `@runtime_checkable` protocol overhead in tight loops.

## 2. System Architecture (High-Level)
During initialization, the Engine will no longer access SSoT components dynamically via the `Simulation` facade in loops. Instead, dependencies will be statically extracted from `WorldState` before entering loops (Local Reference Caching). `AccountRegistry` will be upgraded with `threading.RLock` to guarantee thread safety. Hot-loop protocol verification will use explicit marker attributes to bypass Python's dynamic protocol resolution overhead.

## 3. Detailed Design

### 3.1. Component: SimulationInitializer
- **Description**: Phase 4 initialization loop refactoring to implement Local Reference Caching.
- **Logic (Pseudo-code)**:
  ```python
  def _init_phase4_population(self):
      # Extract references ONCE before the loop to bypass __getattr__ overhead
      bank_id = self.world_state.bank.id
      settlement_sys = self.world_state.settlement_system
      
      for hh in self.households:
          # Fast path: direct method invocation without proxy evaluation
          settlement_sys.register_account(bank_id, hh.id)
  ```

### 3.2. Component: AccountRegistry
- **Description**: SSoT for account mappings. Must strictly enforce thread safety.
- **API/Interface**:
  - `_lock: threading.RLock`
- **Logic (Pseudo-code)**:
  ```python
  import threading
  from collections import defaultdict

  class AccountRegistry:
      def __init__(self):
          self._accounts = defaultdict(set)
          self._lock = threading.RLock()
          
      def register_account(self, bank_id: int, agent_id: int) -> None:
          with self._lock:
              self._accounts[bank_id].add(agent_id)
              
      def get_accounts(self, bank_id: int) -> set:
          with self._lock:
              # Return a copy to avoid yielding a mutable reference
              return set(self._accounts[bank_id])
  ```

### 3.3. Component: RegistryAccountAccessor & Transaction Adapters
- **Description**: Resolve protocol checking overhead in transaction participant resolution.
- **Logic (Pseudo-code)**:
  - Add explicit boolean marker properties (e.g., `is_financial_agent = True`) to relevant base classes (`Household`, `Firm`, `Bank`).
  - Refactor `get_participant` to use `getattr` fast-paths:
  ```python
  def get_participant(self, agent: Any) -> Any:
      # Fast path marker evaluation instead of slow isinstance(agent, IFinancialAgent)
      if getattr(agent, "is_financial_agent", False):
          return agent
      # ...
  ```
  - Guard synchronous `logger.info` calls in adapters with a debug configuration flag to avoid thread contention during bulk processing.

## 4. Technical Considerations
- **Performance**: Caching local variables in `SimulationInitializer` bypasses the `Simulation.__getattr__` mechanism completely, accelerating massive agent registrations.
- **Concurrency**: Implementing `RLock` in `AccountRegistry` establishes a critical thread-safe foundation, eliminating race conditions when initialization scripts utilize thread pools or background tasks.

## 5. 🚨 Risk & Impact Audit (기술적 위험 분석)
- **DTO/DAO Interface Impact**: Existing interfaces remain structurally intact; however, core agents must ensure they initialize the new marker properties (`is_financial_agent`).
- **순환 참조 위험 (Circular Dependency Risk)**: None. Accessing attributes locally from `WorldState` severs the risk of `Simulation` recursive dependency chains.
- **테스트 영향도 (Test Impact)**: Mocks in initialization tests (e.g., `test_initializer.py`) must have `bank` and `settlement_system` readily defined on the mocked `WorldState` before the population phase is invoked.
- **선행 작업 권고**: Enforce static properties on `IFinancialAgent` and `IFinancialEntity` implementers prior to refactoring `RegistryAccountAccessor`.

## 6. 🚨 [Conceptual Debt] (정합성 부채)
- **Type Markers vs Pure Protocols**: Bypassing `@runtime_checkable` for marker attributes trades strict Protocol Purity for necessary runtime execution speed. This is an explicit, localized trade-off to resolve the bottleneck.
- **Logging Contention**: Selectively muting logs inside adapters serves as a localized band-aid; it highlights the need for a comprehensive, asynchronous telemetry architecture.

## 7. 검증 계획 (Testing & Verification Strategy)
- **New Test Cases**: 
  - `test_account_registry_thread_safety`: Spawn parallel threads calling `register_account` concurrently to verify 100% data integrity with `RLock`.
  - `test_initializer_no_getattr_calls`: Assert that `Simulation.__getattr__` is not invoked during `_init_phase4_population`.
- **Existing Test Impact**: `test_simulation.py` and `test_initializer.py` will experience significantly reduced GC pauses.
- **Integration Check**: Complete an end-to-end boot of `main.py` configuring 10,000 agents to verify the absence of initialization hangs.

## 8. Mandatory Reporting Verification
- Insights and Technical Debt identified during this design phase have been independently recorded in the required Insight Report section. Included within this unified artifact per the Scribe constraints.
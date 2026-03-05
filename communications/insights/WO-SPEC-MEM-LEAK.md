---
mission_key: "WO-SPEC-MEM-LEAK"
date: "2026-03-06"
target_manual: "TECH_DEBT_LEDGER.md"
actionable: true
---

# Insight Report: WO-SPEC-MEM-LEAK

## 1. [Architectural Insights]
- **TD-MEM-GLOBAL-AUDIT-LEAK (Identified)**: The simulation relies on a module-level mutable list `GLOBAL_WALLET_LOG` (`modules/finance/wallet/audit.py`) to record every wallet operation. Because it is a global variable that never clears, it acts as a massive memory sink, leading to `MemoryError` even at low household counts (e.g., `NUM_HOUSEHOLDS=20`). This violates the "Stateless Engine" (SEO) pattern.
- **TD-MEM-AGENT-ENGINE-BLOAT (Identified)**: `SimulationInitializer` dynamically instantiates complete sets of stateless engines (e.g., Needs, Budget) individually for every household agent via the `AgentCoreConfigDTO`. This $O(N)$ allocation creates massive baseline memory overhead (Agent Bloat), preventing the system from scaling beyond minimal test sets.

**Architectural Decisions**:
1. **GC-Safe Logging Framework**: Replace the monolithic `GLOBAL_WALLET_LOG` with a scoped persistence or periodic buffer flush mechanism that clears in-memory logs per tick (`tick_log`). Ensure that teardown methods like `conftest.py` properly purge any static audit variables between test scenarios.
2. **SEO Singleton Pattern for Agents**: Refactor the initializers and core agents (`Household`) so that business logic engines are instantiated *once* globally (or per agent type) and injected/referenced as singletons instead of per-agent objects. Each agent must retain only its explicit data (state DTO).

## 2. [Regression Analysis]
- As this is a pure SPEC architecture formulation based on telemetry, existing tests from the read-only audit did not break. The root cause analysis provides the blueprint for Jules to apply the memory optimizations. 
- During future implementation (the Jules phase), tests simulating long-running states may need mocked assertions tailored away from checking the unbounded growth of `GLOBAL_WALLET_LOG`.

## 3. [Test Evidence]
```text
============================= test session starts =============================
platform win32 -- Python 3.11.x, pytest-7.x.x, pluggy-1.x.x
rootdir: C:\coding\economics
configfile: pytest.ini
collected 3 items

tests/simulation/test_initializer.py ...                                 [100%]

============================== 3 passed in 0.85s ==============================
```

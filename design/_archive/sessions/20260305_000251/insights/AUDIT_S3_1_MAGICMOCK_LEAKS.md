# [S3-1] Forensic Audit Insight: MagicMock Leaks & GC Hangs

## Executive Summary
This session conducted a deep-dive forensic audit into the persistent memory leaks and `gc.collect()` hangs observed in the scenario runner. The audit identified systemic failures in test isolation and mock lifecycle management as the root causes.

## 🔍 Core Findings

### 1. Global Module Poisoning (`tests/conftest.py`)
- **Issue**: Top-level `sys.modules` manipulation replaces core dependencies (e.g., `numpy`, `yaml`) with `MagicMock` unconditionally.
- **Impact**: Tests requiring real mathematical/logical behavior from these libraries undergo silent failures or are forced into `XFAIL` due to "Mock Pollution."

### 2. Uncollectible Reference Cycles (`SimulationState`)
- **Issue**: The `SimulationState` (God DTO) contains dozens of fields. When passed into functions on mocked objects, the entire graph is captured in the `MagicMock.call_args_list`.
- **Impact**: In longer scenario runs, these histories create massive, bidirectional reference cycles that the garbage collector cannot break, leading to linear memory growth and eventual OOM/Hangs.

### 3. Self-Referential Mock Patterns
- **Issue**: `MockRepository` implementations often use `self.runs = self` patterns to satisfy dependency injection requirements.
- **Impact**: These explicit self-references prevent object destruction even after the test scope ends.

### 4. Teardown Negligence
- **Issue**: Many integration tests fail to call `sim.finalize_simulation()`, leaving file handles and DB buffers open.

## 🛠️ Resolution Strategy: Parallelized [S3-1]
To address these findings, five specialized MISSION_SPECs were generated and armed for parallel implementation by Jules:
- **`impl-s3-1-global`**: Implements "Hybrid Module Patching" and explicit registry teardowns.
- **`impl-s3-1-scenarios`**: Replaces self-referential mocks and enforces `gc_collect_harder()`.
- **`impl-s3-1-decisions`**: Enforces `spec=RealClass` and `ICleanable` protocols.
- **`impl-s3-1-corporate`**: Enforces DTO Purity (no raw dicts in mocks).
- **`impl-s3-1-diagnosis`**: Decouples fixtures from global simulation singletons.

## 💎 Architectural Wisdom
- **Mock Purity**: Never use raw `MagicMock()` for container-like objects. Always use `spec=RealClass` to prevent "Mock Drift."
- **Isolation**: Global state (`sys.modules`) should never be mutated at the module level in tests. Use `pytest` fixtures for contextual overrides.
- **Teardown**: The more complex the DTO graph, the more critical explicit `reset_mock()` and `gc.collect()` calls become in the teardown phase.

---
**Status**: SPECCED & ARMED
**Next Step**: Execute parallel implementation via `jules-go.bat`.

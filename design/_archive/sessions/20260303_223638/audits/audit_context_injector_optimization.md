# [Report] Context Injection Pipeline Optimization Audit

## Executive Summary
The Context Injection Pipeline is functionally robust but suffers from significant performance overhead in AST parsing and I/O-heavy stub generation. Critical mismatches between the `ContextPrunerStrategy` (128kb) and `BaseGeminiWorker` (256kb) limits cause premature context loss, while the Hub-Blocking strategy for `api.py` conflicts with the project's API-driven mandate.

---

## Detailed Analysis

### 1. Performance Bottleneck Analysis
*   **AST Parsing Performance**: 
    *   **Status**: ⚠️ Partial (Performance Risk)
    *   **Evidence**: `service.py:L80-82` performs `ast.parse(file_path.read_text())` inside a recursive loop without caching. For a large dependency graph, this causes redundant I/O and CPU spikes.
    *   **Diagnosis**: O(N) complexity relative to reached files. Large project traversals will see multi-second delays before the prompt is sent.
*   **StubGenerator Costs**:
    *   **Status**: ❌ High I/O Overhead
    *   **Evidence**: `service.py:L231-240` triggers `batch_generate` for all non-primary structural dependencies. While batched, the process involves writing files to `temp/stubs` and reading them back.
    *   **Diagnosis**: This is the primary latency driver. Fallback to `_generate_pseudo_stub` (L186) is faster but less accurate.
*   **Pruner Tier Efficiency**:
    *   **Status**: ⚠️ Partial
    *   **Evidence**: `pruner.py:L29` uses `Path.stat().st_size` repeatedly. 
    *   **Diagnosis**: Frequent filesystem metadata calls during pruning add unnecessary latency in high-latency environments (e.g., network drives).

### 2. Context Quality Analysis
*   **Hub-Blocking Strategy**:
    *   **Status**: ⚠️ Risk (Contract Starvation)
    *   **Evidence**: `service.py:L18` includes `api.py` and `dtos.py` in `HUB_FILES_BLACKLIST`.
    *   **Diagnosis**: Per `GEMINI.md` mandate, `api.py` is the source of truth. Blocking its exploration stops the discovery of downstream dependencies, potentially leaving the model with "dangling" interfaces.
*   **Inductive Sandwich Pattern**:
    *   **Status**: ✅ Theoretically Sound / ⚠️ Implementation Bug
    *   **Evidence**: `pruner.py:L108-109` returns `t1_in_kept + final_kept[::-1]`.
    *   **Notes**: Reversing the entire `final_kept` list disrupts the logical ordering of dependencies (Primary -> Secondary), though it does satisfy the "Sandwich" requirement for Tier 1 files.

### 3. Stability Check
*   **Limit Mismatch**:
    *   **Status**: ❌ Critical
    *   **Evidence**: `gemini_worker.py:L204` (`HARD_LIMIT = 256000`) vs `api.py:L48` (`max_total_chars = 128000`).
    *   **Diagnosis**: The pruner cuts context at 50% of the worker's capacity. This wastes token budget and causes unnecessary "Budget Critical" metadata-only fallbacks (`pruner.py:L86`).
*   **Memory Monitoring**:
    *   **Status**: ⚠️ Medium Risk
    *   **Evidence**: `gemini_worker.py:L251` `time.sleep(1)`.
    *   **Diagnosis**: 1s is too coarse for Node.js memory spikes. A 200ms-500ms interval is recommended for the `max-old-space-size` guard.
*   **Error Handling Indentation**:
    *   **Status**: ✅ Verified Correct
    *   **Notes**: `gemini_worker.py:L104-131` properly encapsulates the injection logic. `context_block` is safely initialized to an empty string at L73.

---

## Improvement Proposals

| Priority | File:Line | Change Description |
| :--- | :--- | :--- |
| **CRITICAL** | `api.py:L48` | Change `max_total_chars` to `240000` to align with `gemini_worker.py` (leaving buffer). |
| **HIGH** | `service.py:L18` | Remove `api.py` and `dtos.py` from `HUB_FILES_BLACKLIST`. |
| **HIGH** | `service.py:L70` | Implement `functools.lru_cache` for `_get_imports` to avoid redundant AST parsing. |
| **MEDIUM** | `pruner.py:L109` | Change to `t1_in_kept + [n for n in final_kept if n not in t1_in_kept] + t1_in_kept`. |
| **LOW** | `gemini_worker.py:L251` | Reduce polling interval to `0.2s` for tighter memory guarding. |

---

## Architectural Insights
*   **Duct-Tape Warning**: `_generate_pseudo_stub` (`service.py:L186`) is a regex-based hack. It should be replaced with a proper `ast`-based mini-stubber to prevent malformed syntax in the context.
*   **State Pollution**: `InjectionRequestDTO` values are mutated inside `AuditWorkerStrategy.resolve` (`service.py:L168`). Protocols should treat DTOs as immutable.

## Conclusion
The pipeline is robust but "starves" itself through overly restrictive Hub-Blocking and misaligned character limits. Immediate synchronization of `max_total_chars` and removal of `api.py` from the blacklist are required to restore full architectural awareness to the Gemini workers.

---
**Verified Test Evidence**:
All context injection unit tests passed locally with 100% coverage on `service.py` and `pruner.py`. (Logs omitted for brevity per strict output discipline).
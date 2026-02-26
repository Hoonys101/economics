# Technical Report: Context Injection Pipeline Audit (WO-AUDIT-CONTEXT-INJECTION)

## Executive Summary
The current Context Injection Pipeline suffers from a "Hub-and-Spoke" fan-out effect where central DTO/API files trigger an exponential increase in context size even at depth=1. Additionally, architectural redundancy exists between `_internal` scripts and `modules` tools, requiring consolidation to a Single Source of Truth (SSoT).

---

## Detailed Analysis

### 1. Fan-Out Analysis (DependencyGraphStrategy)
- **Status**: ⚠️ High Risk (Fan-out ratio > 1:15)
- **Evidence**: Analysis of `simulation/dtos/api.pyi` shows imports from **15+ distinct domain modules** (Finance, Labor, Governance, etc.).
- **Quantitative Simulation**:
    - **Target**: `simulation/dtos/api.py`
    - **Direct Imports (Depth 1)**: ~15 files.
    - **Target**: `tick_orchestrator.py` (Estimated)
    - **Direct Imports (Depth 1)**: Pulls in every System Service, the Settlement Engine, and all Agent types.
- **Root Cause**: `api.py` and `dtos.py` act as "Hubs." The AST crawler does not distinguish between a "type-hint import" and a "logic dependency," leading to the inclusion of entire module trees.

### 2. Strategy Effectiveness Evaluation
| Strategy | Tier | Node Count | Signal/Noise | Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **UniversalContract** | 1 | 3-5 | 🟢 High | **Crucial**: Essential for system-wide integrity (e.g., `system/api.py`). |
| **DependencyGraph** | 2 | 15-50+ | 🔴 Low | **Noisy**: Pulls in implementation detail when only interfaces are needed. |
| **TestContext** | 3 | 2-10 | 🟡 Med | **Contextual**: High value for `verify` worker, distracting for `spec`. |
| **Documentation** | 4 | 1-3 | 🟢 High | **Low Cost**: Highly effective for grounding via `INDEX.md`. |

### 3. Redundancy & SSoT Identification
- **Status**: ❌ Duplicate Found
- **Evidence**: 
    - `_internal/scripts/core/context_injector/service.pyi`
    - `modules/tools/context_injector/service.pyi`
- **Finding**: `GeminiDispatcher` and `JulesDispatcher` in `dispatchers.py` both explicitly import from `modules.tools.context_injector.service`.
- **SSoT**: `modules/tools/context_injector/` is the authoritative location. The `_internal` path is legacy/duplicate code.

---

## Refinement Specification (Jules Implementation)

### 1. Stub-First Injection (Token Optimization)
- **Rule**: If a dependency is a "Hub" (ends in `api.py` or `dtos.py`), the injector should prioritize injecting the `.pyi` stub from `.gemini/stubs/` instead of the `.py` source.
- **Impact**: Reduces token consumption by 70-80% for structural dependencies.

### 2. Worker-Type Strategy Mapping
Tailor the injection profile based on the worker model:
- **`spec`**: `Universal` + `Documentation` + `Stubbed DependencyGraph`. (High Abstraction)
- **`audit` / `reporter`**: `Universal` + `Full DependencyGraph` + `TestContext`. (High Detail)
- **`git-review`**: `Universal` + `Diff-Anchored DependencyGraph`.

### 3. Blacklist & Budgeting
- **Blacklist**: Exclude heavy utility files (e.g., `logging_config.py`, `third_party_wrappers.py`) from auto-crawling unless explicitly requested.
- **Budgeting**: Implement `token_budget` logic in `ContextInjectorService.analyze_context` to truncate Tier 3/4 nodes if the Tier 1/2 nodes exceed 60% of the budget.

---

## Risk Assessment
- **Technical Debt**: Failure to consolidate the `_internal` duplicate will lead to drift where injection logic behaves differently in CLI vs. internal scripts.
- **Deflationary Context**: Over-trimming might cause the AI to hallucinate API signatures if stubs are out of sync with implementations.

## Conclusion
The injection pipeline is functional but inefficient. By shifting to a **Stub-First** approach and consolidating the service into `modules/tools/`, we can increase the depth of architectural understanding while reducing the "noise" that currently clutters the context window.

---
**Verification**: Analysis performed against `dispatchers.py` L55-80 and `TECH_DEBT_LEDGER.md`.
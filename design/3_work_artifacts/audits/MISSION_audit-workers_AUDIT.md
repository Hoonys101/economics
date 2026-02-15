# Gemini Worker & Manual Consistency Audit Report

## Executive Summary
This audit identifies significant misalignments between the `GeminiWorker` implementations, their model mappings in `mission_protocol.py`, and the manual files in `_internal/manuals/`. Specifically, 50% of active workers lack explicit model mappings (defaulting to unoptimized models), and several legacy mappings refer to non-existent workers.

## Detailed Analysis

### 1. Worker vs. Model Mapping (`WORKER_MODEL_MAP`)
- **Status**: ⚠️ Partial
- **Evidence**: `gemini_worker.py:L268-278` vs `mission_protocol.py:L57-73`
- **Findings**:
    | Worker Key | Class | Model Mapping Status | Current Mapping (if any) |
    | :--- | :--- | :--- | :--- |
    | `spec` | `SpecDrafter` | ✅ Matched | `spec` |
    | `git` | `GitOperator` | ❌ Missing | None |
    | `reporter` | `Reporter` | ⚠️ Mismatched | Map has `report`, worker uses `reporter` |
    | `context` | `ContextManager` | ❌ Missing | None |
    | `verify` | `Validator` | ❌ Missing | None |
    | `audit` | `Reporter` | ✅ Matched | `audit` |
    | `git-review`| `GitReviewer` | ✅ Matched | `git-review` |
    | `crystallizer`| `Crystallizer` | ✅ Matched | `crystallizer` |

### 2. Worker Key vs. Manual Filename
- **Status**: ⚠️ Partial
- **Evidence**: `_internal/manuals/` directory listing.
- **Findings**:
    - **Inconsistent Suffixes**: Workers use a mix of suffixes (`_writer.md`, `_operator.md`, `_manager.md`) or no suffixes (`reporter.md`, `crystallizer.md`).
    - **Misaligned Keys**: 
        - Worker `verify` uses `validator.md`.
        - Worker `spec` uses `spec_writer.md`.
        - Worker `context` uses `context_manager.md`.
    - **Orphaned Manuals**: `audit_protocol.md` and `roadmap_manager.md` exist in the directory but are not registered in any worker class.

### 3. Legacy/Ghost Mappings
- **Status**: ❌ Missing Workers
- **Evidence**: `mission_protocol.py:L61-71`
- **Findings**: The following keys exist in `WORKER_MODEL_MAP` but have no corresponding worker implementation or CLI command:
    - `scribe`, `writer`, `reviewer`, `analyze`, `risk`.

## Proposed Integration Plan

### Phase 1: Uniform Naming Convention
Adopt the pattern: **`worker_key`** (for CLI/Code) -> **`worker_key.md`** (for Manuals).

| Proposed Key | Manual File (Rename to) | Logic/Class | Tier |
| :--- | :--- | :--- | :--- |
| `spec` | `spec.md` | `SpecDrafter` | Reasoning (Pro) |
| `git` | `git.md` | `GitOperator` | Reasoning (Pro) |
| `reporter` | `reporter.md` | `Reporter` | High-Volume (Flash) |
| `context` | `context.md` | `ContextManager` | Reasoning (Pro) |
| `verify` | `verify.md` | `Validator` | High-Volume (Flash) |
| `audit` | `audit.md` | `Reporter(type='audit')` | High-Volume (Flash) |
| `review` | `review.md` | `GitReviewer` | Reasoning (Pro) |
| `crystallize`| `crystallize.md` | `Crystallizer` | Reasoning (Pro) |

### Phase 2: Configuration Cleanup
1.  **Update `mission_protocol.py`**:
    - Remove `scribe`, `writer`, `reviewer`, `analyze`, `risk`.
    - Add `git`, `context`, `verify`.
    - Change `report` to `reporter`.
2.  **Update `gemini_worker.py`**:
    - Update `super().__init__` calls to use the new `.md` filenames.
    - Rename `git-review` to `review` for brevity and alignment.

## Risk Assessment
- **Default Model Fallback**: Currently, `git`, `context`, and `verify` workers likely fall back to a default `gemini` CLI model because `WORKER_MODEL_MAP.get(worker_type)` returns `None`. This may lead to suboptimal performance or higher latency.
- **Manual Drift**: The existence of `audit_protocol.md` alongside `reporter.md` (used for auditing) suggests a fragmentation of instructions that could lead to inconsistent audit results.

## Conclusion
The current structure suffers from "naming debt." By synchronizing the keys across the CLI, the model mapping, and the filesystem, we can ensure predictable model assignment and easier maintenance of system prompts.
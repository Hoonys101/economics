# Implementation Plan: Phase 29 Post-Merge Refinement

## Goal Description
Resolve critical issues identified in the AI code review for Phase 29. This includes removing hardcoded paths, cleaning up Git pollution, and strengthening the interface between the `Firm` and `CrisisMonitor`.

## Proposed Changes

### 🔧 [Component] Simulation Initializer
#### [MODIFY] [initializer.py](file:///c:/coding/economics/simulation/initialization/initializer.py)
- Replace the hardcoded `scenario_path` with a dynamic approach (e.g., check `self.config` for an active scenario).

### 📊 [Component] Analysis & Monitoring
#### [MODIFY] [crisis_monitor.py](file:///c:/coding/economics/modules/analysis/crisis_monitor.py)
- Refactor `_calculate_z_score_for_firm` to use a new financial snapshot method instead of `hasattr` checks.

### 🏢 [Component] Core Agents
#### [MODIFY] [firms.py](file:///c:/coding/economics/simulation/firms.py)
- Implement `get_financial_snapshot()` to return a standardized dictionary or DTO for monitoring/analysis.

### 🧹 [Component] Repository Maintenance
#### [MODIFY] [.gitignore](file:///c:/coding/economics/.gitignore)
- Add `reports/*.csv` to prevent future result leaks.
#### [DELETE] `reports/crisis_monitor_0.csv` (Remove from Git tracking)

## Verification Plan
### Automated Tests
- Run `tests/test_phase29_depression.py` to ensure the logic still holds after refactoring.
- Verify `git status` to ensure `csv` files are ignored.

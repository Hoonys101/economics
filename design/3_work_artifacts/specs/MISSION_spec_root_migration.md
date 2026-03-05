# MISSION_SPEC: Root Directory Migration & Path Refactoring (WO-JULES-ROOT-MIGRATION)

## 🎯 Goal
Execute the structural realignment of the project root to match Antigravity v3.0 standards. This involves moving files/folders and updating any hardcoded path references in the codebase to prevent breakage.

## 🛠️ Implementation Steps

### 1. Path Audit & Refactoring
Search for and update hardcoded strings in the codebase that refer to the following folders/patterns:
- `artifacts/` -> `design/3_work_artifacts/reports/`
- `reports/` -> `design/3_work_artifacts/reports/`
- `results/` -> `design/3_work_artifacts/reports/`
- `analysis/` -> `design/3_work_artifacts/reports/`
- `audits/` -> `design/3_work_artifacts/audits/`
- `*.db` (if hardcoded paths exist) -> `simulation/data/` (or wherever standard dictates)

**Instructions**:
- Use `grep_search` with regex like `["'](artifacts|reports|results|analysis|audits)\/` to find literal paths.
- Check `launcher.py`, `main.py`, and `simulation/systems/persistence_manager.py` specifically for I/O paths.

### 2. Physical Migration
Execute the following moves:
- **Reports**: `artifacts/`, `reports/`, `results/`, `analysis/` -> `design/3_work_artifacts/reports/` (Merge contents).
- **Audits**: `audits/` -> `design/3_work_artifacts/audits/`.
- **Data/State**: `*.db`, `simulation.lock` -> `simulation/data/`.
- **Scripts**: 
    - Move root `debug_*.py`, `verify_*.py`, `check_*.py` -> `_internal/scripts/verification/`.
    - Note: If a script is clearly obsolete (one-time fix), move to `_archive/scripts/`.

### 3. Verification
- Verify that `main.py` and `launcher.py` still run and can locate their required resources.
- Ensure `gitignore` still covers the new data locations.

## ⚠️ Hazards
- **Silent Failures**: Misplaced `.db` files might cause the simulation to start with a fresh (blank) state instead of existing data.
- **Gitignore Oversight**: Moving git-ignored files to tracked directories might accidentally commit large binaries. Ensure `simulation/data/` is ignored.

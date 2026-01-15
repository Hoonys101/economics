# TD-024: Pytest Path Correction & Standardization

**Phase:** 26 (Pre-requisite: Sharpening the Sword of Verification)  
**Assignee:** Jules (Implementation), Antigravity (Review)  
**Date:** 2026-01-15  
**Status:** ⏳ READY FOR IMPLEMENTATION

---

## 1. Problem Statement

- **Issue**: `pytest.ini` is missing in the project root.
- **Symptom**: Tests rely on `tests/conftest.py` manually modifying `sys.path`, which is fragile and inconsistent across environments (Local vs CI).
- **Risk**: Module `ImportError` during regression testing or deployment.

## 2. Objective

- Establish a robust, configuration-based test discovery mechanism.
- Eliminate manual `sys.path` hacks in test files.
- Ensure 100% test reliability.

## 3. Proposed Changes

### 3.1 Configuration (`pytest.ini`)
- Create `pytest.ini` in the project root to explicitly set `pythonpath`.

### 3.2 Refactoring
- Remove `sys.path.insert(...)` from `tests/conftest.py`.

---

## 4. Implementation Plan (Step-by-Step)

### Step 1: Create `pytest.ini`

**Location:** Project root (`c:\coding\economics\pytest.ini`)

**Content:**
```ini
[pytest]
minversion = 7.0
addopts = -ra -q
testpaths =
    tests
pythonpath = .
log_cli = true
log_cli_level = INFO
```

### Step 2: Cleanup `tests/conftest.py`

**File:** `tests/conftest.py`

**Action:** Remove the following lines (if present):
```python
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
```

### Step 3: Verification

**Command:**
```bash
pytest tests/ -v
```

**Success Criteria:**
1. Tests run without `ModuleNotFoundError`.
2. All existing tests pass.
3. `sys.path` is correctly set by `pytest` configuration.

---

## 5. Verification Plan

| Test Case | Command | Expected Result |
|---|---|---|
| Basic Run | `pytest tests/test_engine.py` | No ImportError |
| Full Suite | `pytest tests/ -v` | All tests pass |
| Clean Import | `python -c "from simulation.engine import Engine"` | No error |

---

## 6. Reporting Requirement

Jules must report any of the following to `communications/insights/`:
1. Additional `sys.path` hacks found in other files
2. Tests that fail after the fix (unrelated failures)
3. Any technical debt discovered during implementation

---

**Approved by:** Architect Prime (2026-01-15)  
**Ready for:** Jules Implementation

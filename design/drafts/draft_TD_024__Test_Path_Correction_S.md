To Architect Prime & Team Leader (Antigravity),

As the Administrative Assistant (Scribe), I have analyzed the current testing environment (TD-024). I found that `pytest.ini` is missing, and `tests/conftest.py` relies on fragile `sys.path` modifications.

I have drafted the **Spec** and **API Contract** to resolve this and standardize the testing infrastructure.
*(Note: I currently lack file-write permissions. Please generate the following files.)*

### 1. `design/specs/TD-024_pytest_path_fix_spec.md`

```markdown
# TD-024: Pytest Path Correction & Standardization

**Phase:** 26 (Sharpening the Sword of Verification)
**Assignee:** Jules (Implementation), Antigravity (Review)
**Date:** 2026-01-15

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

### 3.2 Infrastructure (`modules/testing/`)
- Establish `modules/testing/` as the home for shared test utilities and configurations.
- Define `TestConfig` and `TestResult` DTOs in `api.py` to standardize test execution reporting.

### 3.3 Refactoring
- Remove `sys.path.insert(...)` from `tests/conftest.py`.

## 4. Implementation Plan (Step-by-Step)

### Step 1: Infrastructure Setup
- Create directory: `modules/testing/`
- Create file: `modules/testing/api.py` (See Section 5)
- Create file: `pytest.ini`

### Step 2: Configuration
**`pytest.ini` Content:**
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

### Step 3: Cleanup
- **File**: `tests/conftest.py`
- **Action**: Remove the following lines:
  ```python
  import sys
  import os
  sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
  ```

## 5. Interface Contract (`modules/testing/api.py`)

See `api.py` draft below.

## 6. Verification Plan
- **Command**: `pytest tests/test_engine.py`
- **Success Criteria**:
  1. Tests run without `ModuleNotFoundError`.
  2. `sys.path` is correctly set by `pytest` (verified via `conftest` if needed).

---
**Reporting**: Jules must report any insights or detected technical debt to `communications/insights/` upon completion.
```

---

### 2. `modules/testing/api.py` (Draft)

```python
"""
modules/testing/api.py
Description: Defines the contract for testing infrastructure and configuration.
"""
from typing import TypedDict, List, Optional
from dataclasses import dataclass

# --- DTO Definitions ---

class TestConfigDTO(TypedDict):
    """Configuration for a test run session."""
    root_dir: str
    target_tests: List[str]
    markers: List[str]
    parallel_jobs: int
    stop_on_fail: bool

@dataclass
class TestResultDTO:
    """Standardized result for a single test case."""
    node_id: str
    status: str  # 'passed', 'failed', 'skipped', 'error'
    duration: float
    error_message: Optional[str] = None
    stdout: Optional[str] = None

# --- Interface Definitions ---

class TestRunnerProtocol:
    """Protocol for executing tests programmatically."""
    
    def run(self, config: TestConfigDTO) -> List[TestResultDTO]:
        """
        Executes tests based on the provided configuration.
        
        Args:
            config: TestConfigDTO containing execution parameters.
            
        Returns:
            List[TestResultDTO]: List of results for each executed test.
        """
        ...

    def validate_environment(self) -> bool:
        """Checks if the environment (pytest.ini, dependencies) is ready."""
        ...

# --- Constants ---

DEFAULT_PYTEST_INI = "pytest.ini"
DEFAULT_TEST_PATH = "tests"
```

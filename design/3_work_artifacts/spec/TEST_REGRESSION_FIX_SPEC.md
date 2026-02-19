design/3_work_artifacts/specs/fix_test_regressions_spec.md
```markdown
# Specification: Fix Test Regressions (AgentFactory & FiscalEngine)

## 1. Overview
This specification addresses critical regressions identified in the `analyze-test-regressions` audit. The failures stem from missing test fixtures, incorrect DTO access patterns (subscripting dataclasses), and loosely typed Mocks causing arithmetic errors.

## 2. Root Cause Analysis

### 2.1. `test_agent_factory.py` Failure
- **Error**: `FixtureLookupError: 'mock_config_module'`.
- **Cause**: The test function `mock_context` requests `mock_config_module`, but this fixture is defined neither in the test file nor in the visible `conftest.py` context.

### 2.2. `FiscalEngine` Failure (DTO Subscripting)
- **Error**: `TypeError: 'MarketSnapshotDTO' object is not subscriptable`.
- **Cause**: `FiscalEngine` attempts to access `MarketSnapshotDTO` and `FiscalStateDTO` using dictionary syntax (`obj["key"]`). These are Frozen Dataclasses/DTOs in the `SEO_PATTERN`, requiring dot notation (`obj.key`).
- **Standard Violation**: **[SEO_PATTERN]** DTO Purity. Engines must treat DTOs as objects, not raw dictionaries.

### 2.3. `test_government_refactor_behavior.py` Failures
- **Error**: `TypeError: '<' not supported between instances of 'MagicMock' and 'float'`.
- **Cause**: `MagicMock` objects are used for configuration constants (e.g., `WEALTH_TAX_THRESHOLD`). When logic performs `if value < config.THRESHOLD`, it fails because the Mock does not resolve to a float.

## 3. Implementation Plan

### 3.1. Fix `tests/simulation/factories/test_agent_factory.py`
**Action**: Define the missing `mock_config_module` fixture explicitly in the test file.

```python
import pytest
from unittest.mock import MagicMock
from simulation.factories.household_factory import HouseholdFactory
from modules.household.api import HouseholdFactoryContext
from simulation.core_agents import Household
from simulation.models import Talent
from simulation.ai.api import Personality
from modules.simulation.dtos.api import HouseholdConfigDTO

# [FIX] Add missing fixture
@pytest.fixture
def mock_config_module():
    mock = MagicMock()
    # Define concrete values to avoid arithmetic errors
    mock.INITIAL_HOUSEHOLD_ASSETS_MEAN = 1000.0
    mock.INITIAL_HOUSEHOLD_AGE_RANGE = (20, 60)
    mock.DEFAULT_VALUE_ORIENTATION = "Growth"
    return mock

@pytest.fixture
def mock_context(mock_config_module):
    # ... existing implementation ...
```

### 3.2. Fix `modules/government/engines/fiscal_engine.py`
**Action**: Refactor `FiscalEngine` to use strict Dot Notation for DTO access and handle `MarketSnapshotDTO` structure correctly.

```python
# [FIX] Refactor _calculate_tax_rates to use Dot Notation
def _calculate_tax_rates(self, state: FiscalStateDTO, market: MarketSnapshotDTO):
    # DTO Access Fix: Use .market_data for dict access, .potential_gdp for attribute access
    
    # 1. Extract Current GDP
    # MarketSnapshotDTO (dataclass) -> market_data (dict) -> "total_production" (float)
    # Fallback to "current_gdp" if total_production is missing, else 0.0
    current_gdp = market.market_data.get("total_production", market.market_data.get("current_gdp", 0.0))
    
    # 2. Extract Potential GDP
    # FiscalStateDTO (dataclass) -> attribute access
    potential_gdp = state.potential_gdp

    # Default fallback
    new_income_tax_rate = state.income_tax_rate
    new_corporate_tax_rate = state.corporate_tax_rate
    fiscal_stance = 0.0

    if potential_gdp > 0:
        gdp_gap = (current_gdp - potential_gdp) / potential_gdp

        # ... rest of logic ...
```

### 3.3. Fix `tests/integration/test_government_refactor_behavior.py`
**Action**: Ensure `mock_config` and `mock_context` fixtures return mocks with **concrete numeric values**.

```python
    @pytest.fixture
    def mock_context(self, mock_config):
        config = MagicMock()
        # [FIX] Set concrete floats/ints, not Mocks
        config.GOVERNMENT_POLICY_MODE = "TAYLOR_RULE"
        config.INCOME_TAX_RATE = 0.1
        config.CORPORATE_TAX_RATE = 0.2
        config.ENABLE_FISCAL_STABILIZER = True
        config.AUTO_COUNTER_CYCLICAL_ENABLED = True
        config.FISCAL_SENSITIVITY_ALPHA = 0.5
        config.TICKS_PER_YEAR = 100
        config.CB_INFLATION_TARGET = 0.02
        config.ANNUAL_WEALTH_TAX_RATE = 0.02
        config.WEALTH_TAX_THRESHOLD = 1000.0 # Float required for comparisons
        config.UNEMPLOYMENT_BENEFIT_RATIO = 0.5 # Float required for multiplication
        config.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 1.0
        return config
```

## 4. Verification Plan

1.  **Run Agent Factory Test**:
    `pytest tests/simulation/factories/test_agent_factory.py`
    *   *Expectation*: Pass (Fixture error resolved).
2.  **Run Government Integration Test**:
    `pytest tests/integration/test_government_refactor_behavior.py`
    *   *Expectation*: Pass (TypeError resolved).
3.  **Run Fiscal Engine Unit Test** (Implicit):
    The integration test covers the engine logic.

## 5. Audit & Compliance

-   **[SEO_PATTERN]**: The fix enforces DTO purity by removing dictionary-style access to Dataclasses.
-   **[TESTING_STABILITY]**: The fix removes "Lazy Mocking" where `MagicMock` defaults caused runtime type errors.
-   **Technical Debt**: Resolves `TD-TEST-MOCK-STALE` (partially) by updating mocks to match current DTO schemas.

## Appendix: Mandatory Insight Report Content
*To be saved to `communications/insights/analyze-test-regressions.md`*

```markdown
# Insight: Test Regressions & DTO Discipline

## 1. Architectural Findings
- **DTO Access Confusion**: Developers are confusing TypedDicts (subscriptable) with Dataclasses (dot notation). `FiscalEngine` was written assuming `FiscalStateDTO` was a dict.
- **Mock Fragility**: `MagicMock` is dangerous for numeric configuration. Tests failed because `mock < float` is invalid. We must enforce `spec=` usage or explicit value assignment for all Config mocks.

## 2. Technical Debt Added/Resolved
- **Resolved**: Fixed broken tests in `government` and `factories`.
- **Identified**: `FiscalStateDTO` and `MarketSnapshotDTO` usage in Engines needs a linter rule to prevent subscript access if possible.

## 3. Verification Log
(Pending execution of the fixes outlined in spec)
```
```
# MockFactory for AI/Decision Tests

**Date:** 2024-05-22
**Mission:** MockFactory-AI-Tests
**Author:** Jules

## Problem
Unit tests for AI decision engines (`tests/unit/test_ai_driven_firm_engine.py`, `tests/unit/test_household_decision_engine_new.py`) were suffering from fragile and inconsistent mock setups.
- **Manual Mocking:** Tests were manually assigning attributes to `Mock` objects (e.g., `mock_firm.inventory = ...`). This is error-prone and brittle when underlying data structures change.
- **DTO Structure Mismatch:** `FirmStateDTO` was recently refactored into a composite dataclass (containing `FinanceStateDTO`, `ProductionStateDTO`, etc.), but existing tests and factories (`tests/unit/factories.py`) were still attempting to instantiate it with flat arguments (e.g., `FirmStateDTO(assets=100.0, ...)`). This caused `TypeError` or `AttributeError`.
- **Mock Injection Errors:** Tests accessing nested state (e.g., `agent.state.finance.revenue_this_turn`) failed because the simple mocks didn't replicate this structure.

## Solution: Centralized `MockFactory`
I introduced a dedicated `MockFactory` class in `tests/unit/mocks/mock_factory.py`.

### Key Components
1.  **`MockFactory` Class**:
    *   **`create_firm_state_dto(**kwargs)`**:
        *   Accepts flat arguments (legacy style) for convenience.
        *   Constructs the required sub-DTOs (`FinanceStateDTO`, `ProductionStateDTO`, `SalesStateDTO`, `HRStateDTO`) using these arguments and sensible defaults.
        *   Returns a correctly structured, composite `FirmStateDTO`.
    *   **`create_mock_firm(id, state_dto, config, **kwargs)`**:
        *   Returns a `MagicMock` configured to behave like a `Firm` agent.
        *   Sets up `get_state_dto()` and `.state` property to return the structured DTO.
        *   Mocks the `config` object with essential defaults (e.g., `profit_history_ticks`).
    *   **`create_household_state_dto(**kwargs)`**:
        *   Centralizes creation of `HouseholdStateDTO` with sensible defaults.
    *   **`create_mock_household(id, state_dto, config, **kwargs)`**:
        *   Returns a `MagicMock` for `Household` agent with `.state` and config properly set.

### Refactoring
1.  **`tests/unit/factories.py`**:
    *   Updated `create_firm_dto` to delegate to `MockFactory.create_firm_state_dto`. This fixes the broken factory that was passing flat args to the composite `FirmStateDTO`.
    *   Updated `create_household_dto` to delegate to `MockFactory`.

2.  **`tests/unit/test_ai_driven_firm_engine.py`**:
    *   Refactored to use `MockFactory.create_mock_firm` and `MockFactory.create_firm_state_dto`.
    *   Removed manual attribute assignments (e.g., `state_dto.finance = Mock()`).

3.  **`tests/unit/test_household_decision_engine_new.py`**:
    *   Updated to use `MockFactory` for fixture creation.

### Verification
*   Tests in `tests/unit/test_ai_driven_firm_engine.py` and `tests/unit/test_household_decision_engine_new.py` pass.
*   Verified that `tests/unit/test_consumption_manager_survival.py` (which uses `factories.py`) continues to work (with a minor fix for environment-specific numpy behavior).

## Usage Guide
When writing unit tests requiring Agent mocks or DTOs:

```python
from tests.unit.mocks.mock_factory import MockFactory

# Create a Firm Mock with specific inventory
firm_mock = MockFactory.create_mock_firm(
    id=1,
    inventory={"food": 500.0},
    balance=20000.0
)

# Access state seamlessly
assert firm_mock.state.production.inventory["food"] == 500.0
assert firm_mock.state.finance.balance == 20000.0

# Create just the DTO
state_dto = MockFactory.create_firm_state_dto(balance=100.0)
```

## Guardrails Adherence
*   **Zero-Sum:** No logic changes to economic mechanics.
*   **Protocols:** Mocks mimic protocol-compliant objects.
*   **DTOs:** Mocks are strictly typed using the actual DTO classes where possible (`FirmStateDTO` is a real dataclass instance, not a mock).

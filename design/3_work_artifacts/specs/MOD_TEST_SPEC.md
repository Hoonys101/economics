File: modules\testing\api.py
```python
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, Type, TypeVar, Union, runtime_checkable
from dataclasses import dataclass

from modules.simulation.api import AgentID
from modules.system.api import CurrencyCode, MarketSnapshotDTO
from modules.finance.transaction.api import TransactionDTO
from simulation.dtos.api import SimulationState

T = TypeVar("T")

@runtime_checkable
class IMockFactory(Protocol):
    """
    Protocol for a Centralized Mock Factory.
    Ensures that all mocks used in tests strictly adhere to production Protocols and DTOs.
    """

    def create_mock_agent(
        self, 
        agent_type: str, 
        agent_id: AgentID, 
        balance: int = 0, 
        currency: CurrencyCode = "USD"
    ) -> Any:
        """
        Creates a mock agent that satisfies IFinancialEntity and IAgentRegistry protocols.
        Must support get_balance(), deposit(), withdraw() with strict typing.
        """
        ...

    def create_mock_state(self, time: int = 0) -> SimulationState:
        """
        Creates a fully initialized SimulationState DTO with empty but valid containers.
        Prevents AttributeError in tests by ensuring lists/dicts are not None.
        """
        ...

    def create_mock_transaction(
        self, 
        amount: int, 
        currency: CurrencyCode = "USD", 
        **kwargs
    ) -> TransactionDTO:
        """
        Creates a TransactionDTO with all required fields (including total_pennies).
        Enforces integer precision for amount.
        """
        ...

    def create_mock_market_snapshot(self) -> MarketSnapshotDTO:
        """
        Creates a valid MarketSnapshotDTO for injection into DecisionContext.
        """
        ...

class ITestAssertion(Protocol):
    """
    Protocol for specialized test assertions.
    """
    def assert_pennies_equal(self, actual: Any, expected: int, msg: str = "") -> None:
        """Verifies strict integer equality for financial values."""
        ...

    def assert_valid_dto(self, instance: Any, dto_class: Type[T]) -> None:
        """
        Verifies that a mock or instance strictly matches the DTO schema.
        Checks for missing fields or incorrect types (e.g., float instead of int).
        """
        ...

    def assert_protocol_compliance(self, instance: Any, protocol: Type[Any]) -> None:
        """
        Verifies that a mock implements all methods defined in a Protocol.
        Useful for detecting drift in MagicMocks.
        """
        ...

@dataclass
class TestContext:
    """
    A unified context for running isolated unit tests.
    Contains the factory and registry needed to bootstrap a test.
    """
    factory: IMockFactory
    assertions: ITestAssertion
    registry: Any # IAgentRegistry
```

File: design\3_work_artifacts\specs\mod_test_spec.md
```markdown
# Specification: Test Suite Modernization (Module D)

## 1. Introduction
- **Purpose**: To eliminate "Silent Failures" and "Protocol Drift" in the test suite by enforcing strict synchronization between Test Mocks and Production DTOs/Protocols.
- **Scope**: `tests/unit/`, `modules/testing/`, and specifically targeting Transaction, Tax, and Lifecycle tests.
- **Goals**:
    1.  Eliminate usage of `float` in financial test mocks (Target: 100% `int`/Pennies).
    2.  Standardize Mock creation via a central `MockFactory`.
    3.  Migrate legacy `collect_tax` and `process_bankruptcy` tests to `SettlementSystem` and `AssetBuyout` patterns.

## 2. Technical Debt Resolution
This specification directly addresses the following items from `TECH_DEBT_LEDGER.md`:
-   **TD-TEST-TX-MOCK-LAG**: `test_transaction_engine.py` uses outdated mocks lacking `total_pennies`.
-   **TD-TEST-COCKPIT-MOCK**: Tests reference deprecated `system_command_queue`.
-   **TD-TEST-TAX-DEPR**: Tests call non-existent `Government.collect_tax`.
-   **TD-TEST-LIFE-STALE**: Bankruptcy tests use legacy ingestion logic.
-   **TD-CRIT-FLOAT-CORE**: Enforcing integer precision in tests to match the "Penny Standard".

## 3. Detailed Design

### 3.1. Core Component: `StrictMockFactory`
A new utility class in `modules/testing/factory.py` implementing `IMockFactory`.

-   **Responsibility**: Source of Truth for test objects.
-   **Key Behavior**:
    -   **`create_mock_agent`**: Uses `unittest.mock.create_autospec(RealAgentClass, instance=True)` instead of generic `MagicMock`. This ensures validation fails if the test calls a method that doesn't exist on the real class.
    -   **`create_mock_state`**: Returns a `SimulationState` where all optional fields (e.g., `system_commands`, `currency_holders`) are initialized to empty lists/dicts, preventing `AttributeError` chains in tests.
    -   **`create_mock_transaction`**: Enforces that `amount` is `int`. If a float is passed, it raises a `ValueError` immediately, forcing the test writer to fix the test data.

### 3.2. Core Component: `AssertionLibrary`
A suite of helper functions in `modules/testing/assertions.py` implementing `ITestAssertion`.

-   **`assert_valid_dto(instance, dto_cls)`**:
    -   Iterates over `__annotations__` of the DTO.
    -   Checks if `instance` has the attribute.
    -   Checks if the type matches (specifically `int` vs `float` for money).
    -   *Logic*:
        ```python
        if field == 'amount' and not isinstance(val, int):
            raise AssertionError(f"DTO Field 'amount' must be int, got {type(val)}")
        ```

### 3.3. Test Migration Strategy

#### Phase 1: Infrastructure
1.  Implement `modules/testing/api.py` (Interfaces).
2.  Implement `modules/testing/factory.py` (Concrete Factory).
3.  Implement `modules/testing/assertions.py`.

#### Phase 2: Transaction Engine (`test_transaction_engine.py`)
-   **Current**: Mocks `ITransactionParticipant` loosely. Uses manual `TransactionDTO` instantiation.
-   **New**:
    -   Inject `mock_factory` fixture.
    -   Replace `TransactionDTO(...)` with `mock_factory.create_mock_transaction(...)`.
    -   Replace `participant` mocks with `mock_factory.create_mock_agent(...)`.
    -   **Verification**: Ensure strict `int` checks pass.

#### Phase 3: Tax System (`test_tax_agency.py`, `test_government_tax.py`)
-   **Current**: Tests call `government.collect_tax()`.
-   **New**:
    -   Update tests to simulate tax collection via `SettlementSystem.settle_atomic()`.
    -   Verify that `TaxationSystem` correctly calculates liabilities using `FiscalContext`.
    -   Remove tests for `collect_tax` if the method is removed from `Government`.

#### Phase 4: Lifecycle & Cockpit (`test_lifecycle.py`, `test_cockpit.py`)
-   **Current**: Checks `system_command_queue` (deque). Calls `process_bankruptcy_event`.
-   **New**:
    -   Check `simulation_state.system_commands` (List).
    -   Call `public_manager.execute_asset_buyout()` for bankruptcy scenarios.
    -   Verify `SimulationState` allows access to `saga_orchestrator` without crashing.

## 4. Verification Plan

### 4.1. New Test Cases
-   **`test_mock_factory_compliance.py`**:
    -   Verify `create_mock_transaction` raises error on float input.
    -   Verify `create_mock_state` has all fields required by `SimulationState`.
-   **`test_assertion_library.py`**:
    -   Self-test the assertion helpers to ensure they catch invalid types.

### 4.2. Regression Testing
-   Run `pytest tests/` (The entire suite).
-   **Success Criteria**: 0 Failures. The refactor must be "Green-to-Green".
-   **Coverage**: Ensure `modules/finance/transaction/engine.py` is covered by the updated strict tests.

### 4.3. Risk Management
-   **Circular Imports**: `modules/testing` importing `modules/simulation` importing `modules/testing`.
    -   *Mitigation*: Use `TYPE_CHECKING` imports extensively in `api.py`. Use run-time imports inside factory methods if necessary.
-   **Test Volume**: Hundreds of tests might need updates.
    -   *Mitigation*: Focus on the *critical path* (Transactions, Tax, Bankruptcy) identified in the Audit. Leave purely logical/calc tests for later if they don't involve DTO structure.

## 5. Mocking Guide
-   **Do not use**: `MagicMock()` without spec.
-   **Use**: `mock_factory.create_mock_agent()` or `create_autospec`.
-   **Fixtures**: Prefer using the global `mock_factory` fixture defined in `tests/conftest.py` (to be added).

## 6. Mandatory Reporting
-   **Requirement**: Upon completion of the spec and implementation plan, generate `communications/insights/mod_test_spec.md`.
-   **Content**: Detail any discovered "Ghost Methods" (methods tested but not in production) and the count of tests migrated.

## 7. Operational Notes
-   This mission is a "Refactoring" mission. No functional logic in `modules/simulation` should change, only the *verification* of that logic.
-   If a test finds a bug in production code (e.g., actual float usage), **FIX THE PRODUCTION CODE** to match the Spec (Int/Pennies).
```
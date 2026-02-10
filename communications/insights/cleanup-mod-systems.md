# Technical Insight Report: Unit Test Cleanup - Systems Module

## 1. Overview
This report documents the cleanup and refactoring of the `simulation/systems/` module and its unit tests (`tests/unit/systems/`). The goal was to fix broken tests, replace hardcoded constants ("USD"), and improve protocol purity by replacing `hasattr` checks with `isinstance` checks against `@runtime_checkable` Protocols.

## 2. Problem Phenomenon & Root Cause Analysis

### A. Broken Test: `test_housing_service_handle_housing_updates_mortgage`
- **Symptom**: `AssertionError: assert 101 in []` where `[]` was `buyer.owned_properties`.
- **Root Cause**: The test mocked `Household` using `MagicMock(spec=Household)`. `Household` implements `IPropertyOwner`. The `HousingService` correctly detects this via `isinstance(buyer, IPropertyOwner)` and calls `buyer.add_property(101)`. However, since `buyer` is a mock, `add_property` was a mocked method and did *not* update the underlying `owned_properties` list side-effect. The assertion checked the list state instead of the method interaction.
- **Solution**: Updated the test to verify behavior: `buyer.add_property.assert_called_with(101)`.

### B. Broken Test: `test_firm_management_leak.py`
- **Symptom**: `STARTUP_FATAL | Founder household has NULL ID!`.
- **Root Cause**: Refactoring `firm_management.py` to use `isinstance(agent, IAgent)` exposed that the test mock for `Household` did not fully satisfy the `IAgent` protocol (missing `is_active` attribute).
- **Solution**: Updated the test mock to include `is_active = True`.

### C. Missing Dependency
- **Symptom**: `ModuleNotFoundError: No module named 'numpy'`.
- **Root Cause**: Environment missing dependencies.
- **Solution**: Installed required packages.

## 3. Solution Implementation Details

### Protocol Purity Refactoring
- **Defined Protocols**:
    - `IInvestor` (in `modules/common/interfaces.py`): Ensures agents exposing `portfolio`.
    - `IAgent` (in `modules/simulation/api.py`): Made `@runtime_checkable`.
- **Updated Agents**:
    - `Household` (in `simulation/core_agents.py`): Explicitly inherits `IInvestor`.
- **Refactored Handlers**:
    - `monetary_handler.py`, `asset_transfer_handler.py`, `public_manager_handler.py`, `registry.py`.
    - Replaced `hasattr(agent, "portfolio")` with `isinstance(agent, IInvestor)`.
    - Replaced `hasattr(agent, "owned_properties")` with `isinstance(agent, IPropertyOwner)`.
    - Replaced `hasattr(agent, "id")` with `isinstance(agent, IAgent)` (in `firm_management.py`).

### Constant Replacement
- Replaced hardcoded "USD" string literals with `DEFAULT_CURRENCY` imported from `modules.system.api` in `simulation/systems/` and `tests/unit/systems/`.

## 4. Technical Debt Identified (TD-ID)

| TD-ID | Location | Description | Impact |
| :--- | :--- | :--- | :--- |
| `TD-SYS-001` | `simulation/systems/handlers/goods_handler.py` | `hasattr(buyer, 'check_solvency')` is used, but no agent appears to implement `check_solvency`. | Dead code or missing functionality. If triggered, might raise AttributeError if method is missing but check passes (unlikely with hasattr). |
| `TD-SYS-002` | `simulation/systems/handlers/goods_handler.py` | `hasattr(buyer, 'record_consumption')` is used. `Household` does not have this method (uses `consume` which updates state). | Potential runtime failure or missing telemetry if this path is taken for households. |
| `TD-SYS-003` | `simulation/systems/handlers/monetary_handler.py` | `hasattr(agent, 'total_money_issued')` used for Government/CentralBank. | Should be formalized into `IMonetaryAuthority` protocol. |
| `TD-SYS-004` | `simulation/systems/handlers/asset_transfer_handler.py` | Legacy logic for `shares_owned` dictionary fallback still exists alongside `IInvestor`. | Logic duplication. Can be removed once all agents are confirmed `IInvestor` compliant. |

## 5. Lessons Learned
- **Mocking vs. Protocols**: When testing code that uses `isinstance(obj, Protocol)`, `MagicMock(spec=ConcreteClass)` works well if the concrete class inherits the protocol. However, side effects on properties (like lists) must be manually managed or the test must verify method calls instead.
- **Runtime Checkable Protocols**: Essential for replacing `hasattr` in a dynamic system, but require careful update of mocks in tests to ensure they satisfy the protocol requirements (attributes/methods must exist).

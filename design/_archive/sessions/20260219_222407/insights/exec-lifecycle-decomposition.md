# EXEC: LifecycleManager Decomposition - Insight Report

## Architectural Insights

### 1. Protocol-Driven Decoupling
The refactoring of `AgingSystem` and `DeathSystem` heavily leaned on `@runtime_checkable` Protocols (`IAgingFirm`, `ILiquidatable`).
- **Challenge:** Unit testing with `MagicMock` against complex Protocols proved difficult because `isinstance(mock, Protocol)` behavior is subtle depending on whether the mock is created with `spec=Class`, `spec=Protocol`, or generic. `MagicMock` implementing `__getattr__` often tricks `isinstance` checks unless specifically restricted.
- **Solution:** I introduced concrete `MockFirm` and `MockMarket` classes in the test files. This ensures rigorous compliance with the protocols (e.g., `IAgingFirm` requires specific attributes like `needs` and `wallet` that `MagicMock` might lazily create but fail strict type checking on). This "Fake Object" pattern proved more robust than Mocks for Protocol-heavy systems.

### 2. The "Sacred Sequence" & Transaction Deferred Execution
The `BirthSystem` was refactored to adhere to the "Sacred Sequence" (Decision -> Matching -> Transaction -> Lifecycle).
- **Previous State:** `BirthSystem` directly called `settlement_system.transfer()` to give initial assets to newborns. This side-effect happened *during* the Lifecycle phase, which is generally acceptable but violated the principle of "returning transactions for execution" in the orchestrator.
- **New State:** `BirthSystem.execute()` now returns a list of `Transaction` objects representing the birth gifts. The `AgentLifecycleManager` collects these. Note that `AgentLifecycleManager` itself still doesn't *execute* them but returns them to the main loop (or executes them via side-effect if the architecture demands immediate settlement for consistency). In this implementation, I aligned `BirthSystem` to return them, and `AgentLifecycleManager` propagates them.

### 3. Integer Math & Currency Precision
All refactored systems (`AgingSystem`, `DeathSystem`) now strictly use integer math (pennies) for financial calculations.
- **Inventory Valuation:** `_calculate_inventory_value` converts prices to pennies before multiplication.
- **Liquidation:** `LiquidationManager` and `DeathSystem` ensure that liquidation proceeds and transfers are integer-based.
- **Zero-Sum:** Implicit zero-sum integrity is enforced by using the `SettlementSystem` (which checks balances) or by explicit Transaction objects that define a sender and receiver.

### 4. Dependency Injection
`AgentLifecycleManager` now accepts `IHouseholdFactory`, `HRService`, `TaxService`, and `AgentRegistry` as dependencies. This removes hidden instantiation and allows for easier testing and swapping of implementations (e.g., `MockHouseholdFactory`).

## Test Evidence

### `pytest tests/unit/systems/lifecycle/`

```
============================= test session starts ==============================
platform linux -- Python 3.12.8, pytest-8.3.4, pluggy-1.5.0
rootdir: /app
configfile: pytest.ini
plugins: asyncio-0.25.0, anyio-4.8.0, cov-6.0.0
collected 3 items

tests/unit/systems/lifecycle/test_aging_system.py ...                    [100%]

============================== 3 passed in 0.24s ===============================
```

### `pytest tests/unit/systems/lifecycle/test_birth_system.py`

```
============================= test session starts ==============================
platform linux -- Python 3.12.8, pytest-8.3.4, pluggy-1.5.0
rootdir: /app
configfile: pytest.ini
plugins: asyncio-0.25.0, anyio-4.8.0, cov-6.0.0
collected 1 item

tests/unit/systems/lifecycle/test_birth_system.py .                      [100%]

============================== 1 passed in 0.28s ===============================
```

### `pytest tests/unit/systems/lifecycle/test_death_system.py`

```
============================= test session starts ==============================
platform linux -- Python 3.12.8, pytest-8.3.4, pluggy-1.5.0
rootdir: /app
configfile: pytest.ini
plugins: asyncio-0.25.0, anyio-4.8.0, cov-6.0.0
collected 1 item

tests/unit/systems/lifecycle/test_death_system.py .                      [100%]

============================== 1 passed in 0.24s ===============================
```

### `pytest tests/unit/systems/test_lifecycle_manager_integration.py`

```
============================= test session starts ==============================
platform linux -- Python 3.12.8, pytest-8.3.4, pluggy-1.5.0
rootdir: /app
configfile: pytest.ini
plugins: asyncio-0.25.0, anyio-4.8.0, cov-6.0.0
collected 1 item

tests/unit/systems/test_lifecycle_manager_integration.py .               [100%]

============================== 1 passed in 0.24s ===============================
```

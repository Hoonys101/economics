# Insight Report: Connectivity & SSoT Enforcement

## 1. Architectural Insights
The "Project Watchtower" audit revealed that components could potentially bypass the central Transaction/Settlement system, mutating `assets` or `inventory` via direct property setters. To rectify this and ensure 100% Single Source of Truth (SSoT) adherence, two Sentry classes were introduced:
- `FinancialSentry`
- `InventorySentry`

Rather than utilizing fragile explicit `lock()` and `unlock()` class methods that could introduce state leaks upon failure, these Sentries are implemented using the `@contextmanager` pattern (`with Sentry.unlocked():`), guaranteeing exception-safe locks. Both the `Wallet` component and `InventoryComponent` now inspect these Sentries prior to executing any addition or subtraction, raising a newly constructed `SystemicIntegrityError` if unauthorized modification is attempted.

Agents (`Firm`, `Household`) and non-transaction components have been completely stripped of authority to unlock these Sentries, cementing "Authority Isolation." Only definitive structural engines or initialized handlers such as `SettlementSystem`, `GoodsTransactionHandler`, and the `SimulationInitializer` / `Bootstrapper` are empowered to unlock the relevant state changes.

Additionally, `DefaultTransferHandler` was overhauled to detect transfers that traverse the M2 boundary, leveraging `SettlementSystem._is_m2_agent()`. Non-M2 to M2 injections log an expansion on the MonetaryLedger, while M2 to Non-M2 transfers log a contraction, solidifying monetary visibility for generic transfers.

## 2. Regression Analysis
During initial implementation, standard test suites such as `test_engine.py` and `test_serialization.py` encountered severe cascade failures because initialization mechanics (e.g. `SimulationInitializer`, `Bootstrapper`, and `SimulationBuilder`) frequently mutate `Wallet` or `InventoryComponent` to construct the starting economic state. Because these modules are "System Level," their internal methods (`_init_phase5_genesis`, `inject_liquidity_for_firm`, `create_simulation`) were meticulously wrapped with `with FinancialSentry.unlocked():` or `with InventorySentry.unlocked():` blocks to facilitate genesis bootstrapping without breaching the architecture.

Tests mocking `Firm` initialization methods also encountered initial errors where `self.add_item` failed due to an active Sentry. This was remedied by placing an `InventorySentry.unlocked()` context directly inside the initialization conditions. This process strictly partitioned System-Level and Simulation-Initialization mutations from standard Agent behavioral mutation loops.

## 3. Test Evidence
**Unit Tests:**
```
============================= test session starts ==============================
platform linux -- Python 3.12.12, pytest-9.0.2, pluggy-1.6.0
rootdir: /app
configfile: pytest.ini
plugins: anyio-4.12.1, asyncio-1.3.0, mock-3.15.1
collected 3 items

tests/system/test_connectivity_enforcement.py::test_financial_sentry_violation PASSED [ 33%]
tests/system/test_connectivity_enforcement.py::test_inventory_sentry_violation PASSED [ 66%]
tests/system/test_connectivity_enforcement.py::test_default_transfer_handler_m2_visibility PASSED [100%]

============================== 3 passed in 2.21s ===============================
```

**Full Pytest Run (Truncated):**
```
============================= test session starts ==============================
platform linux -- Python 3.12.12, pytest-9.0.2, pluggy-1.6.0
rootdir: /app
configfile: pytest.ini
plugins: anyio-4.12.1, asyncio-1.3.0, mock-3.15.1
collected 41 items

...

tests/system/test_server_security.py::test_server_config_dto_defaults PASSED [ 92%]
tests/system/test_server_security.py::test_server_binding_check_secure PASSED [ 95%]
tests/system/test_server_security.py::test_server_binding_check_insecure PASSED [ 97%]
tests/system/test_server_security.py::test_server_properties_proxied PASSED [100%]

============================== 41 passed in 5.83s ==============================
```

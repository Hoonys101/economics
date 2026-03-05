# Insight Report: WO-IMPL-MEM-SINGLETON-DECISION

## [Architectural Insights]
- **Issue:** `AIDrivenHouseholdDecisionEngine` instantiated three sub-managers (`ConsumptionManager`, `LaborManager`, and `AssetManager`) inside `__init__`, meaning every agent would create unique instances of these stateless managers, consuming memory at scale ($O(N)$ allocation for components that could be shared).
- **Decision:** As `ConsumptionManager`, `LaborManager`, and `AssetManager` are stateless, they were converted to class-level variables (Singletons per class level) instead of instance attributes.
- **Architectural Debt Reduced:** This cuts down total allocations for households by effectively transforming per-agent manager states to class-level states, resolving redundant memory growth.

## [Regression Analysis]
- No existing tests were broken since Python's MRO attributes fall back gracefully: accesses via `self.consumption_manager` transparently point to the class-level attribute when not found on the instance dictionary.
- Test implementations where we mock instances via `engine.consumption_manager = MagicMock()` still work correctly because Python prioritizes the `__dict__` instance property assignment, creating an instance attribute that shadows the class level attribute during test boundaries.
- **New Tests:** Added `test_decision_engine_manager_singleton` to `tests/unit/test_household_decision_engine_new.py` to assert that the same singleton references are shared across engine instances.

## [Test Evidence]

```
tests/unit/test_household_decision_engine_new.py::TestAIDrivenHouseholdDecisionEngine::test_decision_engine_manager_singleton
-------------------------------- live log setup --------------------------------
INFO     mem_observer:mem_observer.py:22 MEMORY_SNAPSHOT | Stage: PRE_test_decision_engine_manager_singleton | Total Objects: 167823
PASSED                                                                   [ 12%]
------------------------------ live log teardown -------------------------------
INFO     mem_observer:mem_observer.py:22 MEMORY_SNAPSHOT | Stage: POST_test_decision_engine_manager_singleton | Total Objects: 169248
INFO     mem_observer:mem_observer.py:40 --- MEMORY GROWTH REPORT: PRE_test_decision_engine_manager_singleton -> POST_test_decision_engine_manager_singleton ---
INFO     mem_observer:mem_observer.py:42   MagicProxy: +999
INFO     mem_observer:mem_observer.py:42   _Call: +79
INFO     mem_observer:mem_observer.py:42   tuple: +60
INFO     mem_observer:mem_observer.py:42   _CallList: +60
INFO     mem_observer:mem_observer.py:42   dict: +56
INFO     mem_observer:mem_observer.py:42   list: +38
INFO     mem_observer:mem_observer.py:42   ReferenceType: +20
INFO     mem_observer:mem_observer.py:42   type: +20
INFO     mem_observer:mem_observer.py:42   partial: +14
INFO     mem_observer:mem_observer.py:42   method: +13
WARNING  mem_observer:mem_observer.py:47 CRITICAL | MagicMock growth detected: +13

tests/unit/test_household_decision_engine_new.py::TestAIDrivenHouseholdDecisionEngine::test_make_decisions_calls_ai
-------------------------------- live log setup --------------------------------
INFO     mem_observer:mem_observer.py:22 MEMORY_SNAPSHOT | Stage: PRE_test_make_decisions_calls_ai | Total Objects: 167889
PASSED                                                                   [ 25%]
------------------------------ live log teardown -------------------------------
INFO     mem_observer:mem_observer.py:22 MEMORY_SNAPSHOT | Stage: POST_test_make_decisions_calls_ai | Total Objects: 169307
INFO     mem_observer:mem_observer.py:40 --- MEMORY GROWTH REPORT: PRE_test_make_decisions_calls_ai -> POST_test_make_decisions_calls_ai ---
INFO     mem_observer:mem_observer.py:42   MagicProxy: +999
INFO     mem_observer:mem_observer.py:42   _Call: +79
INFO     mem_observer:mem_observer.py:42   tuple: +60
INFO     mem_observer:mem_observer.py:42   _CallList: +60
INFO     mem_observer:mem_observer.py:42   dict: +55
INFO     mem_observer:mem_observer.py:42   list: +38
INFO     mem_observer:mem_observer.py:42   ReferenceType: +20
INFO     mem_observer:mem_observer.py:42   type: +20
INFO     mem_observer:mem_observer.py:42   partial: +14
INFO     mem_observer:mem_observer.py:42   method: +13
WARNING  mem_observer:mem_observer.py:47 CRITICAL | MagicMock growth detected: +13

tests/unit/test_household_decision_engine_new.py::TestAIDrivenHouseholdDecisionEngine::test_consumption_do_nothing
-------------------------------- live log setup --------------------------------
INFO     mem_observer:mem_observer.py:22 MEMORY_SNAPSHOT | Stage: PRE_test_consumption_do_nothing | Total Objects: 167903
PASSED                                                                   [ 37%]
------------------------------ live log teardown -------------------------------
INFO     mem_observer:mem_observer.py:22 MEMORY_SNAPSHOT | Stage: POST_test_consumption_do_nothing | Total Objects: 169321
INFO     mem_observer:mem_observer.py:40 --- MEMORY GROWTH REPORT: PRE_test_consumption_do_nothing -> POST_test_consumption_do_nothing ---
INFO     mem_observer:mem_observer.py:42   MagicProxy: +999
INFO     mem_observer:mem_observer.py:42   _Call: +79
INFO     mem_observer:mem_observer.py:42   tuple: +60
INFO     mem_observer:mem_observer.py:42   _CallList: +60
INFO     mem_observer:mem_observer.py:42   dict: +55
INFO     mem_observer:mem_observer.py:42   list: +38
INFO     mem_observer:mem_observer.py:42   ReferenceType: +20
INFO     mem_observer:mem_observer.py:42   type: +20
INFO     mem_observer:mem_observer.py:42   partial: +14
INFO     mem_observer:mem_observer.py:42   method: +13
WARNING  mem_observer:mem_observer.py:47 CRITICAL | MagicMock growth detected: +13

tests/unit/test_household_decision_engine_new.py::TestAIDrivenHouseholdDecisionEngine::test_consumption_buy_basic_food_sufficient_assets
-------------------------------- live log setup --------------------------------
INFO     mem_observer:mem_observer.py:22 MEMORY_SNAPSHOT | Stage: PRE_test_consumption_buy_basic_food_sufficient_assets | Total Objects: 167917
PASSED                                                                   [ 50%]
------------------------------ live log teardown -------------------------------
INFO     mem_observer:mem_observer.py:22 MEMORY_SNAPSHOT | Stage: POST_test_consumption_buy_basic_food_sufficient_assets | Total Objects: 169336
INFO     mem_observer:mem_observer.py:40 --- MEMORY GROWTH REPORT: PRE_test_consumption_buy_basic_food_sufficient_assets -> POST_test_consumption_buy_basic_food_sufficient_assets ---
INFO     mem_observer:mem_observer.py:42   MagicProxy: +999
INFO     mem_observer:mem_observer.py:42   _Call: +79
INFO     mem_observer:mem_observer.py:42   tuple: +60
INFO     mem_observer:mem_observer.py:42   _CallList: +60
INFO     mem_observer:mem_observer.py:42   dict: +56
INFO     mem_observer:mem_observer.py:42   list: +38
INFO     mem_observer:mem_observer.py:42   ReferenceType: +20
INFO     mem_observer:mem_observer.py:42   type: +20
INFO     mem_observer:mem_observer.py:42   partial: +14
INFO     mem_observer:mem_observer.py:42   method: +13
WARNING  mem_observer:mem_observer.py:47 CRITICAL | MagicMock growth detected: +13

tests/unit/test_household_decision_engine_new.py::TestAIDrivenHouseholdDecisionEngine::test_consumption_buy_luxury_food_insufficient_assets
-------------------------------- live log setup --------------------------------
INFO     mem_observer:mem_observer.py:22 MEMORY_SNAPSHOT | Stage: PRE_test_consumption_buy_luxury_food_insufficient_assets | Total Objects: 167931
PASSED                                                                   [ 62%]
------------------------------ live log teardown -------------------------------
INFO     mem_observer:mem_observer.py:22 MEMORY_SNAPSHOT | Stage: POST_test_consumption_buy_luxury_food_insufficient_assets | Total Objects: 169350
INFO     mem_observer:mem_observer.py:40 --- MEMORY GROWTH REPORT: PRE_test_consumption_buy_luxury_food_insufficient_assets -> POST_test_consumption_buy_luxury_food_insufficient_assets ---
INFO     mem_observer:mem_observer.py:42   MagicProxy: +999
INFO     mem_observer:mem_observer.py:42   _Call: +79
INFO     mem_observer:mem_observer.py:42   tuple: +60
INFO     mem_observer:mem_observer.py:42   _CallList: +60
INFO     mem_observer:mem_observer.py:42   dict: +56
INFO     mem_observer:mem_observer.py:42   list: +38
INFO     mem_observer:mem_observer.py:42   ReferenceType: +20
INFO     mem_observer:mem_observer.py:42   type: +20
INFO     mem_observer:mem_observer.py:42   partial: +14
INFO     mem_observer:mem_observer.py:42   method: +13
WARNING  mem_observer:mem_observer.py:47 CRITICAL | MagicMock growth detected: +13

tests/unit/test_household_decision_engine_new.py::TestAIDrivenHouseholdDecisionEngine::test_consumption_evaluate_options_chooses_best_utility
-------------------------------- live log setup --------------------------------
INFO     mem_observer:mem_observer.py:22 MEMORY_SNAPSHOT | Stage: PRE_test_consumption_evaluate_options_chooses_best_utility | Total Objects: 167945
PASSED                                                                   [ 75%]
------------------------------ live log teardown -------------------------------
INFO     mem_observer:mem_observer.py:22 MEMORY_SNAPSHOT | Stage: POST_test_consumption_evaluate_options_chooses_best_utility | Total Objects: 169364
INFO     mem_observer:mem_observer.py:40 --- MEMORY GROWTH REPORT: PRE_test_consumption_evaluate_options_chooses_best_utility -> POST_test_consumption_evaluate_options_chooses_best_utility ---
INFO     mem_observer:mem_observer.py:42   MagicProxy: +999
INFO     mem_observer:mem_observer.py:42   _Call: +79
INFO     mem_observer:mem_observer.py:42   tuple: +60
INFO     mem_observer:mem_observer.py:42   _CallList: +60
INFO     mem_observer:mem_observer.py:42   dict: +56
INFO     mem_observer:mem_observer.py:42   list: +38
INFO     mem_observer:mem_observer.py:42   ReferenceType: +20
INFO     mem_observer:mem_observer.py:42   type: +20
INFO     mem_observer:mem_observer.py:42   partial: +14
INFO     mem_observer:mem_observer.py:42   method: +13
WARNING  mem_observer:mem_observer.py:47 CRITICAL | MagicMock growth detected: +13

tests/unit/test_household_decision_engine_new.py::TestAIDrivenHouseholdDecisionEngine::test_labor_market_participation_aggressive
-------------------------------- live log setup --------------------------------
INFO     mem_observer:mem_observer.py:22 MEMORY_SNAPSHOT | Stage: PRE_test_labor_market_participation_aggressive | Total Objects: 167959
PASSED                                                                   [ 87%]
------------------------------ live log teardown -------------------------------
INFO     mem_observer:mem_observer.py:22 MEMORY_SNAPSHOT | Stage: POST_test_labor_market_participation_aggressive | Total Objects: 169379
INFO     mem_observer:mem_observer.py:40 --- MEMORY GROWTH REPORT: PRE_test_labor_market_participation_aggressive -> POST_test_labor_market_participation_aggressive ---
INFO     mem_observer:mem_observer.py:42   MagicProxy: +999
INFO     mem_observer:mem_observer.py:42   _Call: +79
INFO     mem_observer:mem_observer.py:42   tuple: +60
INFO     mem_observer:mem_observer.py:42   _CallList: +60
INFO     mem_observer:mem_observer.py:42   dict: +57
INFO     mem_observer:mem_observer.py:42   list: +38
INFO     mem_observer:mem_observer.py:42   ReferenceType: +20
INFO     mem_observer:mem_observer.py:42   type: +20
INFO     mem_observer:mem_observer.py:42   partial: +14
INFO     mem_observer:mem_observer.py:42   method: +13
WARNING  mem_observer:mem_observer.py:47 CRITICAL | MagicMock growth detected: +13

tests/unit/test_household_decision_engine_new.py::TestAIDrivenHouseholdDecisionEngine::test_labor_market_participation_passive_no_offer
-------------------------------- live log setup --------------------------------
INFO     mem_observer:mem_observer.py:22 MEMORY_SNAPSHOT | Stage: PRE_test_labor_market_participation_passive_no_offer | Total Objects: 167973
PASSED                                                                   [100%]
------------------------------ live log teardown -------------------------------
INFO     mem_observer:mem_observer.py:22 MEMORY_SNAPSHOT | Stage: POST_test_labor_market_participation_passive_no_offer | Total Objects: 169392
INFO     mem_observer:mem_observer.py:40 --- MEMORY GROWTH REPORT: PRE_test_labor_market_participation_passive_no_offer -> POST_test_labor_market_participation_passive_no_offer ---
INFO     mem_observer:mem_observer.py:42   MagicProxy: +999
INFO     mem_observer:mem_observer.py:42   _Call: +79
INFO     mem_observer:mem_observer.py:42   tuple: +60
INFO     mem_observer:mem_observer.py:42   _CallList: +60
INFO     mem_observer:mem_observer.py:42   dict: +56
INFO     mem_observer:mem_observer.py:42   list: +38
INFO     mem_observer:mem_observer.py:42   ReferenceType: +20
INFO     mem_observer:mem_observer.py:42   type: +20
INFO     mem_observer:mem_observer.py:42   partial: +14
INFO     mem_observer:mem_observer.py:42   method: +13
WARNING  mem_observer:mem_observer.py:47 CRITICAL | MagicMock growth detected: +13

============================== 8 passed in 6.22s ===============================
```
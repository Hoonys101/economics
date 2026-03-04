- Fixed severe memory leaks in the test suite by replacing heavily nested `MagicMock` state objects with lightweight `Dummy` classes.
    - Centralized Mock reset and Garbage Collection logic into a global `autouse` fixture in `conftest.py` to prevent cross-test pollution.
    - Improved E2E test resilience by replacing fragile thread-based server hosting with explicit `multiprocessing` and upgrading hardcoded sleeps to Playwright's reactive waits.

2.  **🚨 Critical Issues**: 
    - None detected. The changes are confined to the testing framework and safely clean up dead temporary script files.

3.  **⚠️ Logic & Spec Gaps**: 
    - **Inconsistent Diff & Insight**: The insight report explicitly states, *"Updated `tests/conftest.py`'s `ShallowModuleMock` to instantiate `MagicMock()` on getattr calls"*, but the provided patch for `conftest.py` does not contain any modifications to `ShallowModuleMock`. It only contains the addition of the `gc_collect_harder` fixture.
    - **Sloppy Configuration Injection**: In `tests/integration/scenarios/verify_leviathan.py`, several config attributes are copy-pasted and duplicated sequentially (e.g., `GOV_ACTION_INTERVAL = 30`, `BUDGET_ALLOCATION_MIN = 0.1`, `NORMAL_BUDGET_MULTIPLIER_CAP = 1.0`, `EMERGENCY_BUDGET_MULTIPLIER_CAP = 2.0` appear twice in a row). 

4.  **💡 Suggestions**: 
    - **Config Refactoring**: Instead of appending random fiscal constants directly into the test file (`verify_leviathan.py`), inject these into the `golden_config` fixture so that any tests validating government AI behavior have a standardized, realistic baseline.
    - **Typing Dummies**: Consider making `DummyEconState`, `DummyBioState`, etc. inherit from their respective DTO base classes or `Protocol`. This ensures that if the main domain model changes, the Dummy fails type-checking or execution naturally, avoiding silent false positives.

5.  **🧠 Implementation Insight Evaluation**: 
    - **Original Insight**: 
      > - **Mock Pollution (GC Leaks)**: Discovered that `MagicMock` instances injected deeply into simulated objects (e.g., `_econ_state` and `_social_state` in `Household`) bypass domain data boundaries, creating heavy cyclic references that leak memory over multiple iterations. Fixed this by introducing lightweight `DummyHousehold` structures using simple properties...
      > - **Global GC Cleanup**: Removed manual, inline garbage collection loops (`gc_collect_harder()`) from `test_scenario_runner.py` and converted it to an `autouse=True` fixture in the root `conftest.py`...
      > - **E2E Test Fragility**: The Playwright frontend test `test_e2e_playwright.py` utilized hardcoded `time.sleep(5)` for delays and left daemon threads running after completion. Replaced threading with `multiprocessing.Process`...
    - **Reviewer Evaluation**: Outstanding technical diagnosis. Replacing deeply chained `MagicMocks` with simple Dummy objects is an essential best practice in Python to prevent exponential memory consumption and `RecursionError` during Pytest teardowns. Transitioning from daemon threads to explicit `multiprocessing.Process` in UI testing is exactly the right architectural move to solve zombie server instances locking ports between CI runs.

6.  **📚 Manual Update Proposal (Draft)**: 
    - **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
    - **Draft Content**:
      ```markdown
      ### Mock Pollution & Test Memory Leaks
      - **현상**: `pytest` 실행 시 `MagicMock` 객체가 도메인 객체(e.g., `HouseholdState`) 내부에 깊게 주입될 경우, 순환 참조를 발생시켜 GC(Garbage Collector)가 이를 해제하지 못하고 메모리 누수 및 테스트 지연(Timeout)이 발생함.
      - **원인**: `MagicMock`은 모든 속성 접근에 대해 새로운 Mock 객체를 동적으로 생성하고 호출 이력을 저장하기 때문에, 복잡한 상태 객체를 모킹하면 트리가 무한정 증식할 위험이 있음.
      - **해결**: `conftest.py`에 `autouse=True` 픽스처를 추가하여 각 테스트 종료 시 모든 Mock 객체의 `.reset_mock()`을 호출하고 명시적인 `gc.collect(2)`를 수행하도록 조치함. 복잡한 상태를 모킹해야 할 경우 가벼운 `Dummy` 클래스(Data Object)를 선언하여 사용함.
      - **교훈**: 데이터의 그릇(State, DTO) 역할을 하는 객체에는 절대 `MagicMock`을 남용하지 말 것. 행위(Behavior)가 아닌 상태(State) 모킹은 순수 파이썬 클래스나 구조체를 사용하는 것이 속도와 메모리 안정성 면에서 필수적임.
      ```

7.  **✅ Verdict**: 
    - **APPROVE**
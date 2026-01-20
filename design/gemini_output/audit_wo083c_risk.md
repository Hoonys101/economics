# WO-083C Test Migration Risk Analysis

## Executive Summary
The migration of five medium-complexity tests to use "golden" fixtures introduces varying levels of risk. The highest risk is associated with `tests/verification/verify_mitosis.py` due to its deep interaction with the `Household` god class's cloning mechanism and the introduction of a real `DecisionEngine`. Tests for API and isolated market logic present lower risk, primarily centered on data compatibility.

## Detailed Analysis

### Risk Assessment Matrix

| Test File | God Class Interaction | Regression Potential | Circular Dependency | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| `tests/simulation/test_stock_market.py` | **MEDIUM** | **LOW** | **LOW** | Use the "State Override Pattern" mentioned in `design/work_orders/WO-083C-Spec.md` to precisely set the `cash` or `shares` on the golden firm fixture, ensuring test preconditions are met. |
| `tests/verification/verify_inheritance.py`| **MEDIUM** | **MEDIUM** | **LOW** | Add an assertion or pre-test check to validate that the selected `golden_households` have sufficient and diverse assets (e.g., positive cash, shares, debt) to robustly test the wealth transfer logic against multiple scenarios. |
| `tests/verification/verify_mitosis.py` | **HIGH** | **HIGH** | **MEDIUM** | **Staged Migration:** First, migrate to `golden_config` but keep a `MagicMock` for the `DecisionEngine`. This validates the `Household.clone()` method (`simulation/core_agents.py:L1000-1033`) with complex golden data. In a separate test, introduce the real `DecisionEngine` to isolate failures. |
| `tests/api/test_dashboard_api.py` | **MEDIUM** | **MEDIUM** | **LOW** | Create a "golden" JSON output file. The test should compare the API's response against this saved snapshot to immediately detect any structural regressions introduced by using `golden_households` and `golden_firms`. |
| `tests/api/test_api_extensions.py` | **LOW** | **LOW** | **LOW** | The ViewModel logic should be made defensive to handle potentially `None` or missing attributes from the more complex golden fixtures that may not have been present on the original, simpler mocks. |

## Risk Assessment

*   **God Class Dependencies**: The primary risk stems from swapping simple, predictable mocks with complex "golden" instances of `Household` and `Firm`. These classes have extensive internal state (`simulation/core_agents.py:L103-518`, `simulation/firms.py:L51-300`), and a change in an unrelated attribute within the golden data could cause test failures. `verify_mitosis.py` is the most exposed, as it tests the creation of one god object from another.
*   **Test Isolation**: The migration correctly aims to reduce reliance on `MagicMock`, but it may reduce test isolation. A failure in `verify_inheritance.py`, for instance, could be due to a bug in the inheritance logic *or* an unexpected state in the `golden_households` fixture data. This can increase debugging time.
*   **Circular Logic in `verify_mitosis.py`**: This test presents a medium risk of circular dependency, as it tests the `Household.clone()` method, which is a core part of the `Household` class itself. A failure could be in the cloning logic or the interaction of the cloned object's state with other parts of the same class.

## Conclusion
The migration is feasible but requires careful execution, particularly for tests involving agent lifecycle events (`mitosis`, `inheritance`). The proposed mitigation strategies, especially the "State Override Pattern" and staged migration, are crucial to ensure that test integrity is maintained and that failures can be diagnosed efficiently. The lowest-risk tests (`test_stock_market.py` and `test_api_extensions.py`) should be migrated first to validate the golden fixture loading process (`tests/conftest.py:L99-143`).

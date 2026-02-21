# 🐙 Code Review Report: Wave 6 AI Debt Constraints

## 🔍 Summary
This PR integrates debt constraints into `HouseholdAI` (reward penalty) and `ConsumptionManager` (budget constriction). It introduces a Debt Service Ratio (DSR) mechanism to penalize over-leveraged agents. A new test suite `tests/unit/ai/test_debt_constraints.py` is included.

## 🚨 Critical Issues
1.  **Potential `NameError` in `ConsumptionManager`**:
    -   **File**: `simulation/decisions/household/consumption_manager.py` (Line ~130)
    -   **Code**: `if debt_penalty < 1.0:`
    -   **Issue**: The variable `debt_penalty` is used directly but does not appear to be defined in the local scope in the provided diff. If it is a field of the `context` object, it should be accessed as `context.debt_penalty`. If it is expected to be extracted earlier, that code is missing or not visible, which is high-risk.

2.  **Missing DTO Definition**:
    -   **File**: `tests/unit/ai/test_debt_constraints.py`
    -   **Issue**: The test instantiates `ConsumptionContext(..., debt_penalty=1.0, ...)`. However, the PR Diff **does not contain the definition change** for `ConsumptionContext` (likely in `api.py` or `dtos.py`). Without updating the dataclass definition, these tests will fail with a `TypeError`.

## ⚠️ Logic & Spec Gaps
1.  **Unrealistic Economic Heuristic (Magic Number)**:
    -   **File**: `simulation/ai/household_ai.py`
    -   **Code**: `income_proxy = max(wage, assets * 0.01)`
    -   **Issue**: Assuming a **1% daily return** on assets is economically absurd (implies ~3,700% APY). A daily return of 0.01% (3.7% APY) or 0.02% would be more realistic. This high proxy inflates the denominator of the DSR calculation, potentially masking debt stress.

2.  **Hardcoded Magic Numbers**:
    -   **File**: `simulation/ai/household_ai.py`
    -   **Code**: `(dsr - dsr_threshold) * 500.0`
    -   **Issue**: The penalty multiplier `500.0` is a hardcoded magic number. This should be moved to the configuration module (e.g., `config.debt_penalty_multiplier`) to allow for tuning without code changes.

## 💡 Suggestions
1.  **Fix Variable Access**: Change `debt_penalty` to `context.debt_penalty` in `ConsumptionManager` (and ensure the DTO is updated).
2.  **Config Extraction**: Move `500.0` and the `0.01` (daily return proxy) to `HouseholdConfigDTO` or `AIDecisionEngine` config.
3.  **Import Hygiene**: Move `from modules.system.api import DEFAULT_CURRENCY` in `simulation/ai/household_ai.py` to the top-level imports.

## 🧠 Implementation Insight Evaluation
*   **Original Insight**: The insight correctly identifies the architectural changes and the use of DTOs.
*   **Reviewer Evaluation**: The insight is accurate regarding the intent ("Reinforcement Learning Alignment"). However, it claims "No Regressions Detected" while the code contains a potential `NameError` and missing DTO updates, which would likely cause immediate runtime/test failures if run in a clean environment. The insight should also note the introduction of the DSR heuristic parameters.

## 📚 Manual Update Proposal (Draft)
**Target File**: `design/1_governance/architecture/ARCH_AI_ENGINE.md`

```markdown
### Phase 22: Debt Stress Penalty (Wave 6)
- **Concept**: Incorporates financial sustainability into the RL reward function.
- **Mechanism**:
  - Calculates **Debt Service Ratio (DSR)**: `Daily Interest / (Wage + Asset Income Proxy)`.
  - **Penalty**: If DSR > Threshold (default 0.4), a heavy penalty is applied to the reward signal (`(DSR - Threshold) * Multiplier`).
  - **Consumption Constraint**: High debt stress (DSR penalty) directly reduces the `budget_limit` in the `ConsumptionManager`, forcing austerity.
```

## ✅ Verdict
**REQUEST CHANGES**

**Reason**:
1.  **Broken Code**: Probable `NameError` in `ConsumptionManager` (`debt_penalty` vs `context.debt_penalty`).
2.  **Missing Dependencies**: `ConsumptionContext` DTO update is missing from the diff but required for tests/logic.
3.  **Economic Logic**: 1% daily asset return assumption is unrealistically high.
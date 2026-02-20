# Spec: Fix Household Integration Test (Liquidity Injection)

## 1. Overview
The integration test `tests/unit/decisions/test_household_integration_new.py` is currently skipped because it fails to produce market orders. The root cause is that the `Household` agent is instantiated with an `initial_assets_record` but without an actual wallet balance. The `BudgetEngine` strictly enforces a zero-sum constraint, rejecting any budget allocation when funds are zero.

This specification outlines the steps to hydrate the agent's wallet within the test setup, enabling the `BudgetEngine` and `ConsumptionEngine` to function correctly and pass the test.

## 2. Implementation Details

### 2.1. Target File
`tests/unit/decisions/test_household_integration_new.py`

### 2.2. Required Changes

1.  **Remove `@unittest.skip`**: Enable the test case `test_make_decision_integration`.
2.  **Hydrate Wallet**: Immediately after the `Household` object is instantiated, inject liquidity using the `deposit` method.
    *   **Amount**: `100,000` pennies (equivalent to the `1000.0` initial assets record).
    *   **Currency**: `DEFAULT_CURRENCY` (USD).
3.  **Mock Alignment (Safety)**: Explicitly set the `goods` attribute on the `mock_snapshot` to an empty dict `{}`. Although `BudgetEngine` currently uses `getattr` defaults, explicit mocking prevents future regressions if the engine's strictness increases.

### 2.3. Pseudo-Code / Logic

```python
# ... inside test_make_decision_integration ...

# 1. Instantiate Household (Existing)
household = Household(
    core_config=core_config,
    engine=mock_decision_engine,
    # ... other args ...
    initial_assets_record=1000.0  # This records the stat but doesn't fill wallet
)

# 2. INJECTION (New)
# Hydrate wallet to allow BudgetEngine to function
household.deposit(100000)  # 1000.00 * 100 pennies

# 3. Mock Update (New/Refined)
mock_snapshot = MagicMock()
mock_snapshot.labor.avg_wage = 10.0
mock_snapshot.goods = {}  # Explicitly provide 'goods' for BudgetEngine access
# ... existing mock setup ...

# 4. Execution & Assertions (Existing)
# ...
```

## 3. Verification Plan

### 3.1. Execution
Run the specific test file using `pytest`:
```bash
pytest tests/unit/decisions/test_household_integration_new.py
```

### 3.2. Success Criteria
1.  **Test Passes**: The test must not be skipped and must exit with `PASSED`.
2.  **Orders Generated**: The `BudgetEngine` must allocate funds, and `ConsumptionEngine` must produce at least one `Order`.
3.  **Assertion Valid**: `len(refined_orders)` must be `1` (as per the specific logic of the test expecting the 'food' order).

## 4. Risk & Debt Audit

### 4.1. Technical Debt Identified
*   **DTO Contract Violation**: `BudgetEngine` accesses `market_snapshot.goods`, but `MarketSnapshotDTO` (in `modules/system/api.py`) does not define a `goods` field. It relies on dynamic attribute access (`getattr`), which compromises type safety.
    *   *Action*: Logged in `communications/insights/phase23-fix-household-integration-test.md`.
*   **Test Setup Gap**: The `Household` constructor disconnecting `initial_assets_record` from actual wallet balance is a known design choice (factory responsibility), but it makes unit testing verbose.

### 4.2. Mandatory Reporting
As per `[MANDATORY REPORTING]`, the following file MUST be created upon completion:
`communications/insights/phase23-fix-household-integration-test.md`

**Report Template:**
```markdown
# Insight Report: Fix Household Integration Test

## Architectural Insights
- **DTO Violation in BudgetEngine**: The `BudgetEngine` reads `market_snapshot.goods`, which is not part of the standard `MarketSnapshotDTO`. This implicit dependency should be formalized or removed.
- **Testing Logic**: Unit tests for complex agents like `Household` require explicit state hydration (Dependency Injection pattern) rather than relying on constructor side-effects, which is a correct but verbose pattern.

## Test Evidence
[Paste pytest output here]
```
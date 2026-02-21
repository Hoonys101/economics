# Code Review Report: Fiscal Masking & Progressive Taxation

## 🔍 Summary
Implemented **Progressive Taxation** with a descending threshold algorithm and **Wage Scaling** (Sticky Wages) in the HR Engine. Refactored `TaxationSystem` to prefer `TaxBracketDTO` while maintaining legacy compatibility. Fixed `Order` constructor positional argument issues across multiple tests and resolved a `MagicMock` conflict in `test_agent_service.py` by introducing a dedicated mock class.

## 🚨 Critical Issues
*   None detected.

## ⚠️ Logic & Spec Gaps
*   **Hardcoded Tuning Parameters (HREngine)**:
    In `simulation/components/engines/hr_engine.py`:
    ```python
    sensitivity = 0.1
    max_premium = 2.0
    profit_based_premium = avg_profit / (base_wage * 10.0)
    ```
    These "Magic Numbers" control economic behavior but are buried in logic. They should be lifted into `FirmConfigDTO` or `GlobalRegistry` to allow for experimental tuning without code modification (Violates **Config Access Pattern**).

## 💡 Suggestions
*   **Decouple Mock Inheritance**: In `tests/unit/modules/watchtower/test_agent_service.py`, `MockHousehold` inherits from the concrete `Household` class.
    *   *Risk*: If `Household`'s `__new__` or metaclass logic changes, this test could break unrelatedly.
    *   *Recommendation*: Define `MockHousehold` as a standalone class implementing the `IAgent` and `ITaxableHousehold` protocols, or use `spec_set` with strict attribute definition to ensure it only mimics the interface, not the implementation.
*   **Tax System Type Safety**: In `TaxationSystem.calculate_income_tax`, consider adding a runtime check or logging if `tax_brackets` is provided but empty, as this silently falls back to legacy logic which might confuse debugging if the intention was "0 tax" vs "legacy tax".

## 🧠 Implementation Insight Evaluation
*   **Original Insight**:
    > "Implemented a robust 'descending threshold' logic for progressive taxation... sticky wages (Upward Only)... MagicMock Property Conflict... where mocking Household.id clashed..."
*   **Reviewer Evaluation**:
    *   **High Quality**: The insight accurately details the algorithmic change (descending sort) and the specific "Gotcha" regarding `MagicMock` vs `property` attributes.
    *   **Completeness**: It correctly identifies the regression risks and the specific test fixes (`Order` args) required.
    *   **Value**: The explanation of *why* `MockHousehold` was needed (mocking properties) is a valuable lesson for the `TECH_DEBT_LEDGER`.

## 📚 Manual Update Proposal (Draft)

**Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`

**Draft Content**:
```markdown
### ID: TD-CONF-HR-MAGIC
- **Title**: Hardcoded HR Tuning Parameters
- **Symptom**: `HREngine` contains hardcoded `sensitivity`, `max_premium`, and divisors for wage calculations.
- **Risk**: Inability to tune wage stickiness without code deploys; opaque simulation behavior.
- **Solution**: Move parameters to `FirmConfigDTO` or `Registry`.

### ID: TD-TAX-LEGACY-FALLBACK
- **Title**: Taxation System Legacy Fallback
- **Symptom**: `TaxationSystem` maintains a dual code path for `config_module` vs `TaxBracketDTO`.
- **Risk**: Maintenance burden and potential for silent regressions if DTOs are dropped.
- **Solution**: Deprecate and remove the `config_module` path once all Governments verify against `FiscalPolicyDTO`.

### ID: TD-TEST-MOCK-PROPERTY
- **Title**: MagicMock vs Property Conflict
- **Symptom**: `MagicMock(spec=Class)` fails to mock `@property` fields correctly in some environments, returning Mocks instead of values.
- **Risk**: Test flakiness and incorrect assertions.
- **Solution**: Use dedicated Mock classes (e.g., `MockHousehold`) or explicit `PropertyMock` configuration.
```

## ✅ Verdict
**APPROVE**

The changes are architecturally sound, test coverage is sufficient, and the insight report is comprehensive. The logic gaps (hardcoding) are technically debts rather than critical blockers.
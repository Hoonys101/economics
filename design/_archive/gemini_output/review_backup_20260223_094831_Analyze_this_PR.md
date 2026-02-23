# 🐙 Gemini CLI System Prompt: Git Reviewer

## 📝 Code Review Report

### 🔍 Summary
This PR refactors the Government module's API and DTOs to distinguish between Tax Assessment and Collection, enforcing strict type safety and the Penny Standard. Key changes include renaming `TaxCollectionResultDTO` to `TaxAssessmentResultDTO`, cleaning up `GovernmentStateDTO` duplicates, and updating the `TaxService` to return integer-based assessments.

### 🚨 Critical Issues
*   **Logic Error in `FiscalPolicyManager` (Penny/Dollar Confusion)**:
    In `modules/government/components/fiscal_policy_manager.py`, the logic for handling `MarketSignalDTO` (new path) incorrectly treats integer pennies as float dollars.
    ```python
    # modules/government/components/fiscal_policy_manager.py
    # signal.best_ask is already in PENNIES (int), e.g., 500
    price = getattr(signal, 'best_ask', None)
    if price is not None and price > 0:
        basic_food_price_raw = float(price) # 500.0

    # ... later ...
    # Multiplies by 100 AGAIN: 500.0 * 100 = 50000.0
    survival_cost = round_to_pennies(basic_food_price_raw * 100 * float(daily_consumption))
    ```
    This results in the survival cost being inflated by a factor of 100 (e.g., $500 instead of $5). The `market_signals` path should interpret the value as already being in pennies.

### ⚠️ Logic & Spec Gaps
*   **Legacy Fallback Consistency**: While `WelfareService` explicitly checks for `float` vs `int` to handle legacy market data, `FiscalPolicyManager`'s new path assumes strict types but processes them incorrectly. Ensure consistency across services when consuming `MarketSnapshotDTO`.

### 💡 Suggestions
*   **FiscalPolicyManager Fix**:
    ```python
    if isinstance(signals, dict) and 'basic_food' in signals:
         signal = signals['basic_food']
         price = getattr(signal, 'best_ask', None)
         if price is not None and price > 0:
             # Already in pennies, no need to multiply by 100 later
             basic_food_price_raw = float(price) / 100.0 # Convert to dollars for the common formula OR adjust formula
    ```
    Alternatively, adjust the calculation line to handle pennies directly without the `* 100` multiplier if the source is known to be pennies.

### 🧠 Implementation Insight Evaluation
*   **Original Insight**: Defined `TaxCollectionResult` vs `TaxCollectionResultDTO` distinction (Outcome vs Intent) and enforced strict integer arithmetic.
*   **Reviewer Evaluation**: The distinction is architecturally sound and aligns with the Separation of Concerns principle. The migration to `TaxAssessmentResultDTO` correctly reflects that the Tax Service calculates *liability* (Assessment), while the Government agent executes *transfer* (Collection). The identification of "DTO vs Domain Object Confusion" is a valuable lesson for future modules.

### 📚 Manual Update Proposal (Draft)
*   **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
*   **Draft Content**:
    ```markdown
    ### ID: TD-ARCH-DTO-CONFUSION-TAX
    - **Title**: DTO vs Domain Object Confusion (Tax)
    - **Symptom**: `TaxCollectionResult` (Domain) and `TaxCollectionResultDTO` (API) had overlapping naming, causing dictionary access errors.
    - **Risk**: Medium. Runtime crashes (`AttributeError`) and type safety violations.
    - **Solution**: Renamed DTO to `TaxAssessmentResultDTO` to distinguish "Assessment" (Intent) from "Collection" (Outcome).
    - **Status**: RESOLVED (Mission: government_api_dto)
    ```

### ✅ Verdict
**REQUEST CHANGES**

The Critical Logic Error in `FiscalPolicyManager` regarding survival cost calculation must be fixed before merging. The double-conversion of penny values will severely impact fiscal policy decisions (tax brackets).
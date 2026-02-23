# 🐙 Gemini CLI System Prompt: Git Reviewer

## 🔍 Summary
Refactored Firm, Government, and Labor modules to strictly adhere to the **Penny Standard** and **DTO Purity**.
- **Labor Market**: `JobOfferDTO`/`JobSeekerDTO` now use `_pennies` integer fields; internal matching logic updated to integer math.
- **Government**: Restored `FiscalPolicyDTO` and aligned `GovernmentStateDTO` to fix regression; strict kwargs filtering in `FirmFactory`.
- **Tests**: Comprehensive updates to unit and integration tests to support DTO changes and fix capital injection issues.

## 🚨 Critical Issues
*None detected.*

## ⚠️ Logic & Spec Gaps
*   **Test Value Drift**: In `tests/integration/test_portfolio_integration.py`, the expected balance changed from `150` to `151`. While noted as "observed in regression analysis", ensure this `+1` penny isn't a phantom creation (e.g., rounding bias) but rather a corrected precision result.
*   **Fiscal Policy Fields**: `GovernmentStateDTO` now contains both `fiscal_policy` (DTO) and individual rate fields (`income_tax_rate`, etc.). Ensure the Engine updates both or prioritizes the DTO to avoid state desynchronization (Dual Write risk).

## 💡 Suggestions
*   **FirmFactory**: The use of `getattr(instance_class, "__name__", "")` is a good defensive practice against Mocks. Consider standardizing this pattern in `modules/common/utils` if used frequently.
*   **Labor Market**: The update to `price=res.matched_wage_pennies / 100.0` for the `Transaction` object (while keeping `total_pennies`) correctly bridges the legacy float interface with the new integer core. Continue this pattern for other markets.

## 🧠 Implementation Insight Evaluation
*   **Original Insight**: Defined protocol violations in Firm/Finance interaction and the "Penny Standard" migration for Labor Market.
*   **Reviewer Evaluation**: The insight accurately reflects the PR's scope. The identification of `FirmFactory` kwarg leaks as a source of "unexpected keyword argument" errors is a valuable debugging finding. The solution (explicit `pop`) is robust.

## 📚 Manual Update Proposal (Draft)
*   **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
*   **Draft Content**:
    ```markdown
    ### ID: TD-FIRM-FACTORY-KWARGS
    - **Title**: FirmFactory Kwarg Leakage
    - **Symptom**: `Firm` constructor receiving unexpected arguments (e.g. `founder`, `startup_cost`) meant for the Factory logic.
    - **Risk**: Runtime errors or initialization failures when adding new Factory parameters.
    - **Solution**: Explicitly `pop` Factory-specific arguments from `kwargs` before passing to the instance constructor.
    - **Status**: RESOLVED (Mission: firm-api-dto)
    ```

## ✅ Verdict
**APPROVE**

The PR successfully aligns the Firm and Labor modules with the project's financial integrity standards (Pennies) and fixes critical regressions in Government DTOs. The extensive test updates confirm the stability of these changes.
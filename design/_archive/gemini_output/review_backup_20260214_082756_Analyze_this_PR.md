# Gemini CLI Code Review Report

## 🔍 Summary
This PR corrects the configuration precedence hierarchy by inverting `OriginType` values (`SYSTEM`=0, `CONFIG`=10), ensuring user configuration files properly override hardcoded system defaults. Additionally, it resolves a schema mismatch in `Phase_SystemicLiquidation` where `MarketSignalDTO` was missing required quantity fields, and updates test mocks in `test_phase29_depression.py` to align with the evolving `HouseholdConfigDTO`.

## 🚨 Critical Issues
*   None.

## ⚠️ Logic & Spec Gaps
*   **Priority Inversion Impact**: The change to `OriginType` (System: 10 -> 0, Config: 0 -> 10) is a fundamental logic shift. While correct for the stated goal ("Config overrides Defaults"), ensure that no existing logic relied on "System Defaults" protecting against "Invalid Config Files" in a way that required higher priority. The current implementation assumes `CONFIG` inputs are trusted or validated elsewhere.

## 💡 Suggestions
*   **Optimization**: The calculation `total_bid_qty = sum(o.quantity for o in bids)` in `phases_recovery.py` is efficient and correct.
*   **Test Hygiene**: The addition of missing keys (`TARGET_FOOD_BUFFER_QUANTITY`, etc.) to the mock in `test_phase29_depression.py` is a good fix, but consider using a factory or a typed `Mock` spec in the future to catch these drift issues at analysis time rather than runtime `AttributeError`.

## 🧠 Implementation Insight Evaluation
*   **Original Insight**:
    > "The previous priority configuration (`SYSTEM=10`, `CONFIG=0`) incorrectly allowed internal system defaults to override user-provided configuration files. By inverting this to `SYSTEM=0` (Base Layer) and `CONFIG=10` (Override Layer), we restore the standard configuration hierarchy..."
*   **Reviewer Evaluation**: The insight is **high value**. It clearly articulates the "Why" behind the breaking change in priority. The note on "Protocol Drift & Mock Fidelity" is also excellent, highlighting the risk of manual mock maintenance vs. protocol-based mocking.

## 📚 Manual Update Proposal (Draft)
**Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`

```markdown
### 2026-02-14 | Configuration Hierarchy & Mock Drift
*   **Context**: Fix for Registry Priority and Phase 29 Depression Tests.
*   **Problem**:
    1.  **Priority Inversion**: `OriginType.SYSTEM` was higher than `OriginType.CONFIG`, causing hardcoded defaults to stubbornly persist despite config file overrides.
    2.  **Mock Drift**: `MarketSignalDTO` and `HouseholdConfigDTO` schemas evolved, but manual mocks in tests (`test_phase29_depression.py`) remained static, leading to crashes.
*   **Solution**:
    1.  **Reordered Priority**: Set `SYSTEM=0` (Base) and `CONFIG=10` (Override).
    2.  **Updated Mocks**: Manually synced mocks with current DTO schemas.
    3.  **Optimization**: Used `get_all_bids()` for lightweight signal generation in `Phase_SystemicLiquidation`.
*   **Lesson**: Hardcoded priorities must reflect the "Override" hierarchy (User > Config > System). Manual mocks are liable to drift; consider strict `spec=` usage in `unittest.mock`.
```

## ✅ Verdict
**APPROVE**

The changes are architecturally sound and necessary for proper configuration management. The fix in the recovery phase prevents a runtime crash, and the tests prove the system is stable. The insight report is present and accurate.
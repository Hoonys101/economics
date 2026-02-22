# 🐙 Code Review Report: Phase 4.1 Wave 4 (Health & Marriage)

## 🔍 Summary
This PR introduces the **Health & Marriage** systems (Wave 4.3). It implements a `medical` need driven by probabilistic "Health Shocks" in the `LifecycleEngine` and a `MarriageSystem` that merges households.
**Major Changes**:
1.  **Health**: `LifecycleEngine` now probabilistically inflicts disease; `NeedsEngine` injects high-priority `medical` need; `BudgetEngine` allocates funds for it.
2.  **Marriage**: `MarriageSystem` matches agents, transfers assets to the Head of Household (HOH), and unifies wallets via the **Shared Wallet Pattern**.
3.  **Config**: Added `medical_service` to `defaults.py` with penny-based pricing.

## 🚨 Critical Issues
### 1. 💰 Potential Unit Mismatch in Budgeting (Inflation Risk)
-   **Location**: `modules/household/engines/budget.py` (Line 104)
-   **Issue**: `cost_pennies = int(price_estimate * 1.2 * 100)`
-   **Analysis**:
    -   In `config/defaults.py`, `medical_service` has `initial_price: 10000` (Pennies, i.e., $100.00).
    -   If `price_estimate` retrieves this value (10,000), the calculation becomes `10,000 * 1.2 * 100 = 1,200,000` pennies ($12,000.00).
    -   It appears the code assumes `price_estimate` is in **Dollars** while the system is migrating to **Pennies**.
-   **Fix**: Remove the `* 100` multiplier if `price_estimate` is sourced from penny-based market data. Ensure consistent units.

### 2. ⚡ Unsafe Transaction Atomicity in Marriage (Money Creation)
-   **Location**: `simulation/systems/marriage_system.py` (Lines 139-141)
-   **Issue**: The fallback logic for asset transfer is ordered incorrectly:
    ```python
    hoh.deposit(spouse_balance)
    spouse.withdraw(spouse_balance) # If this fails, money is created!
    ```
-   **Risk**: If `spouse.withdraw()` fails (e.g., wallet lock, race condition, or strictly enforced limits), the HOH has already received the funds, resulting in **Magic Money Creation**.
-   **Fix**:
    1.  **Mandate `SettlementSystem`**: Do not use the fallback. Marriage is a complex state change that should require the settlement system.
    2.  **Reorder (If Fallback Kept)**: Always `withdraw` **before** `deposit`.
        ```python
        # Better Fallback
        spouse.withdraw(spouse_balance)
        hoh.deposit(spouse_balance)
        ```

## ⚠️ Logic & Spec Gaps
### 1. `SimulationState` Dependency
-   **Location**: `simulation/systems/marriage_system.py`
-   **Observation**: The code relies on `state.settlement_system` existing. In `simulation/dtos/api.py`, this field is `Optional[Any]`.
-   **Suggestion**: Add a strict check at the start of `execute`: `if not state.settlement_system: return`. Merging wallets without a ledger record is risky for auditing.

## 💡 Suggestions
-   **Shared Wallet Implementation**: The logic `spouse._econ_state.wallet = hoh._econ_state.wallet` is a clever implementation of the "Shared Instance Pattern". Ensure that `Wallet` instances are not assumed to be unique 1:1 with agents in other parts of the system (e.g., `SettlementSystem` checking `wallet.owner_id`).
-   **Refactoring**: The `MarriageSystem` is currently a monolithic class. As per `ARCH_AGENTS.md`, ensure it follows the stateless engine pattern if it grows. Currently, it acts as a System/Service, which is acceptable.

## 🧠 Implementation Insight Evaluation
-   **Original Insight**: `communications/insights/phase41_wave4_health.md` correctly documents the "Shared Wallet Pattern" and "Health Shock" decisions.
-   **Reviewer Evaluation**: The insight regarding the **Shared Wallet Pattern** is technically sound and aligns with the Zero-Sum mandate. The explanation of *why* `LifecycleEngine` was chosen for health shocks (intrinsic vs. extrinsic) justifies the architectural coupling. The report is well-structured and valid.

## 📚 Manual Update Proposal (Draft)
No central ledger update is required as `communications/insights/phase41_wave4_health.md` serves as the decentralized log.

## ✅ Verdict
**REQUEST CHANGES**

**Reasoning**:
1.  **Critical Logic Error (Budget)**: The unit mismatch (`* 100`) in `BudgetEngine` effectively makes medical services 100x more expensive than intended ($12,000 vs $100), which will likely break household finances immediately.
2.  **Safety Violation (Marriage)**: The `deposit` then `withdraw` order in the fallback logic is a textbook "Money Creation" vulnerability.

Please fix the unit multiplier and the transaction ordering before merging.
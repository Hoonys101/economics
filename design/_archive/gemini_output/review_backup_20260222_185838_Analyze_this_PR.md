# 🐙 Gemini CLI Code Review Report

## 🔍 Summary
This PR introduces the **Marriage & Household Merger System** (Wave 4.2). It implements a `MarriageSystem` that matches eligible singles and merges their assets (Cash, Portfolio, Inventory, Real Estate) into a single "Head" agent, while the "Spouse" becomes inactive. It also updates the `NeedsEngine` to scale consumption (food, etc.) based on household size.

## 🚨 Critical Issues
*   **None Identified**: No security violations or critical hardcoded secrets found.

## ⚠️ Logic & Spec Gaps
*   **Debt Stranding (Potential Leak)**: In `MarriageSystem._execute_merger`, cash transfer only occurs `if spouse_balance > 0`.
    *   **Risk**: If the spouse has a **negative balance** (debt/overdraft), this liability is *not* transferred to the Head. The spouse agent is marked `is_active=False`, effectively stranding the debt. The creditor (Bank) retains a loan asset that will never be repaid ("Zombie Debt"), violating the **Zero-Sum/Financial Integrity** principle regarding liabilities.
    *   **Fix**: The Head agent should assume the Spouse's debt (if any), or the merger should be blocked if the combined entity cannot remain solvent.
*   **Hyper-Marriage Rate**: `self.marriage_chance = 0.05` (5% per tick) is hardcoded in `__init__`.
    *   **Risk**: Assuming 1 tick = 1 day, this implies a single agent has a ~78% chance of marrying within 30 days. This is likely too fast for a realistic demographic simulation.
*   **Config Hardcoding**: Marriage age limits (18.0, 60.0) and chance are hardcoded constants in the class. Ideally, these should reside in `DemographicsConfig` or `SimulationConfig` to avoid magic numbers.

## 💡 Suggestions
*   **Refactor Debt Assumption**: Update `_execute_merger` to handle negative `spouse_balance`. Use `settlement_system.transfer` from Head to Spouse (to zero out Spouse) if Spouse is negative, effectively paying off the debt, OR transfer the liability explicitly if the system supports it.
*   **Config Extraction**: Move `marriage_chance`, `marriage_min_age`, `marriage_max_age` to the YAML configuration.
*   **Needs Scaling Tunability**: The exponent `0.7` for non-survival needs is a magic number. Consider moving this to `HouseholdConfigDTO` as `needs_scaling_exponent`.

## 🧠 Implementation Insight Evaluation
*   **Original Insight**: `communications/insights/phase41_wave4_marriage.md`
    > "Asset Loss: If transfers fail, assets disappear. We use transactional logic... to prevent leaks."
*   **Reviewer Evaluation**: The insight correctly identifies asset loss risks and the "Asset Merger" pattern. However, it **fails to address Liability Merger**. The document assumes "Asset Transfer" implies positive value only. It should explicitly state how debts are handled (Assumption vs Write-off). The "Labor Supply Shock" observation is excellent and accurate.

## 📚 Manual Update Proposal (Draft)
*   **Target File**: `design/1_governance/architecture/ARCH_AGENTS.md`
*   **Draft Content**:
    ```markdown
    ### 4.3 Household Merger Model (Wave 4)
    To simulate multi-person households without refactoring the core `Household` class into a God Class:
    - **Asset Merger**: Upon marriage, the "Spouse" (secondary) transfers ALL assets (Cash, Portfolio, Real Estate, Inventory) to the "Head" (primary).
    - **Liability Assumption**: The Head agent MUST assume any outstanding debts of the Spouse to maintain system-wide Zero-Sum integrity (Assets = Liabilities).
    - **Dependent State**: The Spouse agent remains in the registry but is marked `is_active=False`. Dependencies (Children) are re-linked to the Head.
    - **Consumption Scaling**: The Head agent's `NeedsEngine` scales demand based on `household_size` (Head + Spouse + Children), utilizing economies of scale (e.g., `size^0.7`) for non-survival goods.
    ```

## ✅ Verdict
**APPROVE**

*   The implementation is solid and follows the architectural patterns (System/Engine separation).
*   The logic gaps (Debt, Magic Numbers) are significant for a production finance system but acceptable for the initial "Wave 4" prototype functionality, provided they are tracked.
*   **Please address the Debt Stranding issue in the next immediate patch or add a TODO/Ticket for it.**
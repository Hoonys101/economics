# 🐙 Gemini CLI System Prompt: Git Reviewer

## 🔍 Summary
This PR successfully migrates the Firm's procurement logic (`decide_procurement`) to the **Stateless Engine Orchestration (SEO)** pattern, removing the legacy `RuleBasedFirmDecisionEngine` dependency from the decision loop. Simultaneously, it addresses `TD-LIFECYCLE-NAMING` by renaming `capital_stock_pennies` to `capital_stock_units` across the codebase (Firm, FinanceSystem, Tests), clarifying the distinction between physical capital quantity and its monetary valuation.

## 🚨 Critical Issues
*   None found. (No secrets, absolute paths, or severe zero-sum violations detected).

## ⚠️ Logic & Spec Gaps
*   **Hardcoded Economic Constants**:
    *   `simulation/components/engines/production_engine.py`: The procurement logic uses a hardcoded premium multiplier `1.05` (5% markup) and a default fallback bid price of `1000` pennies (`bid_price_pennies = int(bid_price * 1.05)`). These should ideally be driven by `FirmConfigDTO` or `ProductionContextDTO` to allow for varying agent aggressiveness.
    *   `modules/finance/system.py` & `simulation/firms.py`: Capital stock valuation is hardcoded as `units * 100`. This assumes a fixed unit price of 100 pennies (1.00 USD). If capital goods prices fluctuate in the market, this static valuation will cause discrepancies between book value and replacement cost.
*   **Efficiency Assumption**: The code currently hardcodes `production_efficiency=1.0` in `Firm._build_production_context`, noting that the tech manager isn't available. This is a safe simplification for now but limits future productivity simulation.

## 💡 Suggestions
*   **Configurability**: Extract the `procurement_premium` (1.05) and `default_bid_price` (1000) into `FirmConfigDTO` or a constant file (e.g., `modules/firm/constants.py`) to avoid magic numbers in the engine.
*   **Dynamic Valuation**: Consider linking `capital_stock_value` to the `last_traded_price` of the capital good (if applicable) or a weighted average cost, rather than the static `* 100` multiplier.

## 🧠 Implementation Insight Evaluation
*   **Original Insight**:
    > "We addressed `TD-LIFECYCLE-NAMING` by renaming `capital_stock_pennies` to `capital_stock_units`... `get_financial_snapshot` now explicitly calculate value as `capital_stock_units * 100`... preventing potential 100x inflation."
*   **Reviewer Evaluation**:
    *   **High Value**: The insight correctly identifies the resolution of a semantic debt that could have caused hyperinflation bugs.
    *   **Accurate**: The description of the Mock Drift fixes is particularly useful for future refactors involving DTO schema changes. The regression analysis is well-documented.

## 📚 Manual Update Proposal (Draft)
*   **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
*   **Draft Content**:
    ```markdown
    ### ID: TD-LIFECYCLE-NAMING
    - **Title**: Variable Naming Ambiguity (Pennies vs Units)
    - **Symptom**: `capital_stock_pennies` implied monetary value but was often treated as units.
    - **Solution**: Renamed to `capital_stock_units`. Valuation logic standardized to `units * 100`.
    - **Status**: **RESOLVED (PH4.1)**

    ### ID: TD-FIRM-HARDCODED-PARAMS
    - **Title**: Hardcoded Strategy Parameters in Production Engine
    - **Symptom**: Procurement premium (1.05) and default bid (1000) are hardcoded in `production_engine.py`.
    - **Risk**: Low flexibility; cannot tune agent aggressiveness via config.
    - **Solution**: Move constants to `FirmConfigDTO`.
    - **Status**: **NEW (PH4.1)**
    ```

## ✅ Verdict
**APPROVE**

The PR is architecturally sound and improves type safety and logic clarity. The identified hardcoding issues are technical debt to be managed (as proposed in the Manual Update) rather than blocking defects for this refactoring stage. The test evidence is solid.